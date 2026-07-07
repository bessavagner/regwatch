import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from accounts.models import Membership, Workspace

User = get_user_model()


@pytest.mark.django_db
def test_invite_user_creates_user_workspace_and_membership():
    call_command("invite_user", workspace="Acme", email="a@firm.com", password="pw12345")
    user = User.objects.get(username="a@firm.com")
    ws = Workspace.objects.get(name="Acme")
    assert Membership.objects.filter(user=user, workspace=ws).exists()
    assert user.check_password("pw12345")


@pytest.mark.django_db
def test_invite_user_is_idempotent():
    call_command("invite_user", workspace="Acme", email="a@firm.com")
    call_command("invite_user", workspace="Acme", email="a@firm.com")
    assert User.objects.filter(username="a@firm.com").count() == 1
    assert Membership.objects.count() == 1


@pytest.mark.django_db
def test_invite_user_reads_password_from_env(monkeypatch):
    # A Secret Manager-backed env var supplies the password without putting it
    # on the command line (which would persist in inspectable Job config).
    monkeypatch.setenv("INVITE_USER_PASSWORD", "envpw12345")
    call_command("invite_user", workspace="Acme", email="a@firm.com")
    assert User.objects.get(username="a@firm.com").check_password("envpw12345")


@pytest.mark.django_db
def test_invite_user_password_flag_overrides_env(monkeypatch):
    monkeypatch.setenv("INVITE_USER_PASSWORD", "envpw12345")
    call_command("invite_user", workspace="Acme", email="a@firm.com", password="flagpw999")
    assert User.objects.get(username="a@firm.com").check_password("flagpw999")
