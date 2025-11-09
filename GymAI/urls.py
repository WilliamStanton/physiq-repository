from django.urls import path

from Main import views_auth, views, views_dashboard
from Main.views import chat_api
from . import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("auth/", views_auth.login_view, name="auth"),
    path("login/", views_auth.login_view, name="login"),
    path("logout/", views_auth.logout_view, name="logout"),
    path("profile/", views_auth.profile_view, name="profile"),
    path("dashboard/", views_dashboard.dashboard_view, name="dashboard"),
    path("dashboard/overview/", views_dashboard.overview_view, name="overview"),
    path("dashboard/workout/", views_dashboard.workout_view, name="workout_planner"),
    path("dashboard/nutrition/", views_dashboard.nutrition_view, name="nutrition"),
    path("dashboard/chat/", views_dashboard.chat_view, name="chat"),
    path("dashboard/progress/", views_dashboard.progress_view, name="progress"),
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/progress/update/", views_dashboard.update_progress, name="update_progress"),
    path("api/progress/note/", views_dashboard.save_progress_note, name="save_progress_note"),
    path("dashboard/photo-locker/", views_dashboard.photo_locker_view, name="photo_locker"),
    path("dashboard/community-feed/", views_dashboard.community_feed_view, name="community_feed"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)