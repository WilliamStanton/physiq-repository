from django.db import models
from django.contrib.auth.models import User


from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.CharField(max_length=200, null=True, blank=True)
    height = models.CharField(max_length=200, null=True, blank=True)
    gender = models.CharField(
        max_length=50,
        choices=[("male", "Male"), ("female", "Female")],
        default="male",
    )
    fitness_goal = models.CharField(max_length=200, blank=True)
    activity_level = models.CharField(
        max_length=50,
        choices=[
            ("sedentary", "Sedentary"),
            ("light", "Lightly Active"),
            ("moderate", "Moderately Active"),
            ("active", "Active"),
            ("very_active", "Very Active"),
        ],
        default="moderate",
    )
    dietary_preferences = models.CharField(max_length=200, blank=True)
    allergies = models.CharField(max_length=200, blank=True)
    budget = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    schedule = models.JSONField(default=dict, blank=True, null=True)
    profile_completed = models.BooleanField(default=False)

    def is_complete(self):
        required = [self.age, self.height, self.weight, self.fitness_goal]
        return all(bool(x) for x in required)

    def __str__(self):
        return self.user.username


class Plan(models.Model):
    PLAN_TYPES = [
        ("workout", "Workout Plan"),
        ("nutrition", "Nutrition Plan"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plans")
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    plan_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_messages"
    )
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class DailyProgress(models.Model):
    WORKOUT_STATUS_CHOICES = [
        ("done", "Done"),
        ("missed", "Missed"),
        ("rest", "Rest"),
    ]

    NUTRITION_STATUS_CHOICES = [
        ("hit", "Hit"),
        ("missed", "Missed"),
        ("none", "None"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_progress")
    date = models.DateField()
    workout_status = models.CharField(
        max_length=10,
        choices=WORKOUT_STATUS_CHOICES,
        default="missed"
    )
    nutrition_status = models.CharField(
        max_length=10,
        choices=NUTRITION_STATUS_CHOICES,
        default="none"
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ["user", "date"]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class PhotoLocker(models.Model):
    VISIBILITY_CHOICES = [
        ("private", "Private"),
        ("public", "Public"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='user_photos/')
    note = models.TextField(blank=True, max_length=300)
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default="private"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.visibility.capitalize()}"

    @staticmethod
    def public_photos():
        """Return all public photos for the community feed."""
        return PhotoLocker.objects.filter(visibility="public").select_related("user").order_by("-uploaded_at")