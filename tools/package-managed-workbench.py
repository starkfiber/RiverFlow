"""Build a native managed Workbench from the pinned public Workbench archive."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "RF2-Workbench-0.38-dev-macos-arm64"
ZIP = ROOT / "dist/workbench-0.38" / (NAME + ".zip")
ZIP_SHA256 = "146874d9b68b2c4a4be373f967e7ea04b7490da4abc69e8df1717be3acb0c8c7"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args):
    subprocess.run(args, timeout=90, check=True)


def extract_workbench(destination):
    if sha(ZIP) != ZIP_SHA256:
        raise ValueError("unexpected Workbench archive digest")
    with zipfile.ZipFile(ZIP) as archive:
        seen = set()
        for item in archive.infolist():
            if not item.filename.startswith(NAME + "/"):
                continue
            path = PurePosixPath(item.filename)
            mode = stat.S_IFMT(item.external_attr >> 16)
            if (".." in path.parts or "\\" in item.filename or item.filename in seen or
                    mode not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError("unexpected Workbench archive member")
            seen.add(item.filename)
    destination.mkdir()
    run("/usr/bin/unzip", "-q", ZIP, NAME + "/*", "-d", destination)
    source = destination / NAME
    manifest = json.loads((source / "MANIFEST.json").read_text())["files"]
    actual = {path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file()}
    if actual != {*manifest, "MANIFEST.json"}:
        raise ValueError("unexpected Workbench file inventory")
    for relative, record in manifest.items():
        member = source / relative
        if member.stat().st_size != record["bytes"] or sha(member) != record["sha256"]:
            raise ValueError(f"invalid Workbench member: {relative}")
    for binary in ("rf2", "rf2c", "booking", "booking-web", "studio"):
        run("/usr/bin/codesign", "--verify", "--strict", source / binary)
    return source


def package(destination, trust):
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise ValueError("this package requires macOS ARM64")
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination must be new")
    if not trust.is_dir() or trust.stat().st_mode & 0o777 != 0o700:
        raise ValueError("trust store must be a pre-provisioned 0700 directory")
    if destination == trust or destination in trust.parents:
        raise ValueError("trust store must be outside the installation")
    with tempfile.TemporaryDirectory(dir=destination.parent) as work:
        stage = Path(work)
        source = extract_workbench(stage / "extract")
        libexec = source / "libexec"
        libexec.mkdir()
        (source / "rf2").rename(libexec / "rf2-core")
        (source / "rf2c").unlink()
        updater = ROOT / "native/updater"
        run("/usr/bin/swiftc", "-O", "-module-cache-path", stage / "modules",
            updater / "main.swift", updater / "ReleaseChain.swift", "-o", source / "rf2")
        run("/usr/bin/codesign", "-s", "-", source / "rf2")
        run("/usr/bin/codesign", "--verify", "--strict", source / "rf2")
        (source / "rf2c").hardlink_to(source / "rf2")
        (source / ".rf2-trust-location").write_text(str(trust))
        (source / "README-MANAGED.md").write_bytes((updater / "README.md").read_bytes())
        manifest = {
            "edition": "Workbench 0.38 managed-update candidate",
            "base_archive_sha256": ZIP_SHA256,
            "files": {
                str(path.relative_to(source)): {"bytes": path.stat().st_size, "sha256": sha(path)}
                for path in sorted(source.rglob("*"))
                if path.is_file() and path.name != "MANIFEST.json"
            },
        }
        (source / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
        source.rename(destination)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("trust", type=Path)
    args = parser.parse_args()
    package(args.destination.resolve(), args.trust.resolve())
