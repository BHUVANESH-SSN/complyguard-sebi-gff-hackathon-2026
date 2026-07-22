from app.ingestion.clause_splitter import split_into_clauses


def test_splits_top_level_numbered_clauses():
    text = "1. Appoint a compliance officer.\n\n2. File a cyber security policy."
    assert split_into_clauses(text) == [
        "1. Appoint a compliance officer.",
        "2. File a cyber security policy.",
    ]


def test_keeps_sub_clauses_separate_when_separately_numbered():
    text = "1. Do X.\n1.1 Sub-requirement A.\n1.2 Sub-requirement B.\n2. Do Y."
    assert split_into_clauses(text) == [
        "1. Do X.",
        "1.1 Sub-requirement A.",
        "1.2 Sub-requirement B.",
        "2. Do Y.",
    ]


def test_falls_back_to_paragraph_split_when_no_numbering():
    text = "Intro paragraph with no numbers.\n\nSecond paragraph, still no numbers."
    assert split_into_clauses(text) == [
        "Intro paragraph with no numbers.",
        "Second paragraph, still no numbers.",
    ]


def test_empty_text_returns_empty_list():
    assert split_into_clauses("") == []
    assert split_into_clauses("   \n\n  ") == []
