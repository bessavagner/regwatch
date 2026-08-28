from collections import Counter

from enrichment.report import (
    Cluster,
    cluster_key,
    cluster_summaries,
    histogram,
    inconsistency_rate,
    modal_share,
)


def test_cluster_key_folds_case_and_accents():
    # normalize_text lowercases, NFKD-decomposes and strips combining marks, so
    # these two openings are the same act type written twice.
    assert cluster_key("Anuiu previamente à celebração de contrato com a União") == cluster_key(
        "anuiu previamente a celebracao de contrato com o Estado"
    )


def test_cluster_key_keeps_only_the_opening_words():
    assert cluster_key("um dois tres quatro cinco seis sete oito") == "um dois tres quatro cinco seis"


def test_cluster_key_of_an_empty_summary_is_empty():
    assert cluster_key("") == ""


def test_cluster_summaries_groups_by_opening_and_drops_small_groups():
    rows = [
        ("Declarou de utilidade publica a entidade A", "regulation"),
        ("Declarou de utilidade publica a entidade B", "regulation"),
        ("Declarou de utilidade publica a entidade C", "other"),
        ("Nomeou fulano para o cargo", "appointment"),
    ]
    clusters = cluster_summaries(rows, min_size=3)
    assert len(clusters) == 1
    assert clusters[0].size == 3
    assert clusters[0].categories == Counter({"regulation": 2, "other": 1})
    assert clusters[0].single_valued is False


def test_cluster_summaries_orders_largest_first():
    rows = [("aaa bbb", "grant")] * 3 + [("ccc ddd", "tender")] * 5
    clusters = cluster_summaries(rows, min_size=3)
    assert [c.size for c in clusters] == [5, 3]


def test_inconsistency_rate_is_the_share_sitting_in_a_split_cluster():
    split = Cluster("a", Counter({"regulation": 12, "other": 5}))
    clean = Cluster("b", Counter({"tender": 3}))
    assert inconsistency_rate([split, clean]) == 17 / 20


def test_inconsistency_rate_of_nothing_is_zero():
    assert inconsistency_rate([]) == 0.0


def test_modal_share_is_one_when_every_value_is_the_same():
    assert modal_share(histogram([0.99, 0.99, 0.99])) == 1.0


def test_modal_share_reports_real_spread():
    assert modal_share(histogram([0, 1, 1, 2])) == 0.5


def test_modal_share_of_nothing_is_zero():
    assert modal_share({}) == 0.0
