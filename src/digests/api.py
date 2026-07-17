from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import WorkspaceScopedQuerysetMixin, workspace_ids_for
from digests.models import Digest
from digests.notifier import build_and_send_digests
from pipeline.adapters import get_email_sender
from watches.models import Client


class DigestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Digest
        fields = ["id", "client", "date", "body", "sent"]


class SendDigestRequestSerializer(serializers.Serializer):
    client = serializers.IntegerField()
    date = serializers.DateField()


class _LazyEmailSender:
    """Defers get_email_sender() until an email actually needs sending.

    build_and_send_digests() only calls sender.send() when there is a
    matched client to notify. Resolving the real sender eagerly would
    require a configured email provider even for a request that ends up
    finding no matches (and thus 404s) for that client+date.
    """

    def send(self, to: str, subject: str, body: str) -> None:
        get_email_sender().send(to=to, subject=subject, body=body)


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

    @action(detail=False, methods=["post"])
    def send(self, request):
        serializer = SendDigestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = get_object_or_404(
            Client.objects.filter(workspace_id__in=workspace_ids_for(request.user)),
            pk=serializer.validated_data["client"],
        )
        digests = build_and_send_digests(
            serializer.validated_data["date"], _LazyEmailSender(), client=client,
        )
        if not digests:
            raise Http404("no matches for this client on this date")
        return Response(DigestSerializer(digests[0]).data)
