import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.main import app
from app.db.database import Base, get_db

client = TestClient(app)


def _override_get_db_with_sqlite():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override


def _cleanup_uploaded(filename: str):
    created = f"data/raw_pdfs/{filename}"
    if os.path.exists(created):
        os.remove(created)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_gaps_returns_501_before_real_models_are_pasted_in():
    response = client.get("/gaps")
    assert response.status_code == 501


def test_upload_returns_501_while_pdf_cleaner_is_still_a_stub():
    pdf_bytes = b"%PDF-1.4 minimal"
    response = client.post(
        "/upload",
        files={"file": ("test_upload_scaffold.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 501
    assert "PDF cleaning not wired up yet" in response.json()["detail"]

    _cleanup_uploaded("test_upload_scaffold.pdf")


def test_upload_returns_zero_clauses_when_none_found():
    with patch("app.api.main.clean_pdf", return_value="   \n\n  "):
        response = client.post(
            "/upload",
            files={"file": ("empty.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["clauses_processed"] == 0
    assert body["results"] == []

    _cleanup_uploaded("empty.pdf")


def test_upload_processes_clauses_and_calls_supersession():
    fake_graph = MagicMock()
    fake_graph.invoke.side_effect = [
        {"diff_status": "new", "task": {"id": "task-1", "obligation_id": "obl-1", "due_date": None}},
        {"diff_status": "unchanged"},
    ]

    override_get_db = _override_get_db_with_sqlite()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch("app.api.main.clean_pdf", return_value="1. Do X.\n\n2. Do Y."),
            patch("app.api.main.build_graph", return_value=fake_graph),
            patch("app.api.main.mark_superseded_obligations", return_value=["obl-old"]) as mock_supersede,
        ):
            response = client.post(
                "/upload",
                files={"file": ("demo.pdf", b"%PDF-1.4", "application/pdf")},
            )
    finally:
        app.dependency_overrides.clear()
        _cleanup_uploaded("demo.pdf")

    assert response.status_code == 200
    body = response.json()
    assert body["circular_id"] == "demo"
    assert body["clauses_processed"] == 2
    assert body["results"][0] == {
        "clause_id": "clause-0",
        "status": "processed",
        "diff_status": "new",
        "task": {"id": "task-1", "obligation_id": "obl-1", "due_date": None},
    }
    assert body["results"][1]["status"] == "processed"
    assert body["superseded_obligation_ids"] == ["obl-old"]
    assert body["supersession_skipped_due_to_errors"] is False

    mock_supersede.assert_called_once()
    args, _ = mock_supersede.call_args
    assert args[1] == "demo"
    assert args[2] == {"obl-1"}

    fake_graph.invoke.assert_any_call(
        {
            "circular_id": "demo",
            "clause_id": "clause-0",
            "raw_clause": "1. Do X.",
            "heading": None,
        },
        config={"configurable": {"thread_id": "demo:clause-0"}},
    )


def test_upload_marks_pending_review_and_protects_its_obligation_from_supersession():
    class FakeInterrupt:
        def __init__(self, value):
            self.value = value

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "__interrupt__": [
            FakeInterrupt({
                "similarity_match": {"payload": {"obligation_id": "obl-2"}},
            })
        ]
    }

    override_get_db = _override_get_db_with_sqlite()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch("app.api.main.clean_pdf", return_value="1. Do X quarterly."),
            patch("app.api.main.build_graph", return_value=fake_graph),
            patch("app.api.main.mark_superseded_obligations", return_value=[]) as mock_supersede,
        ):
            response = client.post(
                "/upload",
                files={"file": ("amend.pdf", b"%PDF-1.4", "application/pdf")},
            )
    finally:
        app.dependency_overrides.clear()
        _cleanup_uploaded("amend.pdf")

    assert response.status_code == 200
    body = response.json()
    assert body["results"] == [{"clause_id": "clause-0", "status": "pending_review"}]

    mock_supersede.assert_called_once()
    args, _ = mock_supersede.call_args
    assert args[2] == {"obl-2"}


def test_upload_skips_supersession_when_a_clause_errors():
    fake_graph = MagicMock()
    fake_graph.invoke.side_effect = RuntimeError("groq is down")

    override_get_db = _override_get_db_with_sqlite()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch("app.api.main.clean_pdf", return_value="1. Do X."),
            patch("app.api.main.build_graph", return_value=fake_graph),
            patch("app.api.main.mark_superseded_obligations") as mock_supersede,
        ):
            response = client.post(
                "/upload",
                files={"file": ("broken.pdf", b"%PDF-1.4", "application/pdf")},
            )
    finally:
        app.dependency_overrides.clear()
        _cleanup_uploaded("broken.pdf")

    assert response.status_code == 200
    body = response.json()
    assert body["results"] == [
        {"clause_id": "clause-0", "status": "error", "detail": "groq is down"}
    ]
    assert body["supersession_skipped_due_to_errors"] is True
    assert body["superseded_obligation_ids"] == []
    mock_supersede.assert_not_called()
