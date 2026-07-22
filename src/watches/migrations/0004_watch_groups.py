from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("watches", "0003_watch_match_mode")]

    operations = [
        migrations.AddField(
            model_name="watch",
            name="groups",
            field=models.JSONField(default=list),
        ),
    ]
