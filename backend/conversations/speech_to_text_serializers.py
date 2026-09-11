from rest_framework import serializers


class SpeechToTextSerializer(serializers.Serializer):

    audio = serializers.FileField(
        allow_empty_file=False,
    )

    language = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False,
    )

    def validate(self, attrs):
        if "language" in self.initial_data:
            language = self.initial_data["language"]

            if not language or not str(language).strip():
                raise serializers.ValidationError(
                    {
                        "language": "Language cannot be empty."
                    }
                )

            attrs["language"] = str(language).strip()

        return attrs