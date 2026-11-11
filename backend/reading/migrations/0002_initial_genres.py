from django.db import migrations


def seed_genres(apps, schema_editor):
    genre = apps.get_model("reading", "Genre")
    rows = [
        ("science_fiction", "Bilim kurgu"),
        ("philosophy", "Felsefe"),
        ("fantasy", "Fantastik"),
        ("humor", "Mizah"),
        ("crime", "Polisiye"),
    ]
    for code, name in rows:
        genre.objects.using(schema_editor.connection.alias).get_or_create(
            code=code, defaults={"name": name}
        )


class Migration(migrations.Migration):
    dependencies = [("reading", "0001_initial")]
    operations = [migrations.RunPython(seed_genres, migrations.RunPython.noop)]
