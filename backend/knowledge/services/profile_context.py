from users.models import NIRAPersonalProfile


class NIRAPersonalProfileContextService:
    """
    Converts a NIRA personal profile into structured AI context.
    """

    PROFILE_FIELDS = (
        ("languages", "Languages"),
        ("communication_style", "Communication Style"),
        ("work_info", "Work Information"),
        ("skills", "Skills"),
        ("interests", "Interests"),
        ("important_people", "Important People"),
        ("custom_instructions", "Custom Instructions"),
        ("privacy_settings", "Privacy Settings"),
        ("memory_settings", "Memory Settings"),
    )

    CONTEXT_FIELD_GROUPS = {
        "general": {
            "languages",
            "communication_style",
            "interests",
        },
        "work": {
            "work_info",
            "skills",
        },
        "communication": {
            "languages",
            "communication_style",
            "important_people",
        },
        "instructions": {
            "custom_instructions",
        },
        "privacy": {
            "privacy_settings",
        },
        "memory": {
            "memory_settings",
        },
    }

    PROTECTED_FIELDS = {
        "privacy_settings",
        "memory_settings",
    }


    def _validate_context_fields(
        self,
        context_purpose: str,
        allowed_fields: set[str],
    ) -> None:
        """
        Prevent protected profile fields from entering
        non-protected AI contexts.
        """

        if context_purpose in {"privacy", "memory"}:
            return

        exposed_protected_fields = (
            allowed_fields & self.PROTECTED_FIELDS
        )

        if exposed_protected_fields:
            raise ValueError(
                "Protected profile fields cannot be exposed "
                f"for context purpose: {context_purpose}."
            )

    def _validate_exposed_fields(
        self,
        allowed_fields: set[str],
    ) -> None:
        """
        Ensure only profile fields explicity defined by the 
        profile context service can enter an AI context.
        """

        supported_fields = {
            field_name
            for field_name, _label in self.PROFILE_FIELDS
        }

        unsupported_fields = (
            allowed_fields - supported_fields
        )

        if unsupported_fields:
            raise ValueError(
                "Unsupported profile fields cannot be exposed "
                "to AI context."
            )    

    def build(
        self,
        profile: NIRAPersonalProfile,
        *,
        context_purpose: str = "general",
    ) -> str:
        """
        Build structured context from a personal profile.
        """

        if context_purpose not in self.CONTEXT_FIELD_GROUPS:
            raise ValueError(
                f"Unsupported profile context purpose: "
                f"{context_purpose}"
            )

        allowed_fields = self.CONTEXT_FIELD_GROUPS[
            context_purpose
        ]

        self._validate_context_fields(
            context_purpose,
            allowed_fields,
        )

        self._validate_exposed_fields(
            allowed_fields,
        )

        context_parts = ["Personal Profile:"]

        for field_name, label in self.PROFILE_FIELDS:
            if field_name not in allowed_fields:
                continue

            value = getattr(profile, field_name)

            if value in (None, "", [], {}):
                continue

            context_parts.append(
                f"{label}: {value}"
            )

        if len(context_parts) == 1:
            return ""

        return "\n".join(context_parts)