"""Reproduce the 0.49 compiler and run both application suites through Workbench."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "39f4944fa001397cf4977322d89f322316ee21f5105cbe3d75bdddd886820009"
FULL = "faa36d7da6657f6b819d12383a54342951d0b1196268fdab9b445bb51c846432"
COMPACT = "4953dd4d507329f6ae8e4c3b19cc1e9c9913a103e25b95e836a321a2fb731a8e"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args, env):
    result = subprocess.run(args, env=env, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError((args, result.returncode, result.stdout[-1200:], result.stderr[-2400:]))
    return result.stdout


def signed_image(compiler, source, output, options, env):
    run(compiler, source, output, *options, env=env)
    run("/usr/bin/codesign", "-s", "-", output, env=env)
    run("/usr/bin/codesign", "--verify", "--strict", output, env=env)
    return sha(output)


def rebuild(source, bootstrap, work, env):
    if sha(source) != SOURCE:
        raise ValueError("expected the archived, hash-pinned 0.49 compiler source")
    images = work / "build-0.49"
    images.mkdir()
    for label, compiler, options, pin in (
        ("full", bootstrap, ["--opt"], FULL),
        ("full-self", images / "full" / "program", ["--opt"], FULL),
        ("compact", images / "full-self" / "program", ["--compact", "--opt"], COMPACT),
        ("compact-self", images / "compact" / "program", ["--compact", "--opt"], COMPACT),
    ):
        folder = images / label
        folder.mkdir()
        fingerprint = signed_image(compiler, source, folder / "program", options, env)
        if fingerprint != pin:
            raise ValueError(f"0.49 {label} digest drift: {fingerprint}")
    full, compact = (images / mode / "program" for mode in ("full-self", "compact-self"))
    return compact, full, {
        "source_sha256": SOURCE, "legacy": {"sha256": FULL, "bytes": full.stat().st_size},
        "compact": {"sha256": COMPACT, "bytes": compact.stat().st_size},
        "legacy_self_reproduced": True, "compact_self_reproduced": True,
    }


def exercise(compiler, work, env, evidence):
    results = {}
    node = os.environ.get("DOCUMENT_AUDIT_NODE") or shutil.which("node")
    for app, suite in (("sensor-audit", "verify.py"), ("document-audit", "test.py")):
        source = ROOT / "examples" / app / "main.flow"
        run(compiler, "--check", source, env=env)
        for mode, options in (("plain", ["--compact"]), ("optimized", ["--compact", "--opt"])):
            label = f"{app}-{mode}"
            program = work / label
            image = signed_image(compiler, source, program, options, env)
            test_env = {**env, "RF2_TEST_ARTIFACTS": str(work)}
            args = [str(program), "--label", mode] if app == "sensor-audit" else []
            if app == "document-audit":
                test_env["DOCUMENT_AUDIT_BIN"] = str(program)
                if node:
                    test_env["DOCUMENT_AUDIT_NODE"] = node
            raw = run(sys.executable, "-B", source.parent / suite, *args, env=test_env)
            summary = json.loads(raw.splitlines()[-1])
            assert summary["allPassed"] and summary["checks"] > 0
            receipt = Path(summary["directory"]) / "RESULTS.json"
            assert json.loads(receipt.read_text())["binarySHA256"] == image
            target = evidence / (label + ".json")
            shutil.copyfile(receipt, target)
            results[label] = {"checks": summary["checks"], "signed_sha256": image,
                              "receipt": target.name, "receipt_sha256": sha(target)}
    return results
