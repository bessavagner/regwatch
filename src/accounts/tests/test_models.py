import pytest
from django.contrib.auth.models import User
from accounts.models import Workspace, Membership


@pytest.mark.django_db
def test_user_joins_workspace():
    ws = Workspace.objects.create(name="Acme Law")
    user = User.objects.create(username="lawyer")
    Membership.objects.create(workspace=ws, user=user)
    assert ws.members.count() == 1
    assert ws.members.first().user == user
