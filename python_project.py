from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent
OUTPUT_FILE = PROJECT_FOLDER / "project_code.txt"

ALLOWED_EXTENSIONS = {
    ".py",
    ".html",
    ".css",
    ".js",
    ".txt",
}

EXCLUDED_FOLDERS = {
    "venv",
    ".venv",
    "env",
    ".idea",
    "__pycache__",
    "staticfiles",
    "node_modules",
    ".git",
}

EXCLUDED_FILES = {
    "project_code.txt",
    ".env",
    "db.sqlite3",
}

with OUTPUT_FILE.open("w", encoding="utf-8") as output:
    for file_path in PROJECT_FOLDER.rglob("*"):
        if not file_path.is_file():
            continue

        if any(folder in file_path.parts for folder in EXCLUDED_FOLDERS):
            continue

        if file_path.name in EXCLUDED_FILES:
            continue

        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        relative_path = file_path.relative_to(PROJECT_FOLDER)

        output.write("\n")
        output.write("=" * 70)
        output.write(f"\nFILE: {relative_path}\n")
        output.write("=" * 70)
        output.write("\n\n")

        try:
            content = file_path.read_text(encoding="utf-8")
            output.write(content)
        except UnicodeDecodeError:
            output.write("[Could not read this file because of its encoding.]")

        output.write("\n")

print(f"File created successfully:\n{OUTPUT_FILE}")