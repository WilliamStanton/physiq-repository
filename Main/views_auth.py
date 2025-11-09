from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout

from .forms import LoginForm, RegisterForm, UserProfileForm
from .models import UserProfile

from django.contrib.auth import login


def login_view(request):
    login_form = LoginForm(request, data=request.POST or None)
    register_form = RegisterForm(request.POST or None)

    if request.method == "POST":
        # Check if it's a login request
        if (
            "username" in request.POST
            and "password" in request.POST
            and not "email" in request.POST
        ):
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Registration logic
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect("dashboard")
            else:
                messages.error(request, "Please correct the errors below.")

    return render(
        request,
        "auth/login.html",
        {
            "login_form": login_form,
            "register_form": register_form,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("/")


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()

            profile.profile_completed = profile.is_complete()
            profile.save()

            return redirect("dashboard")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "auth/profile.html", {"form": form})
