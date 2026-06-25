from app import persistence


def test_sqlite_snapshot_and_audit_round_trip(monkeypatch, tmp_path):
    db_file = tmp_path / "crm.sqlite"
    payload = {"cus-test": {"id": "cus-test", "name": "Test Customer"}}

    monkeypatch.setenv("CRM_STORAGE", "sqlite")
    monkeypatch.setenv("CRM_SQLITE_PATH", str(db_file))

    persistence.save_customers(payload)
    persistence.append_audit("case_created", {"case_id": "case-999"})

    assert persistence.load_customers() == payload
    assert db_file.exists()
