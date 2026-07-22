import pytest

from app.ingestion.pdf_cleaner import clean_pdf
from app.graph.build_graph import build_graph
from app.graph.state import GraphState
import app.graph.nodes  # noqa: F401
from app.db.models import ObligationDB, EvidenceDB, AuditLogDB
from app.db.seed_synthetic import seed
from app.api.routes_review import router
from scripts.generate_synthetic_data import generate


def test_stub_functions_raise_not_implemented_when_called():
    with pytest.raises(NotImplementedError):
        clean_pdf("whatever.pdf")
    with pytest.raises(NotImplementedError):
        build_graph()
    with pytest.raises(NotImplementedError):
        seed()
    with pytest.raises(NotImplementedError):
        generate()


def test_stub_model_classes_raise_not_implemented_when_instantiated():
    with pytest.raises(NotImplementedError):
        ObligationDB()
    with pytest.raises(NotImplementedError):
        EvidenceDB()
    with pytest.raises(NotImplementedError):
        AuditLogDB()


def test_stub_state_and_router_are_importable_placeholders():
    assert issubclass(GraphState, dict)
    assert router is not None
