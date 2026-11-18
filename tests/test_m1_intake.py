from app.modules.m1_intake.core import SAMPLE, scan, run
def test_trap_1(): # TRAP-01, TRAP-08
    assert scan("\ufeff档号,盒号\n0001,01\n")["header"]==["档号","盒号"]
def test_trap_2():
    assert len(scan("a,b\na,b\n1,2\n")["rows"])==1
def test_ragged_is_quarantined(): assert scan("a,b\n1\n")["quarantine"][0]["reason"]=="BAD_COLUMNS"
def test_blank_is_counted(): assert scan("a,b\n\n1,2\n")["empty"]==1
def test_source_line_survives(): assert scan("a,b\n1,2\n")["rows"][0]["source_line"]==2
def test_quoted_newline_is_one_record(): assert len(scan('a,b\n1,"x\ny"\n')["rows"])==1
def test_sample_has_conflict(): assert run(SAMPLE)["quarantine_count"]==1
def test_input_accounting():
    out=run(SAMPLE); assert out["input_count"]==out["valid_count"]+out["quarantine_count"]

BROKEN = ('档号,盒号,题名\n'
          '000123,07,"年度汇编\n'
          '上册\n'
          '000124,08,会议记录\n'
          '000125,09,"年报\n'
          '000126,10,简报\n')

def test_multiline_title_kept_whole():
    out = scan('档号,盒号,题名\n000123,07,"年度汇编\n上册"\n000124,08,会议\n')
    assert [r["题名"] for r in out["rows"]] == ["年度汇编\n上册", "会议"]
    assert (out["rows"][0]["source_line"], out["rows"][0]["line_end"]) == (2, 3)

def test_unclosed_quote_does_not_swallow_following_records():
    out = scan(BROKEN)
    assert [r["档号"] for r in out["rows"]] == ["000124", "000126"]
    assert len(out["quarantine"]) == 2

def test_broken_segment_keeps_raw_and_line_span():
    out = scan(BROKEN)
    first, second = out["quarantine"]
    assert first["reason"] == "QUOTE_MISUSE"
    assert (first["source_line"], first["line_end"]) == (2, 3)
    assert first["raw"] == '000123,07,"年度汇编\n上册'
    assert second["reason"] == "UNCLOSED_QUOTE"
    assert (second["source_line"], second["line_end"]) == (5, 5)
    assert second["raw"] == '000125,09,"年报'

def test_unclosed_quote_at_eof_quarantines_tail():
    out = scan('a,b\n1,2\n3,"x\n')
    assert [r["a"] for r in out["rows"]] == ["1"]
    assert out["quarantine"][0]["reason"] == "UNCLOSED_QUOTE"
    assert (out["quarantine"][0]["source_line"], out["quarantine"][0]["line_end"]) == (3, 3)

def test_continuation_looking_like_record_is_ambiguous():
    out = scan('档号,盒号,题名\n000123,07,"年度汇编\n000124,08,会议记录"\n000125,09,年报\n')
    assert [r["档号"] for r in out["rows"]] == ["000125"]
    assert out["quarantine"][0]["reason"] == "AMBIGUOUS_SPAN"
    assert (out["quarantine"][0]["source_line"], out["quarantine"][0]["line_end"]) == (2, 3)

def test_recovery_accounting_balances():
    out = run({"text": BROKEN})
    assert out["input_count"] == out["valid_count"] + out["quarantine_count"] + out["empty_count"]
    assert (out["valid_count"], out["quarantine_count"]) == (2, 2)
