def test_all_module_pages(client):
    for path in ['/intake', '/encoding', '/fields', '/content', '/reconcile', '/runs']:
        response = client.get(path)
        assert response.status_code == 200
        assert "panel" in response.text

def test_all_module_apis_and_idempotent_run(client):
    for path in ['/api/intake/run', '/api/encoding/detect', '/api/fields/normalize', '/api/content/normalize', '/api/reconcile']:
        response = client.post(path, json={})
        assert response.status_code == 200
    first = client.get("/api/runs").json()
    second = client.get("/api/runs").json()
    assert len(first["runs"]) == len(second["runs"]) == 1
    assert first == second

def test_pipeline_recovers_broken_quotes_and_rerun_is_idempotent(client):
    text = ('档号,盒号,题名\n'
            '000123,07,"年度汇编\n'
            '上册\n'
            '000124,08,会议记录\n'
            '000125,09,"年报\n'
            '000126,10,简报\n')
    intake = client.post("/api/intake/run", json={"text": text}).json()
    assert [r["档号"] for r in intake["rows"]] == ["000124", "000126"]
    assert intake["quarantine_count"] == 2

    content = client.post("/api/content/normalize", json={"records": intake["rows"]}).json()
    accepted = [{"source_line": r["source_line"], "line_end": r["line_end"],
                 "archive_id": r["档号"], "reason": "OK", "normalized_value": r["题名"]}
                for r in content["records"]]
    review = [{"source_line": q["source_line"], "line_end": q["line_end"], "archive_id": "",
               "reason": q["reason"], "raw_value": q["raw"]} for q in intake["quarantine"]]

    first = client.post("/api/export/run", json={"accepted": accepted, "review": review}).json()
    second = client.post("/api/export/run", json={"accepted": accepted, "review": review}).json()
    assert first["run_id"] == second["run_id"]
    assert (first["input_count"], first["valid_count"], first["quarantine_count"]) == (4, 2, 2)
    assert "UNCLOSED_QUOTE" in first["csv"] and "000124" in first["csv"]

    runs = client.get("/api/runs").json()["runs"]
    assert len([r for r in runs if r["run_id"] == first["run_id"]]) == 1
