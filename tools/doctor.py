#!/usr/bin/env python3
from __future__ import annotations
import json, platform, urllib.request
from pathlib import Path
from common import ROOT, find_chrome

def main() -> int:
    checks = {"python": platform.python_version(), "chrome": str(find_chrome() or "missing"),
              "font": any(Path("/System/Library/Fonts").glob("**/*Song*")),
              "pdf_output": str(ROOT / "dist" / "rhcsa" / "reading")}
    try:
        request = urllib.request.Request("http://127.0.0.1:8765", json.dumps({"action":"version","version":6}).encode(), {"Content-Type":"application/json"})
        checks["ankiconnect"] = json.load(urllib.request.urlopen(request, timeout=3))["result"]
    except Exception as exc:
        checks["ankiconnect"] = f"unreachable: {exc}"
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 1 if checks["chrome"] == "missing" else 0
if __name__ == "__main__": raise SystemExit(main())
