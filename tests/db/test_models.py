from sqlalchemy import create_engine, inspect

from app.db.database import Base as DatabaseBase
from app.db.models import AuditTrail, EvidenceLog, Obligation, Task


def test_models_share_the_database_base():
    assert Obligation.metadata is DatabaseBase.metadata


def test_all_tables_registered_on_shared_metadata():
    table_names = set(DatabaseBase.metadata.tables.keys())
    assert {"obligations", "tasks", "evidence_log", "audit_trail"} <= table_names


def test_create_all_tables_against_sqlite():
    engine = create_engine("sqlite:///:memory:")
    DatabaseBase.metadata.create_all(engine)
    with engine.connect() as conn:
        inspector = inspect(conn)
        assert set(inspector.get_table_names()) >= {
            "obligations", "tasks", "evidence_log", "audit_trail",
        }
