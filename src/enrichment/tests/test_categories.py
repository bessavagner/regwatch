import re

from enrichment.anthropic_client import CATEGORIES as REEXPORTED
from enrichment.anthropic_client import SYSTEM_PROMPT
from enrichment.categories import CATEGORIES, CATEGORY_LABELS, label_for


def test_the_vocabulary_is_the_six_categories_the_enricher_writes():
    assert set(CATEGORY_LABELS) == {
        "tender", "grant", "appointment", "penalty", "regulation", "other",
    }


def test_every_label_is_portuguese():
    assert list(CATEGORY_LABELS.values()) == [
        "licitação", "fomento", "pessoal", "sanção", "norma", "outro",
    ]


def test_categories_is_the_keys_of_the_labels():
    assert CATEGORIES == frozenset(CATEGORY_LABELS)


def test_anthropic_client_still_exports_categories_for_openai_client():
    # src/enrichment/openai_client.py imports CATEGORIES from anthropic_client.
    assert REEXPORTED == CATEGORIES


def test_label_for_translates_a_known_value():
    assert label_for("regulation") == "norma"


def test_label_for_names_the_unenriched_case_rather_than_calling_it_outro():
    # An unenriched match carries "". That is the absence of a category, not
    # the "other" category -- saying "outro" would claim the enricher looked.
    assert label_for("") == "sem categoria"


def test_label_for_passes_an_unknown_value_through_unchanged():
    # Both LLM clients coerce an unrecognised reply to "other" before it is
    # stored, so this is a can't-happen. Surfacing the raw value makes a data
    # bug visible instead of disguising it as a real category.
    assert label_for("bogus") == "bogus"


def test_the_prompt_names_every_category_and_no_others():
    listed = re.search(r"um de: ([^)]+)\)", SYSTEM_PROMPT).group(1)
    assert {c.strip() for c in listed.split(",")} == set(CATEGORY_LABELS)
