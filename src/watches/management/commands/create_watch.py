import json

from django.core.management.base import BaseCommand, CommandError

from watches.grouping import KIND_ENTITY, VALID_KINDS
from watches.models import Client, Watch


def _parse_group(spec: str) -> dict:
    """Turn "concept:convênio|termo de fomento" into a groups entry.

    The kind prefix is optional and applies to every term in the group, which is
    how watches are actually written: a group is one dimension (the places, the
    funding words), and a dimension does not mix entity and concept semantics.
    """
    kind = KIND_ENTITY
    body = spec
    head, sep, rest = spec.partition(":")
    if sep and head.strip().lower() in VALID_KINDS:
        kind, body = head.strip().lower(), rest
    elif sep and " " not in head and head.strip() and not head.strip().isdigit():
        # A prefix was clearly intended -- naming an unknown kind must not
        # silently fall through to entity and quietly change the semantics.
        raise CommandError(
            f"unknown term kind {head.strip()!r}; use one of {', '.join(VALID_KINDS)}"
        )

    terms = [{"text": t.strip(), "kind": kind} for t in body.split("|") if t.strip()]
    if not terms:
        raise CommandError(
            f"group {spec!r} has no terms; the matcher fails closed on an empty "
            "group, so the watch would match nothing while looking active"
        )
    return {"terms": terms}


class Command(BaseCommand):
    help = (
        "Create a watch for a client from the command line. Groups are ANDed and "
        "the terms inside one are ORed, as in Watch.groups. Dry-run unless "
        "--apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument("--client", type=int, required=True, help="client id")
        parser.add_argument(
            "--group", action="append", default=[], required=True,
            metavar="[KIND:]TERM|TERM",
            help="one ANDed group; repeat for more. KIND is entity (default) or concept.",
        )
        parser.add_argument("--exclude", action="append", default=[], help="excluded phrase")
        parser.add_argument("--section", default="", help='DOU section, e.g. DO1 ("" = all)')
        parser.add_argument("--apply", action="store_true", help="actually create it")
        parser.add_argument("--json", action="store_true", help="machine-readable output")

    def handle(self, *args, **options):
        try:
            client = Client.objects.get(pk=options["client"])
        except Client.DoesNotExist as exc:
            raise CommandError(f"no client with id {options['client']}") from exc

        groups = [_parse_group(spec) for spec in options["group"]]
        exclude = [e.strip() for e in options["exclude"] if e.strip()]
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
