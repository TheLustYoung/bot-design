"""Exports the service list of the bot to site/data/services.json so the website and the bot always show the same services and questions."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bot.faq import answer  # noqa: E402
from bot.flow import LABELS  # noqa: E402
from bot.services import GROUPS, SERVICES  # noqa: E402

SKIP = {"source", "files", "design_text", "doc_text", "deadline_text", "address"}
out = {"groups": [{"key": k, "title": t} for k, t in GROUPS if k != "hidden"], "services": []}
for key, svc in SERVICES.items():
    if svc.get("group") == "hidden":
        continue
    asks, seen = [], set()
    for st in svc["steps"]:
        if st["id"] in SKIP or st["id"] in seen or st["id"] not in LABELS:
            continue
        seen.add(st["id"])
        asks.append(LABELS[st["id"]])
    out["services"].append({"key": key, "emoji": svc["emoji"], "title": svc["title"], "group": svc["group"], "asks": asks[:5]})
out["faq"] = {k: {l: answer(k, l) for l in ("ru", "en", "hy")} for k in ("price", "timing", "files", "payment", "delivery", "minimum", "hours", "address")}
(ROOT / "site" / "data" / "services.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out["services"]), "services exported")
