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
        if options.get("password"):
            user.set_password(options["password"])
            user.save(update_fields=["password"])
        Membership.objects.get_or_create(workspace=workspace, user=user)
        verb = "created" if created else "updated"
        self.stdout.write(f"{verb} {email} in workspace {workspace.name!r}")
