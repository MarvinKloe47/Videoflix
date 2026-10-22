"""Check submission naming/size rules without importing or modifying the application."""

import ast
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_NAMES = {"setUp", "tearDown"}


def python_sources():
    files = [ROOT / "manage.py"]
    for directory in ("auth_app", "video_app", "core", "scripts"):
        files.extend((ROOT / directory).rglob("*.py"))
    return [p for p in files if not {"migrations", "__pycache__"} & set(p.parts)]


def check_functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    functions = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for node in functions:
        location = f"{path.relative_to(ROOT)}:{node.lineno} {node.name}"
        if node.end_lineno - node.lineno + 1 > 14:
            raise ValueError(f"Function exceeds 14 physical lines: {location}")
        snake_case = re.fullmatch(r"[a-z_][a-z0-9_]*", node.name)
        if node.name not in HOOK_NAMES and not snake_case:
            raise ValueError(f"Function name must use snake_case: {location}")
    return len(functions)


def check_tracked_paths():
    paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    forbidden = {"env", ".venv", "__pycache__", ".ruff_cache", "Videoflix_frontend"}
    for value in paths.splitlines():
        path = Path(value)
        if forbidden & set(path.parts) or path.suffix in {".pyc", ".sqlite3", ".pem"}:
            raise ValueError(f"Local/generated file is tracked: {value}")
        if path.name == ".env" or ".runtime" in path.parts:
            raise ValueError(f"Runtime environment is tracked: {value}")


def main():
    sources = python_sources()
    count = sum(check_functions(path) for path in sources)
    check_tracked_paths()
    print(f"PASS: {len(sources)} Python files, {count} functions <=14 lines; "
          "clean tracked paths.")


if __name__ == "__main__":
    main()
