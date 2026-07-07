from accounts.models import Membership


def workspace_ids_for(user):
    return list(
        Membership.objects.filter(user=user).values_list("workspace_id", flat=True)
    )


class WorkspaceScopedQuerysetMixin:
    """Filter every queryset to the objects in the caller's workspace(s).

    `workspace_lookup` is the ORM path from the model to its Workspace
    (e.g. "workspace", "client__workspace", "watch__client__workspace").
    Out-of-scope object ids therefore 404 via DRF's get_object().
    """

    workspace_lookup = "workspace"

    def get_queryset(self):
        qs = super().get_queryset()
        ids = workspace_ids_for(self.request.user)
        return qs.filter(**{f"{self.workspace_lookup}__in": ids})

    def _user_workspace(self):
        membership = Membership.objects.filter(user=self.request.user).first()
        return membership.workspace if membership else None
