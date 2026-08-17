from django.db import migrations


def backfill_user_languages(apps, schema_editor):
    User = apps.get_model("users", "User")
    Language = apps.get_model("users", "Language")

    english = Language.objects.filter(
        code="en",
        is_active=True,
    ).first()

    if not english:
        return

    User.objects.filter(
        preferred_language="English",
        preferred_language_ref__isnull=True,
    ).update(
        preferred_language_ref=english,
    )

    User.objects.filter(
        voice_language="English",
        voice_language_ref__isnull=True,
    ).update(
        voice_language_ref=english,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_user_preferred_language_ref_user_voice_language_ref"),
    ]

    operations = [
        migrations.RunPython(
            backfill_user_languages,
            migrations.RunPython.noop,
        ),
    ]