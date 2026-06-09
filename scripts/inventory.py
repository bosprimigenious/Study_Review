#!/usr/bin/env python3
"""List likely study materials grouped by subject folder."""

from __future__ import annotations

import argparse
from pathlib import Path


STUDY_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".md", ".txt", ".docx"}


def scan(root: Path, max_depth: int) -> dict[str, list[Path]]:
    subjects: dict[str, list[Path]] = {}
    root = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in STUDY_EXTENSIONS:
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if len(relative.parts) > max_depth:
            continue
        subject = relative.parts[0] if len(relative.parts) > 1 else "."
        subjects.setdefault(subject, []).append(relative)
    return subjects


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Workspace or course root")
    parser.add_argument("--max-depth", type=int, default=3)
    args = parser.parse_args()

    subjects = scan(Path(args.root), args.max_depth)
    for subject, files in subjects.items():
        print(f"\n## {subject}")
        for file in files:
            print(f"- {file}")


if __name__ == "__main__":
    main()
