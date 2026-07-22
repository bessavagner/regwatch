from watches.grouping import (
    KIND_ENTITY,
    groups_from_terms,
    iter_terms,
    term_texts,
)


def test_all_mode_becomes_one_group_per_term():
    # "all" meant every term had to appear, which is AND. One group per term
    # reproduces that exactly, because groups are ANDed together.
    assert groups_from_terms(["sebrae", "contrato"], "all") == [
        {"terms": [{"text": "sebrae", "kind": KIND_ENTITY}]},
        {"terms": [{"text": "contrato", "kind": KIND_ENTITY}]},
    ]


def test_any_mode_becomes_a_single_group():
    assert groups_from_terms(["sebrae", "contrato"], "any") == [
        {"terms": [{"text": "sebrae", "kind": KIND_ENTITY},
                   {"text": "contrato", "kind": KIND_ENTITY}]},
    ]


def test_blank_and_non_string_terms_are_dropped():
    assert groups_from_terms(["  ", "sebrae", None, 7], "any") == [
        {"terms": [{"text": "sebrae", "kind": KIND_ENTITY}]},
    ]


def test_empty_terms_produce_no_groups():
    assert groups_from_terms([], "all") == []


def test_iter_terms_yields_text_and_kind():
    groups = [
        {"terms": [{"text": "sebrae", "kind": "entity"},
                   {"text": "contrato", "kind": "concept"}]},
    ]
    assert list(iter_terms(groups)) == [("sebrae", "entity"), ("contrato", "concept")]


def test_iter_terms_defaults_missing_kind_to_entity():
    assert list(iter_terms([{"terms": [{"text": "sebrae"}]}])) == [("sebrae", KIND_ENTITY)]


def test_iter_terms_tolerates_malformed_structures():
    assert list(iter_terms(None)) == []
    assert list(iter_terms([{}])) == []
    assert list(iter_terms([{"terms": None}])) == []
    assert list(iter_terms([{"terms": [{"text": "   "}]}])) == []


def test_term_texts_flattens_every_group():
    groups = [
        {"terms": [{"text": "sebrae", "kind": "entity"}]},
        {"terms": [{"text": "contrato", "kind": "concept"}]},
    ]
    assert term_texts(groups) == ["sebrae", "contrato"]
