"""M1 文件采信：逐行引号状态机扫描移交表。

题名可跨行（引号内换行属同一记录）；一处引号破损只隔离最小行段，
可确认的后续记录照常采信，拿不准的行段保留原文与物理行号区间留作复核。
"""
SAMPLE = {"text": "档号,盒号,题名\n000123,07,年度 汇编\n档号,盒号,题名\n9007199254740993,08,会议\nBAD,09\n"}


class ScanError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _split_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # 结尾换行是终止符，不是一条空记录
    return lines


def _parse_record(lines: list[str], i: int):
    """从物理行 i（0 基）解析一条 CSV 记录，返回 (fields, 末行下标)。

    严格校验：闭合引号后只允许分隔符或行尾，否则 QUOTE_MISUSE；
    引号内到达文件末尾则 UNCLOSED_QUOTE。
    """
    fields, buf = [], []
    in_quotes = False
    closed = False  # 闭合引号已出现，之后只接受逗号或行尾
    j = i
    while True:
        line = lines[j]
        if line.endswith("\r"):
            line = line[:-1]
        k, n = 0, len(line)
        while k < n:
            ch = line[k]
            if in_quotes:
                if ch == '"':
                    if k + 1 < n and line[k + 1] == '"':
                        buf.append('"')
                        k += 2
                        continue
                    in_quotes = False
                    closed = True
                    k += 1
                    continue
                buf.append(ch)
                k += 1
                continue
            if closed:
                if ch == ",":
                    fields.append("".join(buf))
                    buf = []
                    closed = False
                    k += 1
                    continue
                raise ScanError("QUOTE_MISUSE")
            if ch == ",":
                fields.append("".join(buf))
                buf = []
                k += 1
                continue
            if ch == '"' and not buf:
                in_quotes = True
                k += 1
                continue
            buf.append(ch)
            k += 1
        if in_quotes:
            buf.append("\n")
            j += 1
            if j >= len(lines):
                raise ScanError("UNCLOSED_QUOTE")
            continue
        fields.append("".join(buf))
        return fields, j


def _looks_like_record(lines: list[str], i: int, width: int) -> bool:
    """该行单独看是否像一条完整记录（续行形似新档案的判据）。"""
    try:
        fields, end = _parse_record(lines, i)
    except ScanError:
        return False
    return end == i and len(fields) == width


def _confirmable(lines: list[str], i: int, header) -> bool:
    """从该行起能否确认出一条无歧义的记录（重同步点判据）。"""
    try:
        fields, end = _parse_record(lines, i)
    except ScanError:
        return False
    if header is None:
        return True
    if len(fields) != len(header):
        return False
    return not any(_looks_like_record(lines, k, len(header)) for k in range(i + 1, end + 1))


def scan(text: str):
    lines = _split_lines(text)
    rows, quarantine, empty = [], [], 0
    header = None
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() == "":
            empty += 1
            i += 1
            continue
        try:
            fields, end = _parse_record(lines, i)
        except ScanError as err:
            # 破损记录：隔离最小行段，从下一个可确认记录处恢复
            k = i + 1
            while k < n and not _confirmable(lines, k, header):
                k += 1
            quarantine.append({"source_line": i + 1, "line_end": k, "reason": err.reason,
                               "raw": "\n".join(lines[i:k])})
            i = k
            continue
        if not any(x.strip() for x in fields):
            empty += 1
            i = end + 1
            continue
        if header is None:
            header = [x.lstrip("\ufeff") for x in fields]
            i = end + 1
            continue
        if [x.lstrip("\ufeff") for x in fields] == header:
            i = end + 1
            continue
        if len(fields) != len(header):
            quarantine.append({"source_line": i + 1, "line_end": end + 1, "reason": "BAD_COLUMNS",
                               "raw": "\n".join(lines[i:end + 1])})
            i = end + 1
            continue
        if end > i and any(_looks_like_record(lines, k, len(header)) for k in range(i + 1, end + 1)):
            # 跨行段内混有形似新档案的行：无法判定是题名续行还是被吞记录，整段留复核
            quarantine.append({"source_line": i + 1, "line_end": end + 1, "reason": "AMBIGUOUS_SPAN",
                               "raw": "\n".join(lines[i:end + 1])})
            i = end + 1
            continue
        rows.append(dict(zip(header, fields)) | {"source_line": i + 1, "line_end": end + 1})
        i = end + 1
    return {"rows": rows, "quarantine": quarantine, "empty": empty, "header": header}


def run(payload):
    out = scan(payload.get("text", SAMPLE["text"]))
    return {"status": "READY",
            "input_count": len(out["rows"]) + len(out["quarantine"]) + out["empty"],
            "valid_count": len(out["rows"]),
            "quarantine_count": len(out["quarantine"]),
            "empty_count": out["empty"],
            "header": out["header"],
            "rows": out["rows"],
            "quarantine": out["quarantine"],
            "reason": out["quarantine"][0]["reason"] if out["quarantine"] else "OK"}
