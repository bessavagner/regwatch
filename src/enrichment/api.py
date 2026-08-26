from rest_framework.response import Response
from rest_framework.views import APIView

from enrichment.categories import CATEGORY_LABELS


class VocabularyView(APIView):
    """The user-facing vocabulary, so the SPA does not carry its own copy.

    Order is the contract: the filter dropdown renders this list as given.
    """

    def get(self, request):
        return Response({
            "categories": [
                {"value": value, "label": label}
                for value, label in CATEGORY_LABELS.items()
            ]
        })
