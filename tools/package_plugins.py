#!/usr/bin/env python3
"""Build the WordPress, DirectAdmin, and WHM plugin archives.

Each archive gets data/package.json with the revision it was built from. Installed
copies that came from a GitHub package compare that revision with the plugins
release and download a newer archive when one is published.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "Clownstein/How-To-Help-Protect-Against-AI-Assisted-Attacks"
RELEASE_TAG = "plugins"
EXECUTABLE = {
    "scripts/install.sh",
    "scripts/uninstall.sh",
    "scripts/update.sh",
    "scripts/apply.sh",
    "admin/index.html",
    "user/index.html",
    "reseller/index.html",
    "install.sh",
    "uninstall.sh",
    "update.sh",
    "index.cgi",
}


def revision(explicit: str | None) -> str:
    if explicit:
        return explicit
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError):
        return "dev"
    return completed.stdout.strip() or "dev"


def write_tar_gz(destination: Path, files: list[tuple[str, Path]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(destination, "w:gz") as archive:
        for name, path in files:
            normalized = name.replace("\\", "/")
            relative = normalized.split("/", 1)[-1] if normalized.startswith("protect-from-ai/") else normalized
            data = path.read_bytes()
            info = tarfile.TarInfo(normalized)
            info.size = len(data)
            info.mode = 0o755 if relative in EXECUTABLE else 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))


def write_zip(destination: Path, files: list[tuple[str, Path]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in files:
            normalized = name.replace("\\", "/")
            relative = normalized.split("/", 1)[-1] if normalized.startswith("protect-from-ai/") else normalized
            info = zipfile.ZipInfo(normalized)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = 0o100755 if relative in EXECUTABLE else 0o100644
            info.external_attr = mode << 16
            archive.writestr(info, path.read_bytes())


def package_files(source: Path, prefix: str, package: dict[str, str], extra: dict[str, Path], scratch: Path, label: str) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        relative = path.relative_to(source).as_posix()
        if relative == "data/package.json":
            continue
        name = relative if prefix == "" else f"{prefix}/{relative}"
        files.append((name, path))
    for relative, path in extra.items():
        name = relative if prefix == "" else f"{prefix}/{relative}"
        files.append((name, path))
    package_path = scratch / f"{label}-package.json"
    package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    name = "data/package.json" if prefix == "" else f"{prefix}/data/package.json"
    files.append((name, package_path))
    return files


def build(dist: Path, version: str) -> dict[str, str]:
    package = {"version": version, "channel": "github"}
    base = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}"
    assets = {
        "wordpress": "protect-from-ai-wordpress.zip",
        # DirectAdmin installs an upload into plugins/<archive name>, and the menu links use protect_from_ai.
        "directadmin": "protect_from_ai.tar.gz",
        "cpanel": "protect-from-ai-cpanel.tar.gz",
    }
    scratch = dist / ".staging"
    scratch.mkdir(parents=True, exist_ok=True)

    wordpress = package_files(
        ROOT / "plugins" / "wordpress" / "protect-from-ai",
        "protect-from-ai",
        package,
        {},
        scratch,
        "wordpress",
    )
    write_zip(dist / assets["wordpress"], wordpress)

    directadmin = package_files(
        ROOT / "plugins" / "directadmin" / "protect_from_ai",
        "",
        package,
        {},
        scratch,
        "directadmin",
    )
    write_tar_gz(dist / assets["directadmin"], directadmin)

    cpanel = package_files(
        ROOT / "plugins" / "cpanel" / "protect_from_ai",
        "",
        package,
        {},
        scratch,
        "cpanel",
    )
    write_tar_gz(dist / assets["cpanel"], cpanel)

    release = {
        "version": version,
        "wordpress": f"{base}/{assets['wordpress']}",
        "directadmin": f"{base}/{assets['directadmin']}",
        "cpanel": f"{base}/{assets['cpanel']}",
    }
    text = json.dumps(release, indent=2) + "\n"
    (dist / "release.json").write_text(text, encoding="utf-8")
    return release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--version", default=None, help="package revision (default: current git commit)")
    args = parser.parse_args()
    release = build(args.dist.resolve(), revision(args.version))
    print(json.dumps(release, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
