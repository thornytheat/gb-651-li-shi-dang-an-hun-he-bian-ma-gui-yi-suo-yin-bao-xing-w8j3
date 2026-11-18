REASONS = {
    "BAD_COLUMNS": "字段数量不符", "EMPTY_VALUE": "必要值为空",
    "DUPLICATE_CONFLICT": "同一业务键取值冲突", "TRUNCATED": "尾记录不完整",
    "INVALID_VALUE": "值不符合定义", "STALE_VERSION": "提交版本已过期",
    "UNCLOSED_QUOTE": "引号未闭合，记录不完整",
    "QUOTE_MISUSE": "引号闭合后紧跟非法内容",
    "AMBIGUOUS_SPAN": "跨行段内疑似混入新档案，留待复核",
}

def reason(code: str) -> str:
    return REASONS.get(code, "未登记原因")
