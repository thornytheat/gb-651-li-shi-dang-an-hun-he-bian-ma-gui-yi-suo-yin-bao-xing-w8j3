from app.modules.m6_runs.core import SAMPLE, csv_text, run
class FakeStore:
    def __init__(self): self.values={}
    def record(self,digest,rid,result): self.values.setdefault(digest,(rid,result)); return {"run_id":self.values[digest][0],"result":self.values[digest][1]}
def test_csv_header(): assert csv_text(SAMPLE["rows"]).startswith("source_line,archive_id,reason")
def test_csv_preserves_zero(): assert "000123" in csv_text(SAMPLE["rows"])
def test_run_id_stable(): assert run({})["run_id"]==run({})["run_id"]
def test_digest_stable(): assert run({})["digest"]==run({})["digest"]
def test_trap_1(): # TRAP-07
    store=FakeStore(); assert run({"store":store})["run_id"]==run({"store":store})["run_id"]
def test_trap_2():
    assert run({"rows":SAMPLE["rows"]})["input_count"]==2
def test_counts_quarantine(): assert run({})["quarantine_count"]==1
def test_counts_valid(): assert run({})["valid_count"]==1

def test_csv_carries_review_segment_evidence():
    rows = [{"source_line": 2, "line_end": 3, "archive_id": "", "reason": "UNCLOSED_QUOTE",
             "raw_value": '000123,07,"年度汇编\n上册'}]
    text = csv_text(rows)
    assert "\n2,,UNCLOSED_QUOTE,3," in text
    assert "年度汇编" in text

def test_accepted_and_review_merge_in_line_order():
    accepted = [{"source_line": 4, "archive_id": "000124", "reason": "OK", "normalized_value": "会议记录"}]
    review = [{"source_line": 2, "line_end": 3, "archive_id": "", "reason": "QUOTE_MISUSE", "raw_value": "x"}]
    out = run({"accepted": accepted, "review": review})
    assert (out["input_count"], out["valid_count"], out["quarantine_count"]) == (2, 1, 1)
    assert out["csv"].index("QUOTE_MISUSE") < out["csv"].index("000124")

def test_same_batch_rerun_does_not_duplicate():
    store = FakeStore()
    payload = {"store": store, "accepted": [{"source_line": 4, "archive_id": "000124", "reason": "OK"}],
               "review": [{"source_line": 2, "reason": "UNCLOSED_QUOTE", "raw_value": "x"}]}
    first, second = run(payload), run(dict(payload))
    assert first["run_id"] == second["run_id"] and len(store.values) == 1
