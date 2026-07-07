from rest_framework import serializers, viewsets

from accounts.permissions import WorkspaceScopedQuerysetMixin
from digests.models import Digest


class DigestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Digest
        fields = ["id", "client", "date", "body", "sent"]


class DigestViewSet(WorkspaceScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DigestSerializer
    queryset = Digest.objects.all()
    workspace_lookup = "client__workspace"

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if value := p.get("client"):
            qs = qs.filter(client_id=value)
        if value := p.get("date"):
            qs = qs.filter(date=value)
        return qs.order_by("-date")
