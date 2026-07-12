#!/usr/bin/env python3
"""Explicit, ID-based AnkiConnect synchronization.

The release build never imports or calls this module.  Without ``--apply`` the
script only parses the YAML and prints a plan; it does not contact AnkiConnect.
"""
from __future__ import annotations

import argparse
import json
import datetime
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
            "Back": '{{Answer}}<div class="extra">{{Extra}}</div>',
        }],
        "is_cloze": False,
    },
    "cloze": {
        "name": "RedHat-Cloze",
        "fields": ["ID", "Text", "Extra", "Source"],
        "templates": [{
            "Name": "RedHat-Cloze",
            "Front": "{{cloze:Text}}",
            "Back": '{{cloze:Text}}<div class="extra">{{Extra}}</div>',
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
        return "disabled-skipped"

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
    actual_fields = {key: value.get("value", "") for key, value in info["fields"].items()}
    fields_changed = any(actual_fields.get(key) != value for key, value in fields.items())
    old_tags = info.get("tags") or []
    tags_changed = sorted(old_tags) != sorted(tags)
    if not fields_changed and not tags_changed:
        return "unchanged"
    if fields_changed:
        invoke("updateNoteFields", endpoint=endpoint, note={"id": note_id, "fields": fields})
    if tags_changed and old_tags:
        invoke("removeTags", endpoint=endpoint, notes=[note_id], tags=" ".join(old_tags))
    if tags_changed and tags:
        invoke("addTags", endpoint=endpoint, notes=[note_id], tags=" ".join(tags))
    return "updated"


def project_snapshot(endpoint: str, path: Path) -> list[int]:
    ids = sorted(set(invoke("findNotes", endpoint=endpoint, query='note:"RedHat-QA"') + invoke("findNotes", endpoint=endpoint, query='note:"RedHat-Cloze"')))
    infos = []
    for start in range(0, len(ids), 200):
        infos.extend(invoke("notesInfo", endpoint=endpoint, notes=ids[start:start + 200]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(infos, ensure_ascii=False, indent=2), encoding="utf-8")
    return ids


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
    parser.add_argument("--exam", choices=["rhcsa", "rhce"], help="limit common notes to the target exam")
    parser.add_argument("--apply", action="store_true", help="contact AnkiConnect and perform writes")
    parser.add_argument("--yes", action="store_true", help="confirm the explicit apply operation")
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if args.all and args.sources:
        parser.error("use either explicit sources or --all")
    paths = sorted((ROOT / "content").glob("**/anki.yml")) if args.all else args.sources
    if not paths:
        parser.error("provide source files or --all")
    items = collect(paths)
    if args.exam:
        scoped = []
        for path, data in items:
            if f"content/{args.exam}/" not in path.as_posix() and "content/common/" not in path.as_posix():
                continue
            copy = dict(data)
            if "content/common/" in path.as_posix():
                copy["notes"] = [n for n in data["notes"] if f"exam::{args.exam}" in (n.get("tags") or [])]
            scoped.append((path, copy))
        items = scoped
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

    version = invoke("version", endpoint=args.endpoint)
    ensure_models(args.endpoint)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / "backups" / "anki" / f"RHCSA-before-sync-{stamp}.notes.json"
    before_ids = project_snapshot(args.endpoint, backup)
    results: dict[str, int] = {}
    if not before_ids:
        pending = []
        pending_ids = []
        for _, data in items:
            invoke("createDeck", endpoint=args.endpoint, deck=data["deck"])
            for note in data["notes"]:
                if note.get("disabled"):
                    results["disabled-skipped"] = results.get("disabled-skipped", 0) + 1
                    continue
                spec = MODELS[note["type"]]
                pending.append({"deckName": data["deck"], "modelName": spec["name"], "fields": note_fields(note),
                                "tags": list(dict.fromkeys(note.get("tags") or [])), "options": {"allowDuplicate": False}})
                pending_ids.append(note["id"])
        for start in range(0, len(pending), 100):
            batch = pending[start:start + 100]
            added = invoke("addNotes", endpoint=args.endpoint, notes=batch)
            failed = [pending_ids[start+i] for i, value in enumerate(added) if value is None]
            if failed:
                raise RuntimeError(f"addNotes batch failed for stable IDs: {failed}")
            results["added"] = results.get("added", 0) + len(batch)
        items = []
    for path, data in items:
        invoke("createDeck", endpoint=args.endpoint, deck=data["deck"])
        for note in data["notes"]:
            result = sync_note(note, data["deck"], args.endpoint)
            results[result] = results.get(result, 0) + 1
        print(f"synced {path}")
    after_ids = project_snapshot(args.endpoint, ROOT / "backups" / "anki" / f"RHCSA-after-sync-{stamp}.notes.json")
    summary = {"endpoint": args.endpoint, "api_version": version, "backup": str(backup), "before_notes": len(before_ids), "after_notes": len(after_ids), "results": results}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("sync result: " + ", ".join(f"{key}={value}" for key, value in sorted(results.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
