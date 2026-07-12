#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from common import ROOT, iter_chapters, rel, strip_front_matter

TOPIC_RE = re.compile(
    r'<section[^>]+class="[^"]*\b(topic|classic-task)\b[^"]*"[^>]*>(.*?)</section>',
    re.S,
)
ID_RE = re.compile(r'(?:<section[^>]+id="([A-Za-z0-9_-]+)"|<!--\s*topic:\s*([A-Za-z0-9_-]+)\s*-->)')


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    try:
        meta, body = strip_front_matter(text)
    except Exception as exc:
        return [str(exc)], []
    for field in ("chapter_id", "exam", "sources"):
        if not meta.get(field):
            errors.append(f"missing front matter field: {field}")
    if not (meta.get("title") or meta.get("chapter_title")):
        errors.append("missing front matter field: title or chapter_title")
    if not re.search(r"^# .+", body, re.M):
        errors.append("missing chapter H1")
    if "**[概念]**" not in body:
        errors.append("missing chapter-opening [概念]")
    if "**[操作语义]**" not in body:
        errors.append("missing chapter-opening [操作语义]")
    for marker in ("[经典任务]", "[参考解答]", "[本章收束]"):
        if marker not in body:
            errors.append(f"missing {marker}")
    task_breaks = len(re.findall(r'class="[^"]*page-break', body)) + body.count("task-page") + body.count("solution-page")
    if task_breaks < 1:
        errors.append("classic task and solution require an explicit page break")
    ids = [left or right for left, right in ID_RE.findall(body)]
    if not ids:
        errors.append("no stable section IDs")
    if len(ids) != len(set(ids)):
        errors.append("duplicate stable section ID in chapter")
    for _, section in TOPIC_RE.findall(body):
        heading = re.search(r"^##\s+(.+)$", section, re.M)
        title = re.sub("<[^>]+>", "", heading.group(1)) if heading else "unknown topic"
        if any(tag in title for tag in ("[知识专题]", "[操作专题]", "[诊断专题]")):
            if "[Cheatsheet]" not in section:
                errors.append(f"topic missing Cheatsheet: {title}")
        if "[操作专题]" in title and not re.search(r"\[验证点\]|\*\*\[验证\]\*\*", section):
            warnings.append(f"operation topic has no explicit verification marker: {title}")
    for phrase in ("执行后实测得到", "后续补充", "TODO", "TBD"):
        if phrase in body:
            errors.append(f"prohibited or placeholder phrase: {phrase}")
    if re.search(r"^#{2,3}\s+(?:\[[^]]+\]\s*)?(?:来源(?:说明)?|版本说明|稳定 ID)\s*$", body, re.M):
        errors.append("visible maintenance metadata heading")
    fences = len(re.findall(r"^```", body, re.M))
    if fences % 2:
        errors.append("unclosed fenced code block")
    for number, snippet in enumerate(re.findall(r"```ya?ml\n(.*?)\n```", body, re.S), 1):
        try:
            yaml.safe_load(snippet)
        except yaml.YAMLError as exc:
            problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
            errors.append(f"YAML code block #{number} is invalid: {problem}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or [c["path"] / "lecture.md" for c in iter_chapters() if (c["path"] / "lecture.md").exists()]
    failures = 0
    for path in paths:
        errors, warnings = validate(path)
        for item in warnings:
            print(f"WARN {rel(path)}: {item}")
        for item in errors:
            print(f"ERROR {rel(path)}: {item}")
        failures += len(errors)
    print(f"lecture validation: {len(paths)} file(s), {failures} error(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
