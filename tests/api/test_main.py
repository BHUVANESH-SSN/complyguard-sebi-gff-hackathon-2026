import os

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_gaps_returns_501_before_real_models_are_pasted_in():
    response = client.get("/gaps")
    assert response.status_code == 501


def test_upload_returns_501_before_graph_is_pasted_in():
    pdf_bytes = b"%PDF-1.4 minimal"
    response = client.post(
        "/upload",
        files={"file": ("test_upload_scaffold.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 501

    created = "data/raw_pdfs/test_upload_scaffold.pdf"
    if os.path.exists(created):
        os.remove(created)
