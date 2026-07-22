from django.db import migrations

from watches.grouping import groups_from_terms


def forwards(apps, schema_editor):
    # Faithful conversion: this must not repair a badly configured watch. A watch
    # that matched nothing before still matches nothing after, so any change in
    # match counts after deploy is attributable to the matcher, not to this.
    Watch = apps.get_model("watches", "Watch")
    for watch in Watch.objects.all():
        watch.groups = groups_from_terms(watch.terms, watch.match_mode)
        watch.save(update_fields=["groups"])


def backwards(apps, schema_editor):
    Watch = apps.get_model("watches", "Watch")
    Watch.objects.update(groups=[])


class Migration(migrations.Migration):
    dependencies = [("watches", "0004_watch_groups")]

    operations = [migrations.RunPython(forwards, backwards)]
