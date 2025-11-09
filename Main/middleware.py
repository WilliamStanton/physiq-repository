from django.shortcuts import redirect
from django.urls import resolve

from Main.models import UserProfile


class ForceProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={"profile_completed": False}
            )

            current_url = resolve(request.path_info).url_name

            # Allow profile page & logout while incomplete
            if not profile.profile_completed:
                if current_url not in ("profile", "logout"):
                    return redirect("profile")

        return self.get_response(request)