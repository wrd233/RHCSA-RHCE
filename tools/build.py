from __future__ import annotations

import argparse
import subprocess
import sys

from build_anki_preview import build as build_preview
from build_apkg import build as build_apkg
from build_lecture import build_book, build_chapter
from common import iter_chapters, load_manifest


def release_ready(track: str, manifest: dict) -> bool:
    chapters = manifest[track]["chapters"]
    return bool(chapters) and all(chapter.get("status") in {"validated", "released"} for chapter in chapters)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V2 chapters, books and Anki packages.")
    parser.add_argument("track", choices=["rhcsa", "rhce"])
    parser.add_argument("--chapter")
    parser.add_argument("--all-chapters", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.chapter:
        chapters = [chapter for chapter in iter_chapters([args.track]) if chapter["slug"] == args.chapter]
        if not chapters:
            print(f"chapter is pending or unknown: {args.chapter}", file=sys.stderr)
            return 1
        build_chapter(chapters[0])
        build_preview(chapters[0])
        return 0
    complete = release_ready(args.track, manifest)
    if not complete and not args.allow_incomplete:
        pending = [c["id"] for c in manifest[args.track]["chapters"] if c.get("status") not in {"validated", "released"}]
        print("formal release blocked: " + ", ".join(pending), file=sys.stderr)
        return 1
    chapters = list(iter_chapters([args.track]))
    if args.all_chapters:
        for chapter in chapters:
            build_chapter(chapter)
            build_preview(chapter)
    build_book(args.track, incomplete=not complete)
    build_apkg(args.track, incomplete=not complete)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
