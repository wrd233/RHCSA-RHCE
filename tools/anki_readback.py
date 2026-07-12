#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from sync_anki import invoke

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--endpoint",default="http://127.0.0.1:8765"); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    model_ids={}
    all_ids=[]
    templates={}
    fields={}
    for model in ("RedHat-QA","RedHat-Cloze"):
        ids=invoke("findNotes",endpoint=a.endpoint,query=f'note:"{model}"')
        model_ids[model]=ids; all_ids.extend(ids)
        templates[model]=invoke("modelTemplates",endpoint=a.endpoint,modelName=model)
        fields[model]=invoke("modelFieldNames",endpoint=a.endpoint,modelName=model)
    infos=[]
    for start in range(0,len(all_ids),200): infos.extend(invoke("notesInfo",endpoint=a.endpoint,notes=all_ids[start:start+200]))
    stable=[i.get("fields",{}).get("ID",{}).get("value","") for i in infos]
    duplicates=sorted({x for x in stable if x and stable.count(x)>1})
    cards=[]
    for start in range(0,len(all_ids),500): cards.extend(invoke("findCards",endpoint=a.endpoint,query=" OR ".join(f"nid:{x}" for x in all_ids[start:start+500])))
    chapters={}
    for info in infos:
        for tag in info.get("tags",[]):
            if tag.startswith("chapter::"): chapters.setdefault(tag,[]).append(info)
    samples=[]
    for chapter in sorted(chapters)[:10]:
        for info in chapters[chapter]:
            samples.append({"chapter":chapter,"model":info["modelName"],"id":info["fields"]["ID"]["value"],"fields":{k:v["value"] for k,v in info["fields"].items()},"tags":info["tags"]})
            if sum(s["chapter"]==chapter for s in samples)>=2: break
    report={"endpoint":a.endpoint,"api_version":invoke("version",endpoint=a.endpoint),"notes":len(all_ids),"cards":len(cards),
            "by_model":{k:len(v) for k,v in model_ids.items()},"fields":fields,"templates_hide_source":all("{{Source}}" not in str(t) for t in templates.values()),
            "duplicate_stable_ids":duplicates,"chapter_count":len(chapters),"samples":samples[:20],"errors":[]}
    if report["notes"]!=3353 or report["cards"]!=3700 or duplicates or not report["templates_hide_source"]: report["errors"].append("readback invariant failed")
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in {"samples"}},ensure_ascii=False,indent=2))
    return bool(report["errors"])
if __name__=="__main__": raise SystemExit(main())
