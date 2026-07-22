"""Placeholder ORM + schema definitions.

Real content (Obligation, Evidence, AuditLog, Task, Grievance, OrgRole
models — SQLAlchemy tables + Pydantic schemas) is pasted in separately.
Importing this module must never fail; using these placeholder classes
for real queries raises NotImplementedError.
"""


class _Unbuilt:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            f"{type(self).__name__} is a placeholder — paste the real "
            "SQLAlchemy/Pydantic model here."
        )


class ObligationDB(_Unbuilt):
    pass


class EvidenceDB(_Unbuilt):
    pass


class AuditLogDB(_Unbuilt):
    pass
