from rest_framework import serializers


class TextToSpeechSerializer(serializers.Serializer):

    text = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    language = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=False,
    )

    voice = serializers.CharField(
        required=False,
        allow_blank=True,
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

        if "voice" in self.initial_data:
            voice = self.initial_data["voice"]

            if not voice or not str(voice).strip():
                raise serializers.ValidationError(
                    {
                        "voice": "Voice cannot be empty."
                    }
                )

            attrs["voice"] = str(voice).strip()

        return attrs