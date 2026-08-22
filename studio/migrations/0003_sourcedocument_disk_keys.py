from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("studio", "0002_alter_aiconfiguration_model_name")]

    operations = [
        migrations.AddField(
            model_name="sourcedocument",
            name="disk_source_key",
            field=models.CharField(blank=True, max_length=900, verbose_name="Исходник в DiskSL"),
        ),
        migrations.AddField(
            model_name="sourcedocument",
            name="disk_result_key",
            field=models.CharField(blank=True, max_length=900, verbose_name="Результат в DiskSL"),
        ),
    ]
