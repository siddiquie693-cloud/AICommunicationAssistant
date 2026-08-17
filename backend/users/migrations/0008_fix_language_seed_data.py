from django.db import migrations


def fix_language_seed_data(apps, schema_editor):
    Language = apps.get_model("users", "Language")

    Language.objects.update_or_create(
        code="ur",
        defaults={
            "name": "Urdu",
            "native_name": "اردو",
            "is_active": True,
        },
    )

    Language.objects.update_or_create(
        code="pt",
        defaults={
            "name": "Portuguese",
            "native_name": "Português",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_seed_languages"),
    ]

    operations = [
        migrations.RunPython(
            fix_language_seed_data,
            migrations.RunPython.noop,
        ),
    ]