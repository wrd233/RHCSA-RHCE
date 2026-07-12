#!/usr/bin/env python3
"""Explicit, ID-based AnkiConnect synchronization.

The release build never imports or calls this module.  Without ``--apply`` the
script only parses the YAML and prints a plan; it does not contact AnkiConnect.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from build_apkg import CARD_CSS
from common import ROOT, load_yaml, safe_markdown_to_html

ENDPOINT = "http://127.0.0.1:8765"
MODELS = {
    "qa": {
        "name": "RedHat-QA",
        "fields": ["ID", "Question", "Answer", "Extra", "Source"],
        "templates": [{
            "Name": "RedHat-QA",
            "Front": "{{Question}}",
            "Back": '{{Answer}}<div class="extra">{{Extra}}</div><div class="source">{{Source}}</div>',
        }],
        "is_cloze": False,
    },
    "cloze": {
        "name": "RedHat-Cloze",
        "fields": ["ID", "Text", "Extra", "Source"],
        "templates": [{
            "Name": "RedHat-Cloze",
            "Front": "{{cloze:Text}}",
            "Back": '{{cloze:Text}}<div class="extra">{{Extra}}</div><div class="source">{{Source}}</div>',
        }],
        "is_cloze": True,
    },
}


def invoke(action: str, endpoint: str = ENDPOINT, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    request = urllib.request.Request(endpoint, payload, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot reach AnkiConnect at {endpoint}: {exc}") from exc
    if result.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {result['error']}")
    return result.get("result")


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def note_fields(note: dict) -> dict[str, str]:
    if note["type"] == "qa":
        return {
            "ID": note["id"],
            "Question": safe_markdown_to_html(note["question"]),
            "Answer": safe_markdown_to_html(note["answer"]),
            "Extra": safe_markdown_to_html(note.get("extra")),
            "Source": safe_markdown_to_html("; ".join(note.get("source") or [])),
        }
    return {
        "ID": note["id"],
        "Text": safe_markdown_to_html(note["text"]),
        "Extra": safe_markdown_to_html(note.get("extra")),
        "Source": safe_markdown_to_html("; ".join(note.get("source") or [])),
    }


def ensure_models(endpoint: str) -> None:
    existing = set(invoke("modelNames", endpoint=endpoint))
    for spec in MODELS.values():
        if spec["name"] not in existing:
            invoke(
                "createModel",
                endpoint=endpoint,
                modelName=spec["name"],
                inOrderFields=spec["fields"],
                css=CARD_CSS,
                isCloze=spec["is_cloze"],
                cardTemplates=spec["templates"],
            )
        actual = invoke("modelFieldNames", endpoint=endpoint, modelName=spec["name"])
        if actual != spec["fields"]:
            raise RuntimeError(
                f"model {spec['name']} fields are {actual}; expected {spec['fields']}; "
                "refusing an unsafe automatic migration"
            )


def locate(note_id: str, endpoint: str) -> list[int]:
    return invoke("findNotes", endpoint=endpoint, query=f'ID:"{_quote(note_id)}"')


def sync_note(note: dict, deck: str, endpoint: str) -> str:
    matches = locate(note["id"], endpoint)
    if len(matches) > 1:
        raise RuntimeError(f"stable ID {note['id']} matches multiple Anki notes: {matches}")
    if note.get("disabled"):
        if not matches:
            return "disabled-missing"
        cards = invoke("findCards", endpoint=endpoint, query=f"nid:{matches[0]}")
        if cards:
            invoke("suspend", endpoint=endpoint, cards=cards)
        return "suspended"

    spec = MODELS[note["type"]]
    fields = note_fields(note)
    tags = list(dict.fromkeys(note.get("tags") or []))
    if not matches:
        invoke(
            "addNote",
            endpoint=endpoint,
            note={
                "deckName": deck,
                "modelName": spec["name"],
                "fields": fields,
                "tags": tags,
                "options": {"allowDuplicate": False},
            },
        )
        return "added"

    note_id = matches[0]
    info = invoke("notesInfo", endpoint=endpoint, notes=[note_id])[0]
    if info["modelName"] != spec["name"]:
        raise RuntimeError(
            f"{note['id']} uses {info['modelName']}, expected {spec['name']}; "
            "refusing an unsafe note-type change"
        )
    invoke("updateNoteFields", endpoint=endpoint, note={"id": note_id, "fields": fields})
    old_tags = info.get("tags") or []
    if old_tags:
        invoke("removeTags", endpoint=endpoint, notes=[note_id], tags=" ".join(old_tags))
    if tags:
        invoke("addTags", endpoint=endpoint, notes=[note_id], tags=" ".join(tags))
    cards = info.get("cards") or invoke("findCards", endpoint=endpoint, query=f"nid:{note_id}")
    if cards:
        invoke("unsuspend", endpoint=endpoint, cards=cards)
    return "updated"


def collect(paths: list[Path]) -> list[tuple[Path, dict]]:
    collected: list[tuple[Path, dict]] = []
    for path in paths:
        data = load_yaml(path)
        if not isinstance(data, dict) or not data.get("deck") or not isinstance(data.get("notes"), list):
            raise ValueError(f"invalid Anki source: {path}")
        collected.append((path, data))
    return collected


def load_migrations() -> dict:
    path = ROOT / "config" / "anki-migrations.yml"
    data = load_yaml(path) if path.exists() else {}
    if data and data.get("schema_version") != 1:
        raise ValueError(f"unsupported Anki migration schema: {path}")
    return data or {"disable_ids": [], "redirects": {}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize YAML notes by stable ID")
    parser.add_argument("sources", nargs="*", type=Path, help="one or more chapter anki.yml files")
    parser.add_argument("--all", action="store_true", help="use every content/**/anki.yml source")
    parser.add_argument("--apply", action="store_true", help="contact AnkiConnect and perform writes")
    parser.add_argument("--yes", action="store_true", help="confirm the explicit apply operation")
    parser.add_argument("--endpoint", default=ENDPOINT)
    args = parser.parse_args()

    if args.all and args.sources:
        parser.error("use either explicit sources or --all")
    paths = sorted((ROOT / "content").glob("**/anki.yml")) if args.all else args.sources
    if not paths:
        parser.error("provide source files or --all")
    items = collect(paths)
    migrations = load_migrations()
    counts = {"active": 0, "disabled": 0}
    for _, data in items:
        for note in data["notes"]:
            counts["disabled" if note.get("disabled") else "active"] += 1

    if not args.apply:
        print(
            f"DRY RUN: {len(items)} source file(s), {counts['active']} active note(s), "
            f"{counts['disabled']} disabled note(s), {len(migrations.get('disable_ids', []))} centralized disable ID(s), "
            f"{len(migrations.get('redirects', {}))} redirect(s); AnkiConnect was not called"
        )
        return 0
    if not args.yes:
        parser.error("--apply also requires --yes; this prevents accidental writes")

    invoke("version", endpoint=args.endpoint)
    ensure_models(args.endpoint)
    results: dict[str, int] = {}
    for path, data in items:
        invoke("createDeck", endpoint=args.endpoint, deck=data["deck"])
        for note in data["notes"]:
            result = sync_note(note, data["deck"], args.endpoint)
            results[result] = results.get(result, 0) + 1
        print(f"synced {path}")
    print("sync result: " + ", ".join(f"{key}={value}" for key, value in sorted(results.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
