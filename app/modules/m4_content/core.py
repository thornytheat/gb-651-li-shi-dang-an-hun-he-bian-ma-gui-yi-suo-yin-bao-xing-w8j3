import re, unicodedata
SAMPLE = {"values": ["年度　 汇编\r\n上册", "ＡＢＣ－００１", "馆藏\t目录"]}
# 档号、盒号等编号字段逐字保留，不参与内容归一；source_line/line_end 为结构证据
PRESERVE_FIELDS = ("档号", "盒号", "source_line", "line_end")


def normalize(value: str):
    value = unicodedata.normalize("NFKC", value).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in value.split("\n"))


def evidence(value):
    new = normalize(value)
    return {"raw": value, "normalized": new, "changed": new != value}


def normalize_record(row: dict):
    """接收采信确认的整条档案：内容字段归一，编号与行号逐字保留。"""
    out, changed = {}, False
    for key, value in row.items():
        if key in PRESERVE_FIELDS:
            out[key] = value
            continue
        new = normalize(str(value))
        out[key] = new
        changed = changed or new != value
    out["changed"] = changed
    return out


def run(payload):
    if "records" in payload:
        records = [normalize_record(row) for row in payload["records"]]
        return {"status": "READY", "input_count": len(records), "valid_count": len(records),
                "quarantine_count": 0, "changed": sum(r["changed"] for r in records),
                "records": records, "reason": "OK"}
    values = payload.get("values", SAMPLE["values"])
    rows = [evidence(v) for v in values]
    return {"status": "READY", "input_count": len(rows), "valid_count": len(rows),
            "quarantine_count": 0, "changed": sum(r["changed"] for r in rows),
            "values": [r["normalized"] for r in rows], "reason": "OK"}
