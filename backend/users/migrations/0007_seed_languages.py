from django.db import migrations

def seed_languages(apps, schema_editor):
    Language = apps.get_model("users", "Language")

    languages = [
        {
            "name": "English",
            "code": "en",
            "native_name": "English",
        },
        {
            "name": "Hindi",
            "code": "hi",
            "native_name": "हिन्दी",
        },
        {
            "name": "Arabic",
            "code": "ar",
            "native_name": "العربية",
        },
        {
            "name": "Spanish",
            "code": "es",
            "native_name": "Español",
        },
        {
            "name": "French",
            "code": "fr",
            "native_name": "Français",
        },
        {
            "name": "German",
            "code": "de",
            "native_name": "Deutsch",
        },
        {
            "name": "Portugese",
            "code": "pt",
            "native_name": "Portugues",
        },
        {
            "name": "Chinese",
            "code": "zh",
            "native_name": "中文",
        },
        {
            "name": "Japanese",
            "code": "ja",
            "native_name":  "日本語",
        },
    ]

    for language in languages:
        Language.objects.get_or_create(
            code=language["code"],
            defaults={
                "name": language["name"],
                "native_name": language["native_name"],
                "is_active": True,
            },
        )

def remove_languages(apps, schema_editor):
    Language = apps.get_model("users", "Language")

    Language.objects.filter(
        code_in=[
            "en",
            "hi",
            "ur",
            "ar",
            "es",
            "fr",
            "de",
            "pt",
            "zh",
            "ja",
        ]
    ).delete()

class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_language_is_active"),
    ]

    operations = [
        migrations.RunPython(
            seed_languages,
            remove_languages,
        ),
    ]