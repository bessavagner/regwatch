import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Membership, Workspace

User = get_user_model()


class Command(BaseCommand):
    help = "Provision an invite-only user and attach them to a workspace."

    def add_arguments(self, parser):
        parser.add_argument("--workspace", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=False)

    def handle(self, *args, **options):
        workspace, _ = Workspace.objects.get_or_create(name=options["workspace"])
        email = options["email"]
        user, created = User.objects.get_or_create(
            username=email, defaults={"email": email}
        )
        # Prefer an explicit --password; fall back to INVITE_USER_PASSWORD so a
        # password can be supplied via a Secret Manager-backed env var instead of
        # the command line, which persists in inspectable Cloud Run Job config.
        password = options.get("password") or os.environ.get("INVITE_USER_PASSWORD")
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        Membership.objects.get_or_create(workspace=workspace, user=user)
        verb = "created" if created else "updated"
        self.stdout.write(f"{verb} {email} in workspace {workspace.name!r}")
