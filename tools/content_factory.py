from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def write_chapter(*, track, slug, number, title, chapter_id, sources, intro, concepts, semantics, topics, task, solution, closing, cards):
    base = ROOT / "content" / track
    if track != "common":
        base /= "chapters"
    base /= slug
    base.mkdir(parents=True, exist_ok=True)
    lines = [
        "---", f'title: "{number} {title}"', f"chapter_id: {chapter_id}",
        f"exam: {track.upper()}", "validation: static-verified",
        "sources: [" + ", ".join(sources) + "]", "---", "",
        f"# {number}　{title}", "", intro, "",
    ]
    lines += [f"**[概念]** {x}\n" for x in concepts]
    lines += [f"**[操作语义]** {x}\n" for x in semantics]
    for topic in topics:
        sid, kind, heading, body, cheat = topic
        css = "diagnosis" if kind == "诊断专题" else ("operation" if kind == "操作专题" else "knowledge")
        lines += [f'<section class="topic {css}" id="{sid}" data-kind="{css}-topic">', "",
                  f'## <span class="topic-label">[{kind}]</span> {heading}', "", body, "",
                  f"**[Cheatsheet]** {cheat}", "", "</section>", ""]
    lines += [f'<section class="classic-task task-page" id="{chapter_id}-C01" data-kind="classic-task">', "",
              f'## <span class="topic-label">[经典任务]</span> {task[0]}', "", task[1], "",
              "> 请先独立完成。参考解答从下一页开始。", "", "</section>", "",
              f'<section class="classic-task solution-page" id="{chapter_id}-C01-SOLUTION" data-kind="classic-task-solution">', "",
              f'## <span class="topic-label">[参考解答]</span> {solution[0]}', "", solution[1], "",
              f"**[Cheatsheet]** {solution[2]}", "", "</section>", "",
              f'<section class="topic closing" id="{chapter_id}-CLOSE" data-kind="chapter-closing">', "",
              f'## <span class="topic-label">[本章收束]</span> {closing[0]}', "", closing[1], "", "</section>", ""]
    (base / "lecture.md").write_text("\n".join(lines), encoding="utf-8")

    exam = track
    notes = []
    for i, card in enumerate(cards, 1):
        question, answer, extra, ctype, priority = card
        notes.append({
            "id": f"{chapter_id}-QA-{i:03d}", "type": "qa", "question": question,
            "answer": answer, "extra": extra, "source": list(sources),
            "tags": [f"exam::{exam}", f"chapter::{slug}", f"card::{ctype}", f"priority::{priority}"],
        })
    payload = {"chapter_id": chapter_id, "deck": f"RedHat::{track.upper()}-RHEL9", "note_types": ["RedHat-QA", "RedHat-Cloze"], "notes": notes}
    (base / "anki.yml").write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")

