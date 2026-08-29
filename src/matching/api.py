from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import WorkspaceScopedQuerysetMixin
from enrichment.categories import label_for
from gazette.models import Act
from matching.models import Match


class ActDetailSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source="edition.date", read_only=True)
    section = serializers.CharField(source="edition.section", read_only=True)
    source_url = serializers.CharField(source="edition.source_url", read_only=True)

    class Meta:
        model = Act
        fields = [
            "id", "title", "agency", "identifier",
            "date", "section", "source_url", "source_anchor",
        ]


class MatchSerializer(serializers.ModelSerializer):
    act_detail = ActDetailSerializer(source="act", read_only=True)
    client_id = serializers.IntegerField(source="watch.client_id", read_only=True)
    client_name = serializers.CharField(source="watch.client.name", read_only=True)
    # The label rides along with the row so a rendered badge never depends on a
    # second request having landed. category itself stays the storage enum.
    category_label = serializers.SerializerMethodField()

    def get_category_label(self, obj) -> str:
        return label_for(obj.category)

    class Meta:
        model = Match
        fields = [
            "id", "watch", "act", "act_detail", "client_id", "client_name",
            "snippet", "matched_terms", "rank", "ai_summary", "category",
            "category_label",
            "names_party", "has_amount", "has_deadline", "signal_score",
            "state", "created_at",
        ]


class MatchViewSet(WorkspaceScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    queryset = Match.objects.select_related("act__edition", "watch__client").all()
    workspace_lookup = "watch__client__workspace"

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if value := p.get("client"):
            qs = qs.filter(watch__client_id=value)
        if value := p.get("state"):
            qs = qs.filter(state=value)
        if value := p.get("section"):
            qs = qs.filter(act__edition__section=value)
        if value := p.get("category"):
            qs = qs.filter(category=value)
        if value := p.get("date_from"):
            qs = qs.filter(act__edition__date__gte=value)
        if value := p.get("date_to"):
            qs = qs.filter(act__edition__date__lte=value)
        ordering = p.get("ordering")
        if ordering == "signal":
            # rank is the tiebreaker now, not the sort: it measures textual
            # match strength, which says nothing about whether an act is worth
            # a client's attention.
            return qs.order_by("-signal_score", "-rank", "-id")
        if ordering == "rank":
            return qs.order_by("-rank", "-id")
        return qs.order_by("-created_at", "-id")

    def _set_state(self, new_state):
        match = self.get_object()  # 404 when out of the caller's workspace
        match.state = new_state
        match.save(update_fields=["state"])
        return Response(self.get_serializer(match).data)

    @action(detail=True, methods=["post"])
    def relevant(self, request, pk=None):
        return self._set_state("relevant")

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        return self._set_state("dismissed")
