"""Verify unchanged upstream files and prepare an isolated Academy build context."""

import hashlib
import json
import secrets
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACADEMY = ROOT / "docker" / "academy"
RUNTIME = ACADEMY / ".runtime"
CONTEXT = RUNTIME / "context"


def verify_originals():
    manifest = json.loads((ACADEMY / "upstream.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        data = (ACADEMY / "original" / entry["path"]).read_bytes()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        if hashlib.sha1(blob).hexdigest() != entry["git_blob_sha1"]:
            raise RuntimeError(f"Upstream file changed: {entry['path']}")
    print(f"Verified {len(manifest['files'])} upstream files at {manifest['commit']}")


def prepare_directory():
    if RUNTIME.is_symlink() or RUNTIME.resolve().parent != ACADEMY.resolve():
        raise RuntimeError("Runtime directory must stay inside docker/academy")
    RUNTIME.mkdir(exist_ok=True)
    if CONTEXT.is_symlink() or CONTEXT.resolve().parent != RUNTIME.resolve():
        raise RuntimeError("Generated context must stay inside the runtime directory")
    if CONTEXT.exists():
        shutil.rmtree(CONTEXT)
    CONTEXT.mkdir()


def copy_sources():
    for name in ("auth_app", "video_app", "core"):
        shutil.copytree(ROOT / name, CONTEXT / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("manage.py", "requirements.txt"):
        shutil.copy2(ROOT / name, CONTEXT / name)
    for name in ("backend.Dockerfile", "backend.entrypoint.sh", ".dockerignore"):
        shutil.copy2(ACADEMY / "original" / name, CONTEXT / name)
    (CONTEXT / "academy").mkdir()
    for name in ("entrypoint.sh", "bootstrap_admin.py"):
        shutil.copy2(ACADEMY / name, CONTEXT / "academy" / name)


def prepare_environment():
    target = RUNTIME / ".env"
    if target.exists():
        print("Existing Academy runtime .env retained (no credentials printed).")
        return
    template = (ACADEMY / ".env.example").read_text(encoding="utf-8")
    lines = [line.replace("GENERATE_LOCALLY", secrets.token_urlsafe(48))
             for line in template.splitlines()]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Created ignored Academy runtime .env with random local credentials.")


def main():
    verify_originals()
    prepare_directory()
    copy_sources()
    prepare_environment()
    print("Isolated build context ready; root .env and existing volumes untouched.")


if __name__ == "__main__":
    main()
