from rest_framework import serializers, viewsets

from accounts.permissions import WorkspaceScopedQuerysetMixin, workspace_ids_for
from watches.models import Client, Watch


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name", "is_house", "email"]


class ClientViewSet(WorkspaceScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    queryset = Client.objects.all()
    workspace_lookup = "workspace"

    def perform_create(self, serializer):
        serializer.save(workspace=self._user_workspace())


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


class WatchViewSet(WorkspaceScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = WatchSerializer
    queryset = Watch.objects.all()
    workspace_lookup = "client__workspace"
