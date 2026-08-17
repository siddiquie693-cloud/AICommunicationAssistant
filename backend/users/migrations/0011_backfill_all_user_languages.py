from django.db import migrations


def backfill_all_user_languages(apps, schema_editor):
    User = apps.get_model("users", "User")
    Language = apps.get_model("users", "Language")

    languages = {
        language.name: language
        for language in Language.objects.filter(is_active=True)
    }

    for user in User.objects.all():
        if user.preferred_language and not user.preferred_language_ref_id:
            language = languages.get(user.preferred_language)

            if language:
                user.preferred_language_ref_id = language.id

        if user.voice_language and not user.voice_language_ref_id:
            language = languages.get(user.voice_language)

            if language:
                user.voice_language_ref_id = language.id

        user.save(
            update_fields=[
                "preferred_language_ref",
                "voice_language_ref",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_backfill_user_languages"),
    ]

    operations = [
        migrations.RunPython(
            backfill_all_user_languages,
            migrations.RunPython.noop,
        ),
    ]