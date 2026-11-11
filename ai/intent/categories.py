from enum import StrEnum


class IntentCategory(StrEnum):
    """
    High-level categories of actions and requests understood by NIRA.
    """

    COMMUNICATION = "communication"
    PHONE = "phone"
    MESSAGING = "messaging"
    APP_CONTROL = "app_control"
    INFORMATION = "information"
    NAVIGATION = "navigation"
    REMINDER = "reminder"
    NOTIFICATION = "notification"
    MEDIA = "media"
    SYSTEM = "system"
    UNKNOWN = "unknown"