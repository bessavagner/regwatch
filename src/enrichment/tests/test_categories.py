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
