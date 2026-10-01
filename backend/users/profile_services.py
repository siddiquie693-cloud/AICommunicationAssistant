from .models import NIRAPersonalProfile


def get_nira_personal_profile(user):
    return NIRAPersonalProfile.objects.get(user=user)

def create_nira_personal_profile(user, **profile_data):
    return NIRAPersonalProfile.objects.create(
        user=user,
        **profile_data,
    )

def update_nira_personal_profile(profile, **profile_data):
    for field_name, value in profile_data.items():
        setattr(profile, field_name, value)

    profile.full_clean()
    profile.save()

    return profile

def validate_nira_personal_profile(profile):
    profile.full_clean()
    return profile

def get_or_create_nira_personal_profile(user):
    profile, created = NIRAPersonalProfile.objects.get_or_create(
        user=user,
    )

    return profile, created

def ensure_nira_profile_owner(profile, user):
    if profile.user_id != user.id:
        raise PermissionError(
            "User does not own this NIRA personal profile."
        )

    return profile