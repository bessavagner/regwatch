from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='runlog',
            name='trigger',
            field=models.CharField(
                choices=[('scheduled', 'scheduled'), ('backfill', 'backfill')],
                default='scheduled',
                max_length=20,
            ),
        ),
    ]
