from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from Main.models import UserProfile, Plan, ChatMessage
from wrappers.azure_chat import llm
import json


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("/dashboard")
    return render(request, "landing.html")


@login_required
@require_http_methods(["POST"])
def chat_api(request):
    user_message = request.POST.get("message", "").strip()

    if not user_message:
        return JsonResponse({"error": "Empty message"}, status=400)

    user_profile = UserProfile.objects.get(user=request.user)
    user_name = request.user.get_full_name() or request.user.username

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

    # Get last 10 messages for conversation context
    recent_messages = ChatMessage.objects.filter(user=request.user)[:10]

    # Build conversation history
    conversation_history = []
    for msg in reversed(list(recent_messages)):
        conversation_history.append({"role": "user", "content": msg.message})
        conversation_history.append({"role": "assistant", "content": msg.response})

    # Add current message
    conversation_history.append({"role": "user", "content": user_message})

    # Build system prompt with user context
    system_prompt = f"""
    You are Physiq, an AI fitness & nutrition assistant helping {user_name}.
    Use the user's latest saved data when answering. Be conversational and remember previous messages.
    
    User Profile:
    - Age: {user_profile.age}
    - Height: {user_profile.height}
    - Weight: {user_profile.weight}
    - Goal: {user_profile.fitness_goal}
    - Activity Level: {user_profile.activity_level}
    - Dietary Preference: {user_profile.dietary_preferences}
    
    Latest Workout Plan:
    {json.dumps(latest_workout.plan_data, indent=2) if latest_workout else "None saved yet."}
    
    Latest Nutrition Plan:
    {json.dumps(latest_nutrition.plan_data, indent=2) if latest_nutrition else "None saved yet."}
    """

    try:
        # Call AI with conversation history
        response = llm(conversation_history, system_message=system_prompt)

        # Save message and response to database
        ChatMessage.objects.create(
            user=request.user, message=user_message, response=response
        )

        return JsonResponse({"response": response})

    except Exception as e:
        print(f"AI Error: {e}")
        return JsonResponse({"error": "Failed to get AI response"}, status=500)
