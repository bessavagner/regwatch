from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("gazette", "0004_pg_trgm_index")]

    operations = [
        migrations.RemoveIndex(model_name="act", name="gazette_act_search__f896b7_gin"),
        migrations.RemoveField(model_name="act", name="search_vector"),
    ]
