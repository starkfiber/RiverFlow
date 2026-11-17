"""Independently rebuild four explicitly reviewed model sources; no inference.

Manifest input is local authority supplied by the orchestrator after source review,
not an instruction accepted from provider output. Never rewrites an existing run.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / "experiments/refinement-20261117/ai"
ORACLE_SHA = "f481949423fcfaa62da6e7084b7b39320ac898b9bb501ef0db23ea9524f1ab8e"
BOUNDARY_SHA = "2001688d930c1638b770a72a64d8a2deb37ae99d7041bb79c09a9f81520b99e8"
ORDER = [("C", "manual"), ("D", "cli"), ("C", "cli"), ("D", "manual")]
COMPILER_SHA = "4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(manifest):
    if manifest.get("schema") != "rf2.ai-completion.reviewed-sources.v1":
        raise ValueError("Wrong reviewed-source manifest schema")
    if manifest.get("sourceReviewConfirmed") is not True:
        raise ValueError("Separate orchestrator source/effect review is required")
    compiler = Path(manifest["compiler"]).resolve(strict=True)
    if sha(compiler) != COMPILER_SHA:
        raise ValueError("Unqualified compiler identity")
    sdk = Path(manifest["sdk"]).resolve(strict=True)
    pins = manifest["sdkFiles"]
    actual = {p.name: sha(p) for p in sdk.iterdir() if p.is_file()}
    if actual != pins:
        raise ValueError("SDK bytes differ from reviewed manifest")
    arms = manifest["arms"]
    if [(x["task"], x["condition"]) for x in arms] != ORDER:
        raise ValueError("Exactly the four declared ordered arms are required")
    if sha(OLD / "grade.py") != ORACLE_SHA or sha(OLD / "study.py") != BOUNDARY_SHA:
        raise ValueError("Historical oracle or condition checker changed")
    spec = importlib.util.spec_from_file_location("rf2_previous_condition_checker", OLD / "study.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    for arm in arms:
        source = Path(arm["source"])
        if source.is_symlink() or not source.is_file() or sha(source) != arm["sourceSHA256"]:
            raise ValueError("Reviewed source identity mismatch")
        errors = checker.condition_errors(source.read_text(), arm["condition"])
        if errors:
            raise ValueError("Condition boundary failed: " + "; ".join(errors))
    return compiler, sdk, arms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not os.environ.get("TMPDIR", "").startswith("/Volumes/Mac Work Cache/"):
        raise ValueError("Use the guarded disposable bank for native generated output")
    manifest = json.loads(args.manifest.read_text())
    compiler, sdk, arms = validate(manifest)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    cache = Path(tempfile.mkdtemp(prefix="rf2-ai-final-", dir=os.environ["TMPDIR"]))
    result = {
        "schema": "rf2.ai-completion.independent-acceptance.v1",
        "manifestSHA256": sha(args.manifest), "compilerSHA256": COMPILER_SHA,
        "oracleSHA256": ORACLE_SHA, "runs": [], "allPassed": False,
        "providerCalls": 0, "stableChanged": False,
        "scope": "Four source-reviewed model proposals, plain and optimized native Mac ARM64 builds; unchanged independent synthetic oracle. No universal quality or token-saving claim.",
    }

    def save():
        (out / "RESULTS.json").write_text(json.dumps(result, indent=2) + "\n")

    save()
    for arm in arms:
        for mode in ["plain", "opt"]:
            label = arm["task"] + "-" + arm["condition"] + "-" + mode
            dest = out / label
            dest.mkdir()
            binary = cache / label
            row = {"label": label, "sourceSHA256": arm["sourceSHA256"], "allPassed": False}
            result["runs"].append(row)
            save()
            start = time.monotonic()
            try:
                command = [str(compiler), str(Path(arm["source"]).resolve()), str(binary), "--compact", *(["--opt"] if mode == "opt" else []), "--sdk-root", str(sdk), "--diagnostic-json"]
                run = subprocess.run(command, capture_output=True, timeout=30)
                (dest / "compile.stdout").write_bytes(run.stdout)
                (dest / "compile.stderr").write_bytes(run.stderr)
                row.update(compileExit=run.returncode)
                if run.returncode == 0:
                    subprocess.run(["codesign", "-s", "-", str(binary)], capture_output=True, timeout=10, check=True)
                    row["binarySHA256"] = sha(binary)
                    (dest / "program").symlink_to(binary)
                    run = subprocess.run([sys.executable, "-B", str(OLD / "grade.py"), arm["task"], "--binary", str(binary), "--out", str(dest / "grade")], capture_output=True, timeout=180)
                    (dest / "grade.stdout").write_bytes(run.stdout)
                    (dest / "grade.stderr").write_bytes(run.stderr)
                    row["gradeExit"] = run.returncode
                    if (dest / "grade/RESULTS.json").is_file():
                        grade = json.loads((dest / "grade/RESULTS.json").read_text())
                        row.update(passed=grade["passed"], total=grade["total"], allPassed=bool(run.returncode == 0 and grade["allPassed"] and grade["total"] == (86 if arm["task"] == "C" else 116)))
                        row["gradeReceiptSHA256"] = sha(dest / "grade/RESULTS.json")
            except (subprocess.SubprocessError, OSError) as error:
                row["controllerError"] = type(error).__name__
            row["elapsedSeconds"] = time.monotonic() - start
            save()
            print(json.dumps(row), flush=True)
    result["allPassed"] = len(result["runs"]) == 8 and all(x["allPassed"] for x in result["runs"])
    result["checksPassed"] = sum(x.get("passed", 0) for x in result["runs"])
    result["checksDeclared"] = 808
    save()
    return 0 if result["allPassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
