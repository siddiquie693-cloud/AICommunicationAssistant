from ai.intent.categories import IntentCategory


USER_REQUEST_INTENT_MAPPING = {
    "call": "call_person",
    "message": "send_message",
    "open": "open_app",
    "reminder": "create_reminder",
    "navigate": "navigate",
    "media": "play_media",
    "notification": "check_notifications",
}

INTENT_CATEGORY_MAPPING = {
    "call_person": IntentCategory.PHONE,
    "send_message": IntentCategory.MESSAGING,
    "open_app": IntentCategory.APP_CONTROL,
    "create_reminder": IntentCategory.REMINDER,
    "navigate": IntentCategory.NAVIGATION,
    "play_media": IntentCategory.MEDIA,
    "check_notifications": IntentCategory.NOTIFICATION,
    "unknown": IntentCategory.UNKNOWN,
}