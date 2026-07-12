#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from common import ROOT, iter_chapters


def run(*args: str) -> None:
    command = [sys.executable, str(ROOT / "tools" / args[0]), *args[1:]]
    print("+", " ".join(command))
    subprocess.run(command, check=True, cwd=ROOT)


def main() -> int:
    missing = []
    for chapter in iter_chapters():
        for filename in ("lecture.md", "anki.yml"):
            if not (chapter["path"] / filename).exists():
                missing.append(str((chapter["path"] / filename).relative_to(ROOT)))
    if missing:
        print("release blocked; missing content sources:\n- " + "\n- ".join(missing), file=sys.stderr)
        return 1
    run("validate_lecture.py")
    run("validate_anki.py")
    run("build_anki_preview.py", "--all")
    run("build_lecture.py", "--all-chapters")
    run("build_lecture.py", "--book", "rhcsa")
    run("build_lecture.py", "--book", "rhce")
    run("build_lecture.py", "--book", "combined")
    run("build_apkg.py", "rhcsa")
    run("build_apkg.py", "rhce")
    print("release build complete; AnkiConnect was not called")
    return 0


if __name__ == "__main__":
    sys.exit(main())

