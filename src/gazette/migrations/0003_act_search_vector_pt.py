import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("gazette", "0002_alter_act_agency_alter_act_source_anchor_and_more")]

    operations = [
        migrations.AddField(
            model_name="act",
            name="search_vector_pt",
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name="act",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_vector_pt"], name="gazette_act_search_pt_gin"
            ),
        ),
    ]
