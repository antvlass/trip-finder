from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("flights", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="airport",
            options={"managed": False, "db_table": "airports", "ordering": ["code"]},
        ),
    ]
