import django.contrib.postgres.indexes
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("gazette", "0003_act_search_vector_pt")]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name="act",
            index=django.contrib.postgres.indexes.GinIndex(
                name="gazette_act_search_text_trgm",
                fields=["search_text"],
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
