from rest_framework import serializers

class TranslationSerializer(serializers.Serializer):
    text = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )
    source_language = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    target_language = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )