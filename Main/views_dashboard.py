from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import random
import json
from django.contrib import messages
from datetime import datetime, timedelta

from django.utils import timezone

from Main.models import UserProfile, Plan, ChatMessage, DailyProgress, PhotoLocker
from prompts import (
    build_workout_prompt,
    WORKOUT_SYSTEM_MESSAGE,
    build_nutrition_prompt,
    NUTRITION_SYSTEM_MESSAGE,
    generate_coach_summary,
)
from wrappers.azure_chat import llm


@login_required
def dashboard_view(request):
    return render(
        request,
        "dashboard/main.html",
    )


def _find_today_block(week_plan, weekday_name):
    """Find today's block by day name. Falls back to first entry if not found."""
    if not week_plan:
        return None
    for d in week_plan:
        if str(d.get("day", "")).strip().lower() == weekday_name.strip().lower():
            return d
    return week_plan[0]


@login_required
def overview_view(request):
    now_local = timezone.localtime()
    weekday_name = now_local.strftime("%A")

    try:
        # Linux / macOS use %-d (day without leading zero)
        pretty_date = now_local.strftime("%A, %b %-d")
    except ValueError:
        # Windows fallback uses %#d instead
        pretty_date = now_local.strftime("%A, %b %#d")

    latest_workout = (
        Plan.objects.filter(user=request.user, plan_type="workout")
        .order_by("-created_at")
        .first()
    )
    latest_nutrition = (
        Plan.objects.filter(user=request.user, plan_type="nutrition")
        .order_by("-created_at")
        .first()
    )

    workout_today = None
    nutrition_today = None
    daily_target = None
    macro_targets = {"protein": None, "carbs": None, "fat": None}
    meals_json = "[]"

    if latest_workout and isinstance(latest_workout.plan_data, dict):
        week_plan = latest_workout.plan_data.get("week_plan", [])
        workout_today = _find_today_block(week_plan, weekday_name)

    if latest_nutrition and isinstance(latest_nutrition.plan_data, dict):
        ndata = latest_nutrition.plan_data

        week_plan = ndata.get("week_plan", [])
        nutrition_today = _find_today_block(week_plan, weekday_name)

        daily_targets = ndata.get("daily_targets", {})
        daily_target = daily_targets.get("calorie_target")

        macro_targets = {
            "protein": daily_targets.get("protein_g"),
            "carbs": daily_targets.get("carbs_g"),
            "fat": daily_targets.get("fat_g"),
        }

        if nutrition_today:
            try:
                meals_json = json.dumps(nutrition_today.get("meals", []))
            except Exception:
                meals_json = "[]"

    cache_key = f"coach_summary:{request.user.id}:{now_local.date()}"
    coach_banner = cache.get(cache_key)

    if not coach_banner:
        coach_banner = "Focus on consistency today — progress compounds."
        try:
            coach_banner = generate_coach_summary(
                request.user.username,
                workout_today,
                nutrition_today,
                {
                    "protein": macro_targets.get("protein"),
                    "carbs": macro_targets.get("carbs"),
                    "fat": macro_targets.get("fat"),
                    "calories": daily_target,
                },
            )
        except Exception:
            pass

        tomorrow = now_local + timezone.timedelta(days=1)
        midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = int((midnight - now_local).total_seconds())

        cache.set(cache_key, coach_banner, timeout=seconds_until_midnight)

    today = timezone.localdate()
    new_posts_today = PhotoLocker.objects.filter(
        visibility="public",
        uploaded_at__date=today
    ).count()

    return render(
        request,
        "dashboard/partials/overview.html",
        {
            "today_str": pretty_date,
            "coach_banner": coach_banner,
            "workout_today": workout_today,
            "nutrition_today": nutrition_today,
            "nutrition_meals_json": meals_json,
            "macro_targets": macro_targets,
            "daily_calorie_target": daily_target,
            "view_name": "Overview",
            "new_posts_today": new_posts_today,
        },
    )


@login_required
def workout_view(request):
    user = UserProfile.objects.get(user=request.user)

    latest_plan = (
        Plan.objects.filter(user=request.user, plan_type="workout")
        .order_by("-created_at")
        .first()
    )

    if request.method == "POST":
        if request.headers.get("Content-Type") == "application/json":
            data = json.loads(request.body.decode("utf-8"))
            goal = data.get("goal", "")
            schedule = data.get("schedule", "")
            notes = data.get("notes", "")

        user_prompt = build_workout_prompt(
            user_profile=user,
            current_goal=goal,
            schedule=schedule,
            notes=notes
        )
        response_json = llm(user_prompt, system_message=WORKOUT_SYSTEM_MESSAGE)

        Plan.objects.create(
            user=request.user,
            plan_type="workout",
            plan_data=response_json
        )

        latest_plan = Plan.objects.filter(user=request.user, plan_type="workout").order_by('-created_at').first()

    if not latest_plan:
        user_prompt = build_workout_prompt(user_profile=user, current_goal="", schedule="", notes="")
        response_json = llm(user_prompt, system_message=WORKOUT_SYSTEM_MESSAGE)
        latest_plan = Plan.objects.create(
            user=request.user, plan_type="workout", plan_data=response_json
        )

    return render(request, "dashboard/partials/workout.html", {
        "plan": latest_plan.plan_data,
        "view_name": "Workout Planner"
    })


@login_required
def nutrition_view(request):
    user = UserProfile.objects.get(user=request.user)
    latest_plan = (
        Plan.objects.filter(user=request.user, plan_type="nutrition")
        .order_by("-created_at")
        .first()
    )

    if request.method == "POST":
        user_prompt = build_nutrition_prompt(
            user_profile=user, current_goal="", notes=""
        )
        response_json = llm(user_prompt, system_message=NUTRITION_SYSTEM_MESSAGE)
        Plan.objects.create(
            user=request.user, plan_type="nutrition", plan_data=response_json
        )
        latest_plan = (
            Plan.objects.filter(user=request.user, plan_type="nutrition")
            .order_by("-created_at")
            .first()
        )

    if not latest_plan:
        user_prompt = build_nutrition_prompt(
            user_profile=user, current_goal="", notes=""
        )
        response_json = llm(user_prompt, system_message=NUTRITION_SYSTEM_MESSAGE)
        latest_plan = Plan.objects.create(
            user=request.user, plan_type="nutrition", plan_data=response_json
        )

    plan = latest_plan.plan_data

    for day in plan["week_plan"]:
        day["meals_json"] = json.dumps(day["meals"])

    return render(
        request,
        "dashboard/partials/nutrition.html",
        {"plan": plan, "view_name": "Nutrition Planner"},
    )


def calculate_streaks(user):
    """Calculate current and best streaks for workout, nutrition, and overall."""
    today = timezone.localtime().date()

    # Get all entries
    entries = DailyProgress.objects.filter(user=user).order_by('-date')
    progress_dict = {e.date: e for e in entries}

    print(f"DEBUG: Today is {today}")
    print(f"DEBUG: Found {len(progress_dict)} entries")

    # Initialize counters
    workout_current = 0
    workout_best = 0
    nutrition_current = 0
    nutrition_best = 0
    overall_current = 0
    overall_best = 0

    # Calculate CURRENT streaks (backwards from today)
    current_date = today

    # Workout current streak
    print(f"DEBUG: Calculating workout streak...")
    while current_date in progress_dict:
        entry = progress_dict[current_date]
        print(f"  {current_date}: workout={entry.workout_status}")
        if entry.workout_status == "done":
            workout_current += 1
            current_date -= timedelta(days=1)
        else:
            break

    print(f"DEBUG: Workout current streak: {workout_current}")

    # Reset for nutrition
    current_date = today
    print(f"DEBUG: Calculating nutrition streak...")
    while current_date in progress_dict:
        entry = progress_dict[current_date]
        print(f"  {current_date}: nutrition={entry.nutrition_status}")
        if entry.nutrition_status == "hit":
            nutrition_current += 1
            current_date -= timedelta(days=1)
        else:
            break

    print(f"DEBUG: Nutrition current streak: {nutrition_current}")

    # Reset for overall
    current_date = today
    print(f"DEBUG: Calculating overall streak...")
    while current_date in progress_dict:
        entry = progress_dict[current_date]
        print(f"  {current_date}: workout={entry.workout_status}, nutrition={entry.nutrition_status}")
        if entry.workout_status == "done" and entry.nutrition_status == "hit":
            overall_current += 1
            current_date -= timedelta(days=1)
        else:
            break

    print(f"DEBUG: Overall current streak: {overall_current}")

    # Calculate BEST streaks (scan past 365 days)
    start_date = today - timedelta(days=365)
    current_date = start_date

    workout_temp = 0
    nutrition_temp = 0
    overall_temp = 0

    while current_date <= today:
        entry = progress_dict.get(current_date)

        if entry and entry.workout_status == "done":
            workout_temp += 1
            workout_best = max(workout_best, workout_temp)
        else:
            workout_temp = 0

        if entry and entry.nutrition_status == "hit":
            nutrition_temp += 1
            nutrition_best = max(nutrition_best, nutrition_temp)
        else:
            nutrition_temp = 0

        if entry and entry.workout_status == "done" and entry.nutrition_status == "hit":
            overall_temp += 1
            overall_best = max(overall_best, overall_temp)
        else:
            overall_temp = 0

        current_date += timedelta(days=1)

    workout_best = max(workout_best, workout_current)
    nutrition_best = max(nutrition_best, nutrition_current)
    overall_best = max(overall_best, overall_current)

    print(
        f"DEBUG: Final streaks - workout: {workout_current}/{workout_best}, nutrition: {nutrition_current}/{nutrition_best}, overall: {overall_current}/{overall_best}")

    return {
        "workout_current": workout_current,
        "workout_best": workout_best,
        "nutrition_current": nutrition_current,
        "nutrition_best": nutrition_best,
        "overall_current": overall_current,
        "overall_best": overall_best,
    }


@login_required
def progress_view(request):
    today = timezone.localtime().date()

    week_start = today - timedelta(days=today.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    progress_data = []
    for date in week_dates:
        try:
            entry = DailyProgress.objects.get(user=request.user, date=date)
            progress_data.append({
                'date': date,
                'day_name': date.strftime('%a'),
                'day_num': date.day,
                'workout_status': entry.workout_status,
                'nutrition_status': entry.nutrition_status,
                'notes': entry.notes,
                'is_today': date == today,
            })
        except DailyProgress.DoesNotExist:
            progress_data.append({
                'date': date,
                'day_name': date.strftime('%a'),
                'day_num': date.day,
                'workout_status': 'missed',
                'nutrition_status': 'none',
                'notes': '',
                'is_today': date == today,
            })

    streaks = calculate_streaks(request.user)

    return render(
        request,
        "dashboard/partials/progress.html",
        {
            "view_name": "Progress",
            "week_data": progress_data,
            "streaks": streaks,
        }
    )


@login_required
@require_http_methods(["POST"])
def update_progress(request):
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        workout_status = data.get('workout_status')
        nutrition_status = data.get('nutrition_status')

        if not date_str:
            return JsonResponse({'error': 'Date is required'}, status=400)

        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        entry, created = DailyProgress.objects.get_or_create(
            user=request.user,
            date=date,
            defaults={
                'workout_status': workout_status or 'missed',
                'nutrition_status': nutrition_status or 'none',
            }
        )

        if not created:
            if workout_status:
                entry.workout_status = workout_status
            if nutrition_status:
                entry.nutrition_status = nutrition_status
            entry.save()

        streaks = calculate_streaks(request.user)

        return JsonResponse({
            'success': True,
            'workout_status': entry.workout_status,
            'nutrition_status': entry.nutrition_status,
            'streaks': streaks,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_progress_note(request):
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        notes = data.get('notes', '')

        if not date_str:
            return JsonResponse({'error': 'Date is required'}, status=400)

        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        entry, created = DailyProgress.objects.get_or_create(
            user=request.user,
            date=date,
            defaults={'notes': notes}
        )

        if not created:
            entry.notes = notes
            entry.save()

        return JsonResponse({
            'success': True,
            'notes': entry.notes,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def chat_view(request):
    prompt_suggestions = [
        "What are some effective exercises for building muscle?",
        "How can I improve my cardio endurance?",
        "What should I eat before a workout?",
        "Can you suggest a 30-minute home workout?",
        "How do I stay motivated to exercise regularly?",
        "What are good post-workout meals?",
        "How many calories should I eat to lose weight?",
        "What's the best way to track my fitness progress?",
        "How can I avoid workout injuries?",
        "What supplements do you recommend?",
        "How do I build a balanced meal plan?",
        "What are some healthy snack options?",
    ]

    selected_prompts = random.sample(
        prompt_suggestions, min(5, len(prompt_suggestions))
    )

    chat_history = ChatMessage.objects.filter(user=request.user)[:50]

    return render(
        request,
        "dashboard/partials/chat.html",
        {
            "view_name": "Coach Bot",
            "prompt_suggestions": selected_prompts,
            "chat_history": reversed(list(chat_history)),
        },
    )


@login_required
def photo_locker_view(request):
    photos = PhotoLocker.objects.filter(user=request.user).order_by("-uploaded_at")

    if request.method == "POST":
        image = request.FILES.get("image")
        if not image:
            messages.error(request, "Please select an image to upload.")
            return redirect("photo_locker")

        note = request.POST.get("note", "").strip()
        visibility = request.POST.get("visibility", "private")

        PhotoLocker.objects.create(
            user=request.user,
            image=image,
            note=note,
            visibility=visibility
        )

        return redirect("/dashboard/?tab=photo-locker")

    return render(
        request,
        "dashboard/partials/photo_locker.html",
        {"photos": photos, "view_name": "Photo Locker"}
    )

@login_required
def community_feed_view(request):
    posts = PhotoLocker.public_photos()
    return render(request, "dashboard/partials/community_feed.html", {"posts": posts, "view_name": "Community Feed"})
