from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import WorkspaceScopedQuerysetMixin
from matching.models import Match


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = [
            "id", "watch", "act", "snippet", "rank", "ai_summary",
            "category", "confidence", "state", "created_at",
        ]


class MatchViewSet(WorkspaceScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    queryset = Match.objects.all()
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
        if p.get("ordering") == "rank":
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
