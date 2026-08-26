---
id: decision-005
title: The API reports its own pagination arithmetic
date: '2026-08-26 23:23'
status: accepted
---
## Context

TASK-011 needs the feed to render "Page N of M". DRF's default paginated
payload has count/next/previous/results and no page number or total, so the
client has to derive M as ceil(count / page_size) -- and page_size is
PAGE_SIZE = 25 in src/config/settings.py, a server constant.

## Decision

Add page, total_pages and page_size to every paginated response via
config.pagination.CountedPageNumberPagination, set as DEFAULT_PAGINATION_CLASS.
The SPA never learns the page size; it reads the arithmetic.

Rejected: hardcoding 25 in the SPA. That is the same duplicated-constant bug
as web/src/lib/constants.ts::CATEGORIES, which TASK-005 deleted -- a value
owned by the server, copied into the client, free to drift silently. Changing
PAGE_SIZE would have quietly broken every page indicator.

Rejected: a matches-only pagination class. Three endpoints paginate; one
contract is cheaper to hold than two.

## Consequences

Every list endpoint's payload grows by three integers. This is additive and no
existing test asserts an exact key set. Changing PAGE_SIZE now updates the
client automatically. Page<T> in the SPA carries the fields as optional (only
the feed consumes them) while listMatches returns Paged<Match>, which
requires them.
