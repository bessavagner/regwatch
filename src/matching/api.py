from django.http import Http404
from django.shortcuts import get_object_or_404
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
        else:
            # Dismissing has to visibly shrink the feed, or triage is unpaid
            # work -- which is how 947 of 950 matches stayed untriaged. The
            # dismissed rows are hidden, not deleted: ?state=dismissed reaches
            # them, and the state filter still names all three explicitly.
            qs = qs.exclude(state="dismissed")
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
        """Archive a match: hide it from the feed without destroying it."""
        return self._set_state("dismissed")

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        """Take a match back out of the archive.

        get_object() normally runs through get_queryset(), which hides
        dismissed rows when no state filter is given — so this action would
        404 on everything it exists to act on. Look the row up in the
        workspace-scoped set instead, which is still the only scoping that
        matters for safety.
        """
        match = get_object_or_404(self.workspace_queryset(), pk=pk)
        match.state = "new"
        match.save(update_fields=["state"])
        return Response(self.get_serializer(match).data)

    @action(detail=False, methods=["post"])
    def bulk_dismiss(self, request):
        """Dismiss many matches at once: an explicit id list, or one agency.

        Both forms are narrowed by get_queryset(), so a bulk mutation can never
        reach further than the list the caller is looking at, nor outside their
        workspace.

        There is deliberately no "dismiss everything currently filtered" form.
        A mutation over hundreds of rows driven only by a re-parsed query string
        is how someone dismisses a day they meant to read, and the undo for that
        is reconstructing which rows were already dismissed beforehand.
        """
        ids = request.data.get("ids")
        agency = request.data.get("agency")

        if (ids is None) == (agency is None):
            raise serializers.ValidationError(
                "informe exatamente um de: ids ou agency"
            )

        qs = self.get_queryset()

        if ids is not None:
            if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
                raise serializers.ValidationError("ids precisa ser uma lista de inteiros")
            qs = qs.filter(pk__in=ids)
            # All-or-nothing. Silently dismissing the visible subset would
            # report a number the caller cannot act on, and would answer
            # "does this id exist elsewhere?" for rows they cannot see.
            if qs.count() != len(set(ids)):
                raise Http404("uma ou mais ocorrências não foram encontradas")
        else:
            if not isinstance(agency, str) or not agency.strip():
                raise serializers.ValidationError("agency não pode ficar vazio")
            qs = qs.filter(act__agency=agency)

        # update() rather than a save() loop: one statement, and the count it
        # returns is the number of rows that actually changed.
        dismissed = qs.update(state="dismissed")
        return Response({"dismissed": dismissed})

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """Permanently delete archived matches. There is no undo.

        Dismissing is archiving — it hides a match, it never destroys one — so
        this is the one operation in the app that actually loses something. Two
        properties keep it survivable:

        - it reaches only rows already in the archive, so there is always one
          deliberate step between reading a feed and losing a row;
        - it takes an explicit id list, never a filter and never "everything",
          so the blast radius is whatever the operator could see and tick.
        """
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
            raise serializers.ValidationError("ids precisa ser uma lista de inteiros não vazia")

        # workspace_queryset(), not get_queryset(): the feed hides dismissed
        # rows by default, which is precisely the set this may touch.
        qs = self.workspace_queryset().filter(pk__in=ids, state="dismissed")
        if qs.count() != len(set(ids)):
            raise Http404(
                "uma ou mais ocorrências não estão no arquivo ou não foram encontradas"
            )

        deleted, _ = qs.delete()
        return Response({"deleted": len(set(ids))})
