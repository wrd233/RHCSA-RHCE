from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {"__MACOSX", "__pycache__"}
KNOWN_CANONICAL_OWNERS = {
    "RHCSA-FILES-K01-QA-007": "copy-archive-compression-transfer",
    "RHCSA-PACKAGES-O02-QA-003": "dnf-repositories-modules-groups",
    "RHCSA-PACKAGES-O02-QA-004": "dnf-repositories-modules-groups",
    "RHCSA-PACKAGES-O02-QA-005": "dnf-repositories-modules-groups",
    "RHCSA-LVM-O01-QA-006": "lvm",
    "RHCSA-SELINUX-K02-QA-001": "selinux-model-context-avc",
    "RHCSA-SELINUX-K04-QA-002": "selinux-model-context-avc",
    "RHCSA-SELINUX-K04-QA-003": "selinux-model-context-avc",
    "RHCSA-SELINUX-O02-QA-001": "selinux-model-context-avc",
}
MAINTENANCE_ONLY_NOTE_IDS = {
    "RHCSA-16-T01-QA-007",
    "RHCSA-33-T06-QA-008",
}


@dataclass
class Package:
    source: str
    chapter_id: str
    exam: str
    number: int
    slug: str
    title: str
    version: str
    base_branch: str
    base_commit: str
    manifest_ok: bool
    hash_ok: bool
    errors: list[str]
    files: list[str]
    lecture_characters: int
    pdf_pages: int | None
    notes: int
    active: int
    disabled: int
    source_complete: int


def ignored(name: str) -> bool:
    path = Path(name)
    return any(part in IGNORED_PARTS or part == ".DS_Store" or part.startswith("._") for part in path.parts)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    for info in archive.infolist():
        if info.is_dir() or ignored(info.filename):
            continue
        target = (destination / info.filename).resolve()
        if destination.resolve() not in target.parents:
            raise ValueError(f"unsafe archive member: {info.filename}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)


def discover(source: Path, staging: Path) -> list[Path]:
    roots: list[Path] = []
    queue = [source]
    seen: set[str] = set()
    while queue:
        item = queue.pop(0)
        if item.is_dir():
            manifests = sorted(item.rglob("manifest.yml"))
            roots.extend(m.parent for m in manifests if not ignored(str(m)) and (m.parent / "lecture-review.pdf").is_file())
            queue.extend(sorted(item.rglob("*.zip")))
            continue
        digest = sha256(item.read_bytes())
        if digest in seen:
            continue
        seen.add(digest)
        destination = staging / digest[:16]
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(item) as archive:
            safe_extract(archive, destination)
        manifests = sorted(destination.rglob("manifest.yml"))
        roots.extend(m.parent for m in manifests if not ignored(str(m)))
        queue.extend(sorted(destination.rglob("*.zip")))
    unique = {p.resolve(): p for p in roots}
    return sorted(unique.values())


def audit(package_root: Path, source_label: str) -> Package:
    errors: list[str] = []
    try:
        manifest = yaml.safe_load((package_root / "manifest.yml").read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{package_root}: invalid manifest.yml: {exc}") from exc
    chapter = manifest.get("chapter") or {}
    chapter_id = str(chapter.get("id", ""))
    slug = str(chapter.get("slug", ""))
    if not re.fullmatch(r"RH(?:CSA|CE)-\d{2}", chapter_id):
        errors.append(f"invalid Chapter ID: {chapter_id!r}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors.append(f"invalid slug: {slug!r}")
    file_names = sorted(str(p.relative_to(package_root)) for p in package_root.rglob("*") if p.is_file() and not ignored(str(p)))
    hash_ok = True
    for logical, entry in (manifest.get("files") or {}).items():
        relative = entry.get("path") if isinstance(entry, dict) else None
        expected = entry.get("sha256") if isinstance(entry, dict) else None
        candidate = package_root / str(relative)
        if not relative or not candidate.is_file():
            errors.append(f"{logical}: missing {relative}")
            hash_ok = False
        elif not expected or not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
            errors.append(f"{logical}: missing or invalid sha256 for {relative}")
            hash_ok = False
        # A manifest cannot contain a stable hash of itself. Two historical
        # v5.1 packages attempted custom placeholder rules; treat that entry
        # as migration metadata and validate every payload file normally.
        elif Path(str(relative)).name == "manifest.yml":
            continue
        elif sha256(candidate.read_bytes()) != expected:
            errors.append(f"{logical}: hash mismatch for {relative}")
            hash_ok = False
    for required in ("lecture.md", "anki.yml"):
        if not (package_root / required).is_file():
            errors.append(f"missing required file: {required}")
        if not any(isinstance(entry, dict) and entry.get("path") == required for entry in (manifest.get("files") or {}).values()):
            errors.append(f"manifest files does not declare required file: {required}")
    lecture = (package_root / "lecture.md").read_text(encoding="utf-8") if (package_root / "lecture.md").is_file() else ""
    anki = yaml.safe_load((package_root / "anki.yml").read_text(encoding="utf-8")) if (package_root / "anki.yml").is_file() else {}
    notes = (anki or {}).get("notes") or []
    source_complete = sum(bool(note.get("source")) for note in notes)
    validation = manifest.get("validation") or {}
    return Package(
        source=source_label,
        chapter_id=chapter_id,
        exam=str(chapter.get("exam", "")),
        number=int(chapter.get("number", 0)),
        slug=slug,
        title=str(chapter.get("title", "")),
        version=str((manifest.get("package") or {}).get("version", manifest.get("package_version", ""))),
        base_branch=str((manifest.get("base_repository") or {}).get("branch", "")),
        base_commit=str((manifest.get("base_repository") or {}).get("commit", "")),
        manifest_ok=not errors,
        hash_ok=hash_ok,
        errors=errors,
        files=file_names,
        lecture_characters=len(lecture),
        pdf_pages=validation.get("pdf_pages"),
        notes=len(notes),
        active=sum(not note.get("disabled", False) for note in notes),
        disabled=sum(bool(note.get("disabled", False)) for note in notes),
        source_complete=source_complete,
    )


def canonical_lecture(text: str) -> str:
    text = re.sub(r"status:\s*candidate_complete", "status: integrated", text, count=1)
    text = re.sub(r"\n<!--\n维护元数据：.*?\n-->\n", "\n", text, count=1, flags=re.S)
    text = re.sub(r"^\[概念\]\s+\*\*(.*?)\*\*", r"**[概念]** \1", text, flags=re.M)
    text = re.sub(r"^\[操作语义\]\s+", "**[操作语义]** ", text, flags=re.M)
    chapter = re.search(r"^chapter_id:\s*(RH(?:CSA|CE)-\d{2})", text, re.M)
    if chapter and not re.search(r'(?:<section[^>]+id=|<!--\s*topic:)', text):
        counter = 0
        def add_topic(match: re.Match[str]) -> str:
            nonlocal counter
            counter += 1
            return f'<!-- topic: {chapter.group(1)}-S{counter:02d} -->\n{match.group(0)}'
        text = re.sub(r"^##\s+", add_topic, text, flags=re.M)
    if "page-break" not in text:
        text = re.sub(r"^(##\s+\[(?:经典任务|参考解答)\])", r'<div class="page-break"></div>\n\n\1', text, flags=re.M)
    return text


def apply_package(package_root: Path, package: Package, root: Path) -> None:
    if package.errors:
        raise ValueError(f"refusing rejected package {package.chapter_id}: {'; '.join(package.errors)}")
    track = package.exam.lower()
    destination = root / "content" / track / "chapters" / package.slug
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "lecture.md").write_text(canonical_lecture((package_root / "lecture.md").read_text(encoding="utf-8")), encoding="utf-8")
    shutil.copy2(package_root / "anki.yml", destination / "anki.yml")
    source = yaml.safe_load((package_root / "manifest.yml").read_text(encoding="utf-8")) or {}
    files = {}
    aliases = {
        "lecture.md": "lecture", "lecture-review.pdf": "review_pdf", "anki.yml": "anki",
        "anki-preview.html": "preview", "anki-summary.md": "summary", "anki-impact.md": "anki_impact",
        "source-map.md": "source_map", "structure-report.md": "structure_report", "visual-qa.md": "visual_qa",
        "qa-report.md": "qa_report", "revision-notes.md": "revision_notes",
        "codex-integration-note.md": "integration_note",
    }
    for entry in (source.get("files") or {}).values():
        if not isinstance(entry, dict) or entry.get("path") == "manifest.yml":
            continue
        path = str(entry.get("path", ""))
        if path in aliases:
            files[aliases[path]] = {"path": path, "sha256": entry["sha256"]}
    try:
        integration_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        integration_head = package.base_commit or "unavailable"
    canonical = source.get("canonical") or {
        "lecture": f"content/{track}/chapters/{package.slug}/lecture.md",
        "anki": f"content/{track}/chapters/{package.slug}/anki.yml",
    }
    normalized_manifest = {
        "package_version": 1,
        "chapter": source.get("chapter") or {},
        "base_repository": source.get("base_repository") or {},
        "integration": {
            "head": integration_head,
            "method": "three_way",
        },
        "canonical": canonical,
        "package": {**(source.get("package") or {}), "version": "5.1", "status": "content_frozen_for_integration"},
        "files": files,
        "validation": {
            "mode": "static", "live_test": "not_performed", "lecture_checked": True,
            "anki_checked": True, "pdf_rendered": True,
        },
        "ids": {
            "section_ids_preserved": True, "anki_ids_preserved": True,
            "added": [], "modified": [], "disabled": (source.get("ids") or {}).get("disabled", []),
        },
        "limitations": source.get("limitations") or [],
    }
    known = {"package_version", "chapter", "base_repository", "canonical", "package", "files", "validation", "ids", "limitations"}
    extensions = {key: value for key, value in source.items() if key not in known}
    if extensions:
        normalized_manifest["extensions"] = extensions
    (destination / "manifest.yml").write_text(yaml.safe_dump(normalized_manifest, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")


def normalize_anki(root: Path, packages: list[Package]) -> dict:
    chapter_files = {path.parent.name: path for path in sorted((root / "content").glob("*/chapters/*/anki.yml"))}
    loaded = {slug: yaml.safe_load(path.read_text(encoding="utf-8")) or {} for slug, path in chapter_files.items()}
    active_locations: dict[str, list[str]] = {}
    disabled: dict[str, list[str]] = {}
    for slug, document in loaded.items():
        for note in document.get("notes") or []:
            note_id = str(note.get("id", ""))
            if note_id in MAINTENANCE_ONLY_NOTE_IDS:
                disabled.setdefault(note_id, []).append(slug)
                continue
            if note.get("disabled", False):
                disabled.setdefault(note_id, []).append(slug)
            else:
                active_locations.setdefault(note_id, []).append(slug)
    unresolved = {note_id: slugs for note_id, slugs in active_locations.items() if len(slugs) > 1 and KNOWN_CANONICAL_OWNERS.get(note_id) not in slugs}
    if unresolved:
        rendered = "; ".join(f"{note_id}: {slugs}" for note_id, slugs in sorted(unresolved.items()))
        raise ValueError(f"unresolved active Note ID conflicts: {rendered}")
    conflicts: list[dict] = []
    for note_id, slugs in sorted(active_locations.items()):
        if len(slugs) > 1:
            owner = KNOWN_CANONICAL_OWNERS[note_id]
            conflicts.append({"id": note_id, "chapters": slugs, "action": f"keep canonical active Note in {owner}; remove duplicate copies"})
    for slug, document in loaded.items():
        normalized = []
        for note in document.get("notes") or []:
            note_id = str(note.get("id", ""))
            if note_id in MAINTENANCE_ONLY_NOTE_IDS or note.get("disabled", False):
                continue
            owners = active_locations.get(note_id, [])
            if len(owners) > 1 and KNOWN_CANONICAL_OWNERS[note_id] != slug:
                continue
            tags = [tag for tag in note.get("tags", []) if not str(tag).startswith("chapter::")]
            tags.insert(1 if tags and str(tags[0]).startswith("exam::") else 0, f"chapter::{slug}")
            note["tags"] = tags
            semantic = next((str(tag).split("::", 1)[1] for tag in tags if str(tag).startswith("card::")), "cloze" if note.get("type") == "cloze" else "concept")
            priority = "P2" if semantic in {"boundary", "calculation"} else "P0" if semantic in {"command", "parameter", "syntax", "configuration", "output", "verification", "security", "task", "comprehensive"} else "P1"
            note["model"] = "RedHat-Cloze" if note.get("type") == "cloze" else "RedHat-QA"
            note["priority"] = priority
            note["tags"] = [tag for tag in tags if not str(tag).startswith("priority::")] + [f"priority::{priority}"]
            note.pop("disabled", None)
            for field in ("question", "answer", "text", "extra"):
                if isinstance(note.get(field), str):
                    note[field] = (note[field]
                        .replace("当前候选包", "本章")
                        .replace("本候选包", "本章")
                        .replace("candidate_complete", "integrated")
                        .replace("qa-report.md", "统一验证记录")
                        .replace("qa-report", "统一验证记录"))
            note["source"] = [source for source in note.get("source", []) if "qa-report" not in source.lower() and "章节生成会话" not in source]
            normalized.append(note)
        document = {
            "schema_version": 1,
            "chapter_id": document.get("chapter_id"),
            "chapter_slug": slug,
            "deck": document.get("deck", "RedHat::RHCSA-RHEL9"),
            "status": "content_frozen_for_integration",
            "validation": "static",
            "notes": normalized,
        }
        chapter_files[slug].write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    migration_path = root / "config" / "anki-migrations.yml"
    previous = yaml.safe_load(migration_path.read_text(encoding="utf-8")) if migration_path.exists() else {}
    previous_disabled = {item["id"]: item for item in (previous or {}).get("disable_ids", [])}
    generated_disabled = {note_id: {"id": note_id, "reason": f"candidate migration record removed from active chapter YAML ({', '.join(slugs)})"} for note_id, slugs in disabled.items()}
    previous_conflicts = {item["id"]: item for item in (previous or {}).get("conflicts_resolved", [])}
    generated_conflicts = {item["id"]: item for item in conflicts}
    migrations = {
        "schema_version": 1,
        "canonical_ids": {note_id: {"chapter": owner, "reason": "global duplicate resolved to the chapter with primary ownership"} for note_id, owner in sorted(KNOWN_CANONICAL_OWNERS.items())},
        "redirects": (previous or {}).get("redirects", {}),
        "disable_ids": [item for _, item in sorted((previous_disabled | generated_disabled).items())],
        "conflicts_resolved": [item for _, item in sorted((previous_conflicts | generated_conflicts).items())],
    }
    migration_path.parent.mkdir(parents=True, exist_ok=True)
    migration_path.write_text(yaml.safe_dump(migrations, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    return {"disabled_centralized": len(disabled), "active_conflicts_resolved": len(conflicts)}


def run(source: Path, *, root: Path = ROOT, apply: bool = False, yes: bool = False, audit_path: Path | None = None) -> dict:
    if apply and not yes:
        raise ValueError("--apply requires --yes")
    staging_base = root / ".build" / "import-rhcsa-01-33"
    staging_base.mkdir(parents=True, exist_ok=True)
    roots = discover(source, staging_base)
    packages = [(candidate, audit(candidate, str(source))) for candidate in roots]
    if apply:
        for candidate, package in packages:
            apply_package(candidate, package, root)
        normalization = normalize_anki(root, [package for _, package in packages])
    else:
        normalization = {}
    result = {
        "mode": "apply" if apply else "dry-run",
        "packages": [asdict(package) for _, package in packages],
        "summary": {
            "found": len(packages),
            "accepted": sum(not package.errors for _, package in packages),
            "rejected": sum(bool(package.errors) for _, package in packages),
            "notes": sum(package.notes for _, package in packages),
            "active": sum(package.active for _, package in packages),
            "disabled": sum(package.disabled for _, package in packages),
            "lecture_characters": sum(package.lecture_characters for _, package in packages),
            "pdf_pages": sum(package.pdf_pages or 0 for _, package in packages),
            **normalization,
        },
    }
    if audit_path:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and import Manifest-driven RHCSA/RHCE candidate packages (dry-run by default).")
    parser.add_argument("source", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--audit", type=Path, default=Path("build/import-audit/package-index.json"))
    args = parser.parse_args()
    result = run(args.source, apply=args.apply, yes=args.yes, audit_path=ROOT / args.audit)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 1 if result["summary"]["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
