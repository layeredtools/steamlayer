import pathlib

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build", ".ruff_cache"}
EXCLUDE_FILES = {"project_dump.txt", "uv.lock", ".DS_Store"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".exe", ".bin", ".png", ".jpg"}


def generate_dump(root_path: pathlib.Path, output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        for path in sorted(root_path.rglob("*")):
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue

            if path.is_file():
                if path.name in EXCLUDE_FILES or path.suffix in EXCLUDE_EXTS:
                    continue

                try:
                    f.write("\n" + "=" * 80 + "\n")
                    f.write(f"# FILE: {path.relative_to(root_path)}\n")
                    f.write("=" * 80 + "\n\n")

                    content = path.read_text(encoding="utf-8")
                    f.write(content)
                    f.write("\n")
                except Exception as e:
                    f.write(f"\n[ERROR READING FILE {path.name}: {e}]\n")


if __name__ == "__main__":
    project_root = pathlib.Path(__file__).parent
    output_path = project_root / "project_dump.txt"

    print(f"Generating dump at {output_path}...")
    generate_dump(project_root, str(output_path))
    print("Done!")
