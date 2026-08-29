import json

from django.core.management.base import BaseCommand, CommandError

from watches.grouping import groups_from_specs
from watches.models import Client, Watch



class Command(BaseCommand):
    help = (
        "Create a watch for a client from the command line. Groups are ANDed and "
        "the terms inside one are ORed, as in Watch.groups. Dry-run unless "
        "--apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument("--client", type=int, required=True, help="client id")
        parser.add_argument(
            "--group", action="append", default=[],
            metavar="[KIND:]TERM|TERM",
            help="one ANDed group; repeat for more. KIND is entity (default) or concept.",
        )
        # `gcloud run jobs execute --args` refuses a repeated flag, so the
        # production path needs every flag named once. Same grammar, ';' between
        # groups.
        parser.add_argument(
            "--groups", default="", metavar="GROUP;GROUP",
            help="all groups in one argument, separated by ';' (for gcloud --args)",
        )
        parser.add_argument("--exclude", action="append", default=[], help="excluded phrase")
        parser.add_argument(
            "--excludes", default="", metavar="PHRASE;PHRASE",
            help="all excluded phrases in one argument, separated by ';'",
        )
        parser.add_argument("--section", default="", help='DOU section, e.g. DO1 ("" = all)')
        parser.add_argument("--apply", action="store_true", help="actually create it")
        parser.add_argument("--json", action="store_true", help="machine-readable output")

    def handle(self, *args, **options):
        try:
            client = Client.objects.get(pk=options["client"])
        except Client.DoesNotExist as exc:
            raise CommandError(f"no client with id {options['client']}") from exc

        if not options["group"] and not options["groups"].strip():
            raise CommandError("at least one group is required (--group or --groups)")
        try:
            groups = groups_from_specs(options["group"], options["groups"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        exclude = [
            e.strip()
            for e in list(options["exclude"]) + options["excludes"].split(";")
            if e.strip()
        ]
        section = options["section"].strip()

        # Re-running a provisioning command must not silently double a client's
        # digest volume -- provision.sh already taught us that lesson.
        if Watch.objects.filter(
            client=client, groups=groups, section=section
        ).exists():
            raise CommandError(
                f"client {client.name} already has an identical watch "
                "(same groups and section); nothing created"
            )

        if not options["apply"]:
            self.stdout.write(
                f"would create a watch for {client.name} (client {client.pk}):\n"
                f"  section : {section or '(all)'}\n"
                f"  groups  : {json.dumps(groups, ensure_ascii=False)}\n"
                f"  exclude : {json.dumps(exclude, ensure_ascii=False)}\n"
                "dry run, nothing written -- re-run with --apply"
            )
            return

        watch = Watch.objects.create(
            client=client, groups=groups, exclude=exclude, section=section, active=True
        )
        if options["json"]:
            self.stdout.write(json.dumps({
                "id": watch.pk, "client": client.pk, "section": section,
                "groups": groups, "exclude": exclude,
            }, ensure_ascii=False))
            return
        self.stdout.write(
            f"created watch {watch.pk} for {client.name} "
            f"({len(groups)} group(s), {len(exclude)} exclude(s), "
            f"section {section or '(all)'})"
        )
