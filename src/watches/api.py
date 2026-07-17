import datetime
import traceback
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.permissions import WorkspaceScopedQuerysetMixin, workspace_ids_for
from pipeline.adapters import get_llm_client
from pipeline.backfill import backfill_watch
from pipeline.models import RunLog
from watches.models import Client, Watch

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name", "is_house", "email"]


class ClientViewSet(WorkspaceScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    queryset = Client.objects.all()
    workspace_lookup = "workspace"

    def perform_create(self, serializer):
        workspace = self._user_workspace()
        if workspace is None:
            raise PermissionDenied("no workspace membership")
        serializer.save(workspace=workspace)


class WatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watch
        fields = ["id", "client", "terms", "exclude", "section", "active"]

    def validate_terms(self, value):
        if not value:
            raise serializers.ValidationError("terms must not be empty")
        return value

    def validate_client(self, value):
        user = self.context["request"].user
        if value.workspace_id not in workspace_ids_for(user):
            raise serializers.ValidationError("client not in your workspace")
        return value


class BackfillRequestSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()

    def validate(self, data):
        if data["date_from"] > data["date_to"]:
            raise serializers.ValidationError("date_from must not be after date_to")
        if (data["date_to"] - data["date_from"]).days > 6:
            raise serializers.ValidationError("range must not exceed 7 days")
        today = datetime.datetime.now(SAO_PAULO).date()
        if data["date_to"] > today:
            raise serializers.ValidationError("date_to must not be in the future")
        return data


class WatchViewSet(WorkspaceScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = WatchSerializer
    queryset = Watch.objects.all()
    workspace_lookup = "client__workspace"

    @action(detail=True, methods=["post"])
    def backfill(self, request, pk=None):
        self.get_object()  # 404 when the watch is outside the caller's workspace
        serializer = BackfillRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        date_from = serializer.validated_data["date_from"]
        date_to = serializer.validated_data["date_to"]

        log = RunLog.objects.create(date=date_to, status="running", trigger="backfill")
        try:
            result = backfill_watch(
                date_from, date_to, get_llm_client(),
                max_enrich=settings.REGWATCH_MAX_ENRICH_PER_RUN,
            )
        except Exception:
            log.status = "failed"
            log.errors = traceback.format_exc()
            log.finished_at = timezone.now()
            log.save()
            raise

        log.status = "success"
        log.editions = result.editions
        log.acts = result.acts
        log.matches = result.matches
        log.enriched = result.enriched
        log.errors = "; ".join(result.skipped_dates)
        log.finished_at = timezone.now()
        log.save()

        return Response({
            "editions": result.editions,
            "acts": result.acts,
            "matches": result.matches,
            "enriched": result.enriched,
            "skipped_dates": result.skipped_dates,
        })
