"""Qualify the installed managed command from the public Workbench archive."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from candidate049 import ROOT, exercise, rebuild, sha
from publisher import Publisher
from regressions import command, mcp, text_audit, text_search

spec = importlib.util.spec_from_file_location("package_workbench", ROOT / "tools/package-managed-workbench.py")
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


def main(source_049, evidence):
    evidence.mkdir(exist_ok=True, parents=True)
    scratch = Path(os.environ["TMPDIR"]).resolve()
    if scratch == evidence or scratch in evidence.parents:
        raise ValueError("use a persistent owner-controlled test evidence directory outside the build cache")
    work = Path(tempfile.mkdtemp(prefix="managed-rf2-", dir=scratch))
    root, trust, home = (work / name for name in ("installed", "retained-trust", "home"))
    trust.mkdir(mode=0o700)
    home.mkdir()
    env = {"HOME": str(home), "PATH": "/nonexistent", "TMPDIR": str(work)}
    manifest = packager.package(root, trust)
    original_bundle = work / "bundle-backup"
    shutil.copytree(root, original_bundle)
    base = packager.extract_workbench(work / "publisher-bootstrap")
    a = base / "rf2c"
    b, original_b, compiler_build = rebuild(source_049, a, work, env)
    ra, rb, rr, unknown, public, other_public, fork, wrong_target = (
        work / name for name in ("A", "B", "rollback", "unknown", "public", "other-key", "fork", "wrong-target")
    )
    receipt = json.dumps({"base_archive_sha256": manifest["base_archive_sha256"],
                          "compiler_049": compiler_build}, sort_keys=True).encode()
    provenance = (source_049.read_bytes(), a.read_bytes(), receipt)
    with tempfile.TemporaryDirectory(prefix="test-publishers-", dir=evidence) as private:
        publisher, foreign = (Publisher(Path(private), label) for label in ("publisher", "foreign"))
        initial = publisher.envelope(None, a.read_bytes(), provenance)
        update = publisher.envelope(initial, b.read_bytes(), provenance)
        rollback_record = publisher.envelope(update, a.read_bytes(), provenance, target=initial)
        for path, value in ((ra, initial), (rb, update), (rr, rollback_record),
                            (unknown, foreign.envelope(None, b.read_bytes(), provenance)),
                            (fork, publisher.envelope(None, b.read_bytes(), provenance)),
                            (wrong_target, publisher.envelope(initial, b.read_bytes(), provenance, target=update)),
                            (public, publisher.public), (other_public, foreign.public)):
            path.write_bytes(value)
    assert not any(path.name in {"publisher.pub", "publisher.pem", "foreign.pem"} for path in root.rglob("*"))

    def cli(*args, status=0):
        return command(root / "rf2", *args, cwd=work, env=env, allowed=(status,))

    authority = trust / "authority"
    history = authority / "generations"
    head = authority / "active"
    compiler = root / "rf2c"
    cli("status")
    rpc = mcp(root / "rf2", env, work)
    journal = work / "journal.rf2book"
    booking = root / "booking"
    command(booking, "init", journal, cwd=work, env=env)
    command(booking, "reserve", journal, "2027-01-10", "09:00", "10:00",
            "Managed Workbench Probe", cwd=work, env=env)
    journal_bytes = journal.read_bytes()
    listing = command(booking, "list", journal, cwd=work, env=env).stdout
    assert b"Managed Workbench Probe" in listing

    def check_journal():
        assert journal.read_bytes() == journal_bytes
        assert command(booking, "list", journal, cwd=work, env=env).stdout == listing

    def check_head(record, artifact):
        assert cli("update", "status").stdout.decode().strip() == sha(record)
        assert head.read_text() == sha(record)
        assert (history / sha(record) / "rf2c").read_bytes() == artifact.read_bytes()
        assert (history / sha(record) / "record").read_bytes() == record.read_bytes()
        check_journal()

    refusals = {}
    def refuse(label, *args):
        process = cli("update", *args, status=2)
        assert not process.stdout
        refusals[label] = process.stderr.decode().strip()

    refuse("unconfigured", "status")
    refuse("missing_enrollment_key", "enroll", work / "missing", sha(public), ra, a)
    refuse("incorrect_enrollment_key", "enroll", other_public, sha(public), ra, a)
    refuse("wrong_publisher_signature", "enroll", public, sha(public), unknown, b)
    assert not authority.exists()
    cli("update", "enroll", public, sha(public), ra, a)
    check_head(ra, a)
    refuse("cannot_reenroll", "enroll", public, sha(public), ra, a)
    results = {"initial": text_search(compiler, work, env, "initial")}
    active_a = history / sha(ra)
    preserved_a = {p.name: sha(p) for p in active_a.iterdir()}
    # Launch also fails closed, before any untrusted compiler bytes run.
    image_a = active_a / "rf2c"
    original_image = image_a.read_bytes()
    image_a.write_bytes(original_image[:-1] + bytes([original_image[-1] ^ 1]))
    launch_refusal = command(compiler, "--check", ROOT / "examples/text-search/main.rf2",
                             cwd=work, env=env, allowed=(2,))
    assert not launch_refusal.stdout and b"compiler differs" in launch_refusal.stderr
    image_a.write_bytes(original_image)
    check_head(ra, a)

    changed = work / "tampered-artifact"
    payload = bytearray(b.read_bytes())
    payload[len(payload) // 2] ^= 1
    changed.write_bytes(payload)
    refuse("missing_candidate", "prepare", rb, work / "missing")
    refuse("tampered_candidate", "prepare", rb, changed)
    refuse("legacy_image_exceeds_transport_limit", "prepare", rb, original_b)
    assert "format size limit" in refusals["legacy_image_exceeds_transport_limit"]
    refuse("untrusted_update", "prepare", unknown, b)
    refuse("trusted_wrong_predecessor", "prepare", fork, b)
    refuse("trusted_wrong_rollback_target", "prepare", wrong_target, b)
    key = authority / "publisher.pub"
    key.unlink()
    refuse("missing_authority_key", "prepare", rb, b)
    key.write_bytes(other_public.read_bytes())
    refuse("substituted_authority_key", "prepare", rb, b)
    key.write_bytes(public.read_bytes())
    check_head(ra, a)

    prepared = cli("update", "prepare", rb, b).stdout.decode().strip()
    assert prepared == sha(rb)
    # Subsequent invocations are fresh processes. A remains current across the handoff.
    check_head(ra, a)
    pending_artifact = authority / "pending" / prepared / "artifact"
    pending_artifact.write_bytes(changed.read_bytes())
    refuse("tampered_prepared_candidate", "activate", prepared)
    check_head(ra, a)
    assert cli("update", "prepare", rb, b).stdout.decode().strip() == prepared

    # One activation wins the writer lock; another invocation must refuse the replay.
    with subprocess.Popen([root / "rf2", "update", "activate", prepared], cwd=work, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as competing:
        try:
            output = subprocess.run([root / "rf2", "update", "activate", prepared], cwd=work,
                                    env=env, capture_output=True, timeout=30)
            competing_out, competing_err = competing.communicate(timeout=30)
        finally:
            if competing.poll() is None:
                competing.kill()
                competing.wait()
    assert sorted([output.returncode, competing.returncode]) == [0, 2]
    assert [output.stdout, competing_out].count(b"activated\n") == 1
    assert b"release already active" in output.stderr + competing_err
    check_head(rb, b)
    results["updated"] = text_search(compiler, work, env, "updated")
    audit = text_audit(compiler, work, env, "audit-updated")
    expanded_apps = exercise(compiler, work, env, evidence)
    updated_rpc = mcp(root / "rf2", env, work)
    assert updated_rpc == rpc
    check_journal()
    active_b = history / sha(rb)
    preserved_b = {p.name: sha(p) for p in active_b.iterdir()}

    # Restoring packaged application files alone cannot rewind separately provisioned authority.
    root.rename(work / "bundle-before-restore")
    original_bundle.rename(root)
    check_head(rb, b)
    rollback = cli("update", "prepare", rr, a).stdout.decode().strip()
    assert rollback == sha(rr)
    cli("update", "activate", rollback)
    check_head(rr, a)
    refuse("replay_superseded_update", "activate", prepared)
    refuse("replay_superseded_prepare", "prepare", rb, b)
    check_head(rr, a)
    results["rolled_back"] = text_search(compiler, work, env, "rolled-back")
    assert results["initial"] == results["rolled_back"]
    assert results["updated"]["result"] == results["initial"]["result"]
    rolled_audit = text_audit(compiler, work, env, "audit-rollback")
    assert rolled_audit["results"] == audit["results"]
    assert mcp(root / "rf2", env, work) == rpc
    assert {p.name: sha(p) for p in active_a.iterdir()} == preserved_a
    assert {p.name: sha(p) for p in active_b.iterdir()} == preserved_b
    compiler_gaps = {}
    for application in ("sensor-audit", "document-audit"):
        source = ROOT / "examples" / application / "main.flow"
        output = command(compiler, "--check", source, cwd=work, env=env, allowed=(0, 1))
        compiler_gaps[application] = {"exit": output.returncode, "diagnostic": output.stderr.decode().strip()}
        assert output.returncode == 1 and b"unknown local" in output.stderr
    latest = history / sha(rr) / "checkpoint"
    state = latest.with_name("state")
    original_state = state.read_bytes()
    state.write_bytes(original_state + b"x")
    refuse("trailing_release_state_bytes", "status")
    state.write_bytes(original_state)
    check_head(rr, a)
    assert int.from_bytes(latest.read_bytes()[40:48], "little") == 3

    record = {
        "native": "macOS arm64", "base_archive_sha256": manifest["base_archive_sha256"],
        "updater_source": {path.name: sha(path) for path in (ROOT / "native/updater").glob("*.swift")},
        "launcher_sha256": sha(root / "rf2"), "workspace": str(work),
        "publisher_key_sha256": sha(public), "independent_openssl_verified_records": 6,
        "heads": [{"record_sha256": sha(r), "compiler_sha256": sha(image)} for r, image in ((ra, a), (rb, b), (rr, a))],
        "journal_sha256": sha(journal), "refusals": refusals, "text_search": results, "text_audit": audit,
        "compiler_049_build": compiler_build, "expanded_apps": expanded_apps,
        "normal_mcp": rpc, "mcp_before_after_rollback_matched": True, "active_compiler_tamper_refused": True, "newer_application_checks": compiler_gaps,
        "bundle_restore_preserved_active": True, "fresh_process_prepare_activate": True,
        "concurrent_activation_returncodes": [0, 2], "disposable_bytes": sum(p.stat().st_size for p in work.rglob("*") if p.is_file()),
    }
    (evidence / "receipt.json").write_text(json.dumps(record, indent=2) + "\n")
    print(evidence / "receipt.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_049", type=Path)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    main(args.source_049.resolve(), args.evidence.resolve())
