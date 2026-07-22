"""Placeholder for seeding Postgres with synthetic compliance data
(6 obligations, 143 tasks, 129 evidence rows, 25 grievances, org roles).

Real implementation is pasted in separately. Once ready, run:
    python -m app.db.seed_synthetic
"""


def seed() -> None:
    raise NotImplementedError(
        "app.db.seed_synthetic.seed is a placeholder — paste the real "
        "synthetic-data seeding implementation here."
    )


if __name__ == "__main__":
    seed()
