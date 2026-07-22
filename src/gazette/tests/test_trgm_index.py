import pytest
from django.db import connection


@pytest.mark.django_db
def test_trigram_index_exists():
    with connection.cursor() as cur:
        cur.execute(
            "select indexdef from pg_indexes where indexname = %s",
            ["gazette_act_search_text_trgm"],
        )
        row = cur.fetchone()
    assert row is not None, "trigram index is missing"
    assert "gin_trgm_ops" in row[0]
