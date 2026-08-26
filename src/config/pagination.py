from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CountedPageNumberPagination(PageNumberPagination):
    """Paginated responses that say which page you are on and how many there are.

    DRF's default payload carries next/previous URLs but no page number and no
    total, so a client can only render "Page 1" beside two blind buttons. The
    alternative -- teaching the SPA that PAGE_SIZE is 25 -- is the duplicated
    constant TASK-005 just deleted. The server owns the page size, so the
    server does the arithmetic and reports it.

    page_size travels too: a client that removes a row from the filtered set
    during triage has to recompute the last page before the next response
    lands, and that division needs the divisor.
    """

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "page": self.page.number,
            "total_pages": self.page.paginator.num_pages,
            "page_size": self.get_page_size(self.request),
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
