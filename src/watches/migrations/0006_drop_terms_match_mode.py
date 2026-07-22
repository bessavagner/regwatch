from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("watches", "0005_backfill_watch_groups")]

    operations = [
        migrations.RemoveField(model_name="watch", name="terms"),
        migrations.RemoveField(model_name="watch", name="match_mode"),
    ]
