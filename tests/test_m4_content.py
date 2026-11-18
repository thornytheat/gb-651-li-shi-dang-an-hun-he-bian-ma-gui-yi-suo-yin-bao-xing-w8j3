from app.modules.m4_content.core import normalize, evidence, run
def test_trap_1(): # TRAP-04, TRAP-18
    assert normalize("ＡＢＣ－００１")=="ABC-001"
def test_trap_2(): assert normalize("甲\r\n乙")=="甲\n乙"
def test_tabs_collapse(): assert normalize("甲\t 乙")=="甲 乙"
def test_line_spaces_trim(): assert normalize(" 甲 \n 乙 ")=="甲\n乙"
def test_evidence_keeps_raw(): assert evidence("Ａ")["raw"]=="Ａ"
def test_evidence_marks_change(): assert evidence("Ａ")["changed"] is True
def test_stable_second_pass(): assert normalize(normalize("Ａ　Ｂ"))=="A B"
def test_run_counts_changed(): assert run({})["changed"]==3

def test_run_accepts_whole_confirmed_records():
    records = [{"档号": "000123", "盒号": "07", "题名": "年度　 汇编\r\n上册", "source_line": 2, "line_end": 3}]
    out = run({"records": records})
    assert out["valid_count"] == 1 and out["changed"] == 1
    row = out["records"][0]
    assert row["题名"] == "年度 汇编\n上册"
    assert (row["source_line"], row["line_end"]) == (2, 3)

def test_record_mode_preserves_identifiers_verbatim():
    records = [{"档号": "０００１２３", "盒号": "０７", "题名": "ＡＢＣ", "source_line": 2, "line_end": 2}]
    row = run({"records": records})["records"][0]
    assert row["档号"] == "０００１２３" and row["盒号"] == "０７"
    assert row["题名"] == "ABC"
