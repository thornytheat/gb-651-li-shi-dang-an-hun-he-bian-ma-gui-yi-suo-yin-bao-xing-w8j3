import csv, io
from app.manifest import canonical_digest, run_id
SAMPLE = {"store": None, "rows": [{"source_line": 2, "archive_id": "000123", "reason": "OK"},
                                  {"source_line": 5, "archive_id": "BAD", "reason": "BAD_COLUMNS"}]}
# 前三个列名是对外契约；后续列承载行号区间、原文与归一值证据
FIELDS = ["source_line", "archive_id", "reason", "line_end", "raw_value", "normalized_value"]


def csv_text(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in FIELDS})
    return out.getvalue()


def run(payload):
    if "rows" in payload:
        rows = payload["rows"]
    elif "accepted" in payload or "review" in payload:
        # 归一后收下的档案 + 待复核行段，按物理行号归并导出
        rows = sorted([*payload.get("accepted", ()), *payload.get("review", ())],
                      key=lambda r: (r.get("source_line", 0), r.get("line_end", 0)))
    else:
        rows = SAMPLE["rows"]
    digest = canonical_digest(rows)
    rid = run_id(rows)
    result = {"input_count": len(rows),
              "valid_count": sum(r.get("reason") == "OK" for r in rows),
              "quarantine_count": sum(r.get("reason") != "OK" for r in rows)}
    store = payload.get("store")
    if store:
        rid = store.record(digest, rid, result)["run_id"]  # 同摘要重跑复用原 run_id，不重复收档
    return {"status": "READY", "run_id": rid, "digest": digest, "csv": csv_text(rows), **result, "reason": "OK"}
