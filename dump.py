from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / "steamlayer"
OUTPUT = ROOT / "project_dump.txt"

INCLUDE_EXTENSIONS = {".py", ".toml", ".md", ".yaml", ".yml"}
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache"}


def should_include(path: pathlib.Path) -> bool:
    if path.suffix not in INCLUDE_EXTENSIONS:
        return False

    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return False

    return True


def main() -> None:
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and should_include(p))

    with OUTPUT.open("w", encoding="utf-8") as out:
        for file in files:
            rel = file.relative_to(ROOT)

            out.write(f"\n{'=' * 80}\n")
            out.write(f"# FILE: {rel}\n")
            out.write(f"{'=' * 80}\n\n")

            try:
                content = file.read_text(encoding="utf-8")
            except Exception as e:
                out.write(f"# ERROR READING FILE: {e}\n")
                continue

            out.write(content)
            out.write("\n\n")

    print(f"Dump written to: {OUTPUT}")


if __name__ == "__main__":
    main()
