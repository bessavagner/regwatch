import datetime
import itertools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from gazette.models import Act, Edition
from matching.models import Match
from watches.models import Client as WatchClient
from watches.models import Watch

User = get_user_model()
_seq = itertools.count()


def _member(name, email):
    ws = Workspace.objects.create(name=name)
    user = User.objects.create_user(username=email, email=email, password="pw12345")
    Membership.objects.create(workspace=ws, user=user)
    return ws, user


def _match(ws, *, section="1", date, category="", state="new", rank=0.0):
    n = next(_seq)
    client = WatchClient.objects.create(workspace=ws, name="C")
    watch = Watch.objects.create(client=client, groups=[{"terms": [{"text": "x", "kind": "entity"}]}])
    edition, _ = Edition.objects.get_or_create(
        date=date, section=section, defaults={"source_url": "https://e.test"}
    )
    act = Act.objects.create(
        edition=edition, identifier=f"id-{n}",
        title="t", raw_text="r", search_text="s",
    )
    return Match.objects.create(watch=watch, act=act, category=category, state=state, rank=rank)


@pytest.fixture
def firm_a(db):
    return _member("Firm A", "a@firm.com")


@pytest.fixture
def firm_b(db):
    return _member("Firm B", "b@firm.com")


@pytest.mark.django_db
def test_feed_lists_only_own_workspace(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    _match(ws_a, date=datetime.date(2026, 7, 1))
    _match(ws_b, date=datetime.date(2026, 7, 1))
    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.get("/api/matches")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_feed_filters_by_state(firm_a):
    ws, user = firm_a
    _match(ws, date=datetime.date(2026, 7, 1), state="new")
    _match(ws, date=datetime.date(2026, 7, 2), state="dismissed", rank=1.0)
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.get("/api/matches?state=new")
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["state"] == "new"


@pytest.mark.django_db
def test_feed_default_order_is_recency(firm_a):
    ws, user = firm_a
    old = _match(ws, date=datetime.date(2026, 7, 1))
    new = _match(ws, date=datetime.date(2026, 7, 2), rank=1.0)
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.get("/api/matches")
    assert resp.data["results"][0]["id"] == new.id  # newest created first


@pytest.mark.django_db
def test_mark_relevant_transitions_state(firm_a):
    ws, user = firm_a
    m = _match(ws, date=datetime.date(2026, 7, 1), state="new")
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(f"/api/matches/{m.id}/relevant")
    assert resp.status_code == 200
    m.refresh_from_db()
    assert m.state == "relevant"


@pytest.mark.django_db
def test_dismiss_transitions_state(firm_a):
    ws, user = firm_a
    m = _match(ws, date=datetime.date(2026, 7, 1), state="new")
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(f"/api/matches/{m.id}/dismiss")
    assert resp.status_code == 200
    m.refresh_from_db()
    assert m.state == "dismissed"


@pytest.mark.django_db
def test_cannot_triage_other_workspace_match(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    m_b = _match(ws_b, date=datetime.date(2026, 7, 1), state="new")
    api = APIClient()
    api.force_authenticate(user=user_a)
    assert api.post(f"/api/matches/{m_b.id}/relevant").status_code == 404
    m_b.refresh_from_db()
    assert m_b.state == "new"


@pytest.mark.django_db
def test_match_payload_identifies_the_act(firm_a):
    ws, user = firm_a
    match = _match(ws, date=datetime.date(2026, 7, 1))
    api = APIClient()
    api.force_authenticate(user=user)

    resp = api.get("/api/matches")
    assert resp.status_code == 200
    row = resp.data["results"][0]

    detail = row["act_detail"]
    assert detail["title"] == "t"
    assert detail["identifier"] == match.act.identifier
    assert detail["date"] == "2026-07-01"
    assert detail["section"] == "1"
    assert detail["source_url"] == "https://e.test"
    # The bare id stays, so nothing that already consumes it breaks.
    assert row["act"] == match.act_id


@pytest.mark.django_db
def test_match_payload_names_the_client(firm_a):
    ws, user = firm_a
    match = _match(ws, date=datetime.date(2026, 7, 1))
    api = APIClient()
    api.force_authenticate(user=user)

    row = api.get("/api/matches").data["results"][0]
    assert row["client_id"] == match.watch.client_id
    assert row["client_name"] == "C"


@pytest.mark.django_db
def test_match_list_does_not_issue_a_query_per_row(firm_a, django_assert_max_num_queries):
    ws, user = firm_a
    for _ in range(25):
        _match(ws, date=datetime.date(2026, 7, 1))
    api = APIClient()
    api.force_authenticate(user=user)

    # 25 rows must not cost 25 act lookups plus 25 client lookups.
    with django_assert_max_num_queries(8):
        api.get("/api/matches")


@pytest.mark.django_db
def test_match_payload_carries_the_portuguese_category_label(firm_a):
    ws, user = firm_a
    _match(ws, date=datetime.date(2026, 8, 26), category="regulation")
    api = APIClient()
    api.force_authenticate(user)
    row = api.get("/api/matches").json()["results"][0]
    assert row["category"] == "regulation"     # storage enum, unchanged
    assert row["category_label"] == "norma"


@pytest.mark.django_db
def test_an_unenriched_match_is_labelled_rather_than_left_blank(firm_a):
    ws, user = firm_a
    _match(ws, date=datetime.date(2026, 8, 26), category="")
    api = APIClient()
    api.force_authenticate(user)
    row = api.get("/api/matches").json()["results"][0]
    assert row["category_label"] == "sem categoria"


@pytest.mark.django_db
def test_the_match_list_reports_its_page_size_page_and_total(firm_a):
    ws, user = firm_a
    for _ in range(26):                      # PAGE_SIZE is 25, so this is two pages
        _match(ws, date=datetime.date(2026, 8, 26))
    api = APIClient()
    api.force_authenticate(user)
    body = api.get("/api/matches").json()
    assert body["count"] == 26
    assert body["page"] == 1
    assert body["total_pages"] == 2
    assert body["page_size"] == 25
    assert len(body["results"]) == 25


@pytest.mark.django_db
def test_page_two_says_it_is_page_two(firm_a):
    ws, user = firm_a
    for _ in range(26):
        _match(ws, date=datetime.date(2026, 8, 26))
    api = APIClient()
    api.force_authenticate(user)
    body = api.get("/api/matches?page=2").json()
    assert body["page"] == 2
    assert body["total_pages"] == 2
    assert len(body["results"]) == 1


@pytest.mark.django_db
def test_an_empty_list_is_one_page_not_zero(firm_a):
    # Django's Paginator counts an empty first page as a page (num_pages is 1
    # when count is 0). The feed therefore renders "Page 1 of 1", never "of 0".
    ws, user = firm_a
    api = APIClient()
    api.force_authenticate(user)
    body = api.get("/api/matches").json()
    assert body["count"] == 0
    assert body["total_pages"] == 1


@pytest.mark.django_db
def test_the_other_list_endpoints_report_the_same_fields(firm_a):
    # DEFAULT_PAGINATION_CLASS is global: one pagination contract, not a
    # special case for matches.
    ws, user = firm_a
    api = APIClient()
    api.force_authenticate(user)
    body = api.get("/api/clients").json()
    assert body["page"] == 1
    assert body["total_pages"] == 1
    assert body["page_size"] == 25


@pytest.mark.django_db
def test_match_payload_carries_the_matched_terms(firm_a):
    ws, user = firm_a
    match = _match(ws, date=datetime.date(2026, 7, 1))
    match.matched_terms = ["saneamento"]
    match.save(update_fields=["matched_terms"])
    api = APIClient()
    api.force_authenticate(user)
    body = api.get("/api/matches").json()
    assert body["results"][0]["matched_terms"] == ["saneamento"]


def _scored(ws, *, date, rank, score, names_party=False):
    # _match() predates the signal columns; set them after creation rather than
    # widening a helper a dozen other tests already call.
    match = _match(ws, date=date, rank=rank)
    match.signal_score = score
    match.names_party = names_party
    match.save(update_fields=["signal_score", "names_party"])
    return match


@pytest.fixture
def signal_feed(firm_a):
    ws, user = firm_a
    day = datetime.date(2026, 8, 27)
    _scored(ws, date=day, rank=2.0, score=3, names_party=True)
    _scored(ws, date=day, rank=8.0, score=3, names_party=True)
    _scored(ws, date=day, rank=9.0, score=1)
    _scored(ws, date=day, rank=4.0, score=0)
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_ordering_by_signal_puts_the_richest_act_first(signal_feed):
    rows = signal_feed.get("/api/matches?ordering=signal").data["results"]
    scores = [row["signal_score"] for row in rows]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 3


@pytest.mark.django_db
def test_ordering_by_signal_falls_back_to_rank_within_a_score(signal_feed):
    rows = signal_feed.get("/api/matches?ordering=signal").data["results"]
    tied = [r for r in rows if r["signal_score"] == rows[0]["signal_score"]]
    assert len(tied) == 2
    ranks = [r["rank"] for r in tied]
    assert ranks == sorted(ranks, reverse=True)


@pytest.mark.django_db
def test_the_serializer_carries_the_signals(signal_feed):
    row = signal_feed.get("/api/matches").data["results"][0]
    for key in ("names_party", "has_amount", "has_deadline", "signal_score"):
        assert key in row


@pytest.fixture
def triaged_feed(firm_a):
    ws, user = firm_a
    day = datetime.date(2026, 8, 27)
    _match(ws, date=day, state="new")
    _match(ws, date=day, state="relevant")
    _match(ws, date=day, state="dismissed")
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_the_feed_hides_dismissed_matches_by_default(triaged_feed):
    # Dismissing has to visibly shrink the pile, or triage is unpaid work: the
    # default view returns what still needs a decision plus what was kept.
    rows = triaged_feed.get("/api/matches").data["results"]
    assert {r["state"] for r in rows} == {"new", "relevant"}


@pytest.mark.django_db
def test_the_count_excludes_dismissed_too(triaged_feed):
    # count drives the header and the dial; if it still counted dismissed rows
    # the number would never fall and triage would look ineffective.
    assert triaged_feed.get("/api/matches").data["count"] == 2


@pytest.mark.django_db
def test_dismissed_matches_are_still_reachable_by_asking_for_them(triaged_feed):
    # Hidden by default is not deleted: the state filter still reaches them.
    rows = triaged_feed.get("/api/matches?state=dismissed").data["results"]
    assert [r["state"] for r in rows] == ["dismissed"]


@pytest.mark.django_db
def test_an_explicit_state_filter_is_unaffected(triaged_feed):
    rows = triaged_feed.get("/api/matches?state=new").data["results"]
    assert [r["state"] for r in rows] == ["new"]


# --- Bulk dismiss (TASK-024 / D7) -------------------------------------------
#
# The most damaging thing in the feed: a mutation over many rows at once. The
# scoping is tested before the ergonomics, deliberately.

def _match_with_agency(ws, agency, *, date=datetime.date(2026, 7, 1), state="new"):
    match = _match(ws, date=date, state=state)
    match.act.agency = agency
    match.act.save(update_fields=["agency"])
    return match


def _api(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_bulk_dismiss_takes_an_explicit_id_list_and_reports_the_count(firm_a):
    ws, user = firm_a
    a = _match_with_agency(ws, "Ministério da Saúde")
    b = _match_with_agency(ws, "Ministério da Saúde")
    untouched = _match_with_agency(ws, "Ministério da Saúde")

    resp = _api(user).post("/api/matches/bulk_dismiss", {"ids": [a.id, b.id]}, format="json")

    assert resp.status_code == 200
    assert resp.data["dismissed"] == 2
    a.refresh_from_db(); b.refresh_from_db(); untouched.refresh_from_db()
    assert a.state == "dismissed" and b.state == "dismissed"
    assert untouched.state == "new"


@pytest.mark.django_db
def test_bulk_dismiss_refuses_to_cross_a_workspace_boundary(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    mine = _match_with_agency(ws_a, "Org")
    theirs = _match_with_agency(ws_b, "Org")

    resp = _api(user_a).post(
        "/api/matches/bulk_dismiss", {"ids": [mine.id, theirs.id]}, format="json")

    # All-or-nothing: a partial apply would report a number the caller cannot
    # act on, and would leak the existence of the other workspace's row.
    assert resp.status_code == 404
    mine.refresh_from_db(); theirs.refresh_from_db()
    assert mine.state == "new"
    assert theirs.state == "new"


@pytest.mark.django_db
def test_bulk_dismiss_by_agency_only_touches_that_agency(firm_a):
    ws, user = firm_a
    hit_a = _match_with_agency(ws, "Ministério da Saúde")
    hit_b = _match_with_agency(ws, "Ministério da Saúde")
    other = _match_with_agency(ws, "Ministério da Educação")

    resp = _api(user).post(
        "/api/matches/bulk_dismiss", {"agency": "Ministério da Saúde"}, format="json")

    assert resp.status_code == 200
    assert resp.data["dismissed"] == 2
    hit_a.refresh_from_db(); hit_b.refresh_from_db(); other.refresh_from_db()
    assert hit_a.state == "dismissed" and hit_b.state == "dismissed"
    assert other.state == "new"


@pytest.mark.django_db
def test_bulk_dismiss_by_agency_stays_inside_the_workspace(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    mine = _match_with_agency(ws_a, "Org")
    theirs = _match_with_agency(ws_b, "Org")

    resp = _api(user_a).post("/api/matches/bulk_dismiss", {"agency": "Org"}, format="json")

    assert resp.data["dismissed"] == 1
    theirs.refresh_from_db()
    assert theirs.state == "new"
    mine.refresh_from_db()
    assert mine.state == "dismissed"


@pytest.mark.django_db
def test_bulk_dismiss_by_agency_honours_the_callers_other_filters(firm_a):
    ws, user = firm_a
    in_range = _match_with_agency(ws, "Org", date=datetime.date(2026, 7, 5))
    out_of_range = _match_with_agency(ws, "Org", date=datetime.date(2026, 7, 20))

    # Same query string the feed is showing, so the button cannot mean something
    # different from the list it sits above.
    resp = _api(user).post(
        "/api/matches/bulk_dismiss?date_from=2026-07-01&date_to=2026-07-10",
        {"agency": "Org"}, format="json")

    assert resp.data["dismissed"] == 1
    in_range.refresh_from_db(); out_of_range.refresh_from_db()
    assert in_range.state == "dismissed"
    assert out_of_range.state == "new"


@pytest.mark.django_db
def test_bulk_dismiss_needs_an_explicit_target(firm_a):
    ws, user = firm_a
    match = _match_with_agency(ws, "Org")

    resp = _api(user).post("/api/matches/bulk_dismiss", {}, format="json")

    # Never "everything currently filtered" by default: that is how someone
    # dismisses 700 rows they meant to read.
    assert resp.status_code == 400
    match.refresh_from_db()
    assert match.state == "new"


@pytest.mark.django_db
def test_bulk_dismiss_refuses_an_ambiguous_request(firm_a):
    ws, user = firm_a
    match = _match_with_agency(ws, "Org")

    resp = _api(user).post(
        "/api/matches/bulk_dismiss",
        {"ids": [match.id], "agency": "Org"}, format="json")

    assert resp.status_code == 400
    match.refresh_from_db()
    assert match.state == "new"


@pytest.mark.django_db
def test_bulk_dismiss_does_not_recount_rows_already_dismissed(firm_a):
    ws, user = firm_a
    _match_with_agency(ws, "Org", state="dismissed")
    live = _match_with_agency(ws, "Org")

    resp = _api(user).post("/api/matches/bulk_dismiss", {"agency": "Org"}, format="json")

    # get_queryset() excludes dismissed when no state filter is given, so the
    # number reported is the number of rows that actually changed.
    assert resp.data["dismissed"] == 1
    live.refresh_from_db()
    assert live.state == "dismissed"


@pytest.mark.django_db
def test_bulk_dismiss_rejects_a_non_list_of_ids(firm_a):
    _ws, user = firm_a
    resp = _api(user).post("/api/matches/bulk_dismiss", {"ids": "1,2,3"}, format="json")
    assert resp.status_code == 400


# --- Permanent delete from the archive --------------------------------------
#
# Dismissing is archiving: it hides a match, it never destroys one. Deletion is
# a separate, explicit act, and it can only reach what is already archived.

@pytest.mark.django_db
def test_delete_removes_archived_matches_and_reports_the_count(firm_a):
    ws, user = firm_a
    a = _match(ws, date=datetime.date(2026, 7, 1), state="dismissed")
    b = _match(ws, date=datetime.date(2026, 7, 1), state="dismissed")

    resp = _api(user).post("/api/matches/bulk_delete", {"ids": [a.id, b.id]}, format="json")

    assert resp.status_code == 200
    assert resp.data["deleted"] == 2
    assert not Match.objects.filter(pk__in=[a.id, b.id]).exists()


@pytest.mark.django_db
def test_delete_refuses_a_match_that_was_never_archived(firm_a):
    ws, user = firm_a
    archived = _match(ws, date=datetime.date(2026, 7, 1), state="dismissed")
    live = _match(ws, date=datetime.date(2026, 7, 1), state="new")

    resp = _api(user).post(
        "/api/matches/bulk_delete", {"ids": [archived.id, live.id]}, format="json")

    # All-or-nothing again, and the interesting half: deletion cannot reach a
    # row the operator has not first archived, so there is always one
    # deliberate step between a feed and an irreversible loss.
    assert resp.status_code == 404
    assert Match.objects.filter(pk=archived.id).exists()
    assert Match.objects.filter(pk=live.id).exists()


@pytest.mark.django_db
def test_delete_refuses_a_relevant_match(firm_a):
    ws, user = firm_a
    keeper = _match(ws, date=datetime.date(2026, 7, 1), state="relevant")

    resp = _api(user).post("/api/matches/bulk_delete", {"ids": [keeper.id]}, format="json")

    assert resp.status_code == 404
    assert Match.objects.filter(pk=keeper.id).exists()


@pytest.mark.django_db
def test_delete_cannot_cross_a_workspace_boundary(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    mine = _match(ws_a, date=datetime.date(2026, 7, 1), state="dismissed")
    theirs = _match(ws_b, date=datetime.date(2026, 7, 1), state="dismissed")

    resp = _api(user_a).post(
        "/api/matches/bulk_delete", {"ids": [mine.id, theirs.id]}, format="json")

    assert resp.status_code == 404
    assert Match.objects.filter(pk=mine.id).exists()
    assert Match.objects.filter(pk=theirs.id).exists()


@pytest.mark.django_db
def test_delete_ignores_the_feeds_own_filters(firm_a):
    # The archive is state=dismissed, which is exactly what the feed's default
    # queryset excludes. Deletion must not inherit that exclusion, or it would
    # be unable to reach the only rows it is allowed to touch.
    ws, user = firm_a
    archived = _match(ws, date=datetime.date(2026, 7, 1), state="dismissed")

    resp = _api(user).post("/api/matches/bulk_delete", {"ids": [archived.id]}, format="json")

    assert resp.status_code == 200
    assert not Match.objects.filter(pk=archived.id).exists()


@pytest.mark.django_db
def test_delete_needs_an_explicit_id_list(firm_a):
    _ws, user = firm_a
    assert _api(user).post("/api/matches/bulk_delete", {}, format="json").status_code == 400
    assert _api(user).post(
        "/api/matches/bulk_delete", {"ids": "1,2"}, format="json").status_code == 400
    # No "delete the whole archive" form: the archive is the safety net.
    assert _api(user).post(
        "/api/matches/bulk_delete", {"ids": []}, format="json").status_code == 400


@pytest.mark.django_db
def test_reopen_puts_an_archived_match_back_in_the_feed(firm_a):
    ws, user = firm_a
    archived = _match(ws, date=datetime.date(2026, 7, 1), state="dismissed")

    resp = _api(user).post(f"/api/matches/{archived.id}/reopen")

    assert resp.status_code == 200
    assert resp.data["state"] == "new"
    archived.refresh_from_db()
    assert archived.state == "new"


@pytest.mark.django_db
def test_reopen_reaches_a_row_the_feed_hides_by_default(firm_a):
    # get_object() runs through get_queryset(), which excludes dismissed rows
    # when no state filter is given -- so the archive's own action would 404 on
    # everything in the archive if it inherited that.
    ws, user = firm_a
    archived = _match(ws, date=datetime.date(2026, 7, 1), state="dismissed")
    resp = _api(user).post(f"/api/matches/{archived.id}/reopen")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_reopen_cannot_cross_a_workspace_boundary(firm_a, firm_b):
    _ws_a, user_a = firm_a
    ws_b, _ = firm_b
    theirs = _match(ws_b, date=datetime.date(2026, 7, 1), state="dismissed")

    resp = _api(user_a).post(f"/api/matches/{theirs.id}/reopen")

    assert resp.status_code == 404
    theirs.refresh_from_db()
    assert theirs.state == "dismissed"
