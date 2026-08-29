import json

from django.core.management.base import BaseCommand, CommandError

from watches.grouping import groups_from_specs
from watches.models import Watch


class Command(BaseCommand):
    help = (
        "Change an existing watch's groups, excludes, section or active flag. "
        "Only what you name is touched. Dry-run unless --apply is given, and the "
        "dry run prints before and after."
    )

    def add_arguments(self, parser):
        parser.add_argument("--watch", type=int, required=True, help="watch id")
        parser.add_argument(
            "--group", action="append", default=[], metavar="[KIND:]TERM|TERM",
            help="one ANDed group; repeat for more",
        )
        parser.add_argument(
            "--groups", default="", metavar="GROUP;GROUP",
            help="all groups in one argument, separated by ';' (for gcloud --args)",
        )
        parser.add_argument("--exclude", action="append", default=[], help="excluded phrase")
        parser.add_argument(
            "--excludes", default="", metavar="PHRASE;PHRASE",
            help="all excluded phrases in one argument, separated by ';'",
        )
        parser.add_argument(
            "--clear-excludes", action="store_true",
            help="remove every exclude (an empty --excludes cannot say this)",
        )
        parser.add_argument("--section", help='DOU section, e.g. DO1 ("" = all)')
        parser.add_argument("--active", action="store_true", help="reactivate the watch")
        parser.add_argument("--inactive", action="store_true", help="stop the watch matching")
        parser.add_argument("--apply", action="store_true", help="actually write the change")

    def handle(self, *args, **options):
        try:
            watch = Watch.objects.select_related("client").get(pk=options["watch"])
        except Watch.DoesNotExist as exc:
            raise CommandError(f"no watch with id {options['watch']}") from exc

        if options["active"] and options["inactive"]:
            raise CommandError("--active and --inactive contradict each other")

        changes = {}
        if options["group"] or options["groups"].strip():
            try:
                changes["groups"] = groups_from_specs(options["group"], options["groups"])
            except ValueError as exc:
                raise CommandError(str(exc)) from exc

        if options["clear_excludes"]:
            changes["exclude"] = []
        elif options["exclude"] or options["excludes"].strip():
            changes["exclude"] = [
                e.strip()
                for e in list(options["exclude"]) + options["excludes"].split(";")
                if e.strip()
            ]

        if options["section"] is not None:
            changes["section"] = options["section"].strip()
        if options["active"]:
            changes["active"] = True
        if options["inactive"]:
            changes["active"] = False

        if not changes:
            raise CommandError(
                "nothing to change; name at least one of --group(s), --exclude(s), "
                "--clear-excludes, --section, --active or --inactive"
            )

        def show(value):
            return json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value

        self.stdout.write(f"watch {watch.pk} ({watch.client.name}):")
        for field, after in changes.items():
            before = getattr(watch, field)
            self.stdout.write(f"  {field}:\n    before {show(before)}\n    after  {show(after)}")

        if not options["apply"]:
            self.stdout.write("dry run, nothing written -- re-run with --apply")
            return

        for field, value in changes.items():
            setattr(watch, field, value)
        watch.save(update_fields=list(changes))
        self.stdout.write(f"updated watch {watch.pk}: {', '.join(changes)}")
