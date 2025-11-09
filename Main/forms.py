from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import UserProfile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
            }
        ),
    )
    password = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
    )


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
    )
    password2 = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "John Doe",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "john.doe@gmail.com",
                }
            ),
        }
        help_texts = {"username": ""}

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("That email is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


FITNESS_GOAL_CHOICES = [
    ("gain_muscle", "Gain Muscle"),
    ("lose_weight", "Lose Weight"),
    ("maintain", "Maintain Shape"),
]


class UserProfileForm(forms.ModelForm):
    fitness_goal = forms.ChoiceField(
        choices=FITNESS_GOAL_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "d-none"}),
        required=False,
    )
    schedule = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = UserProfile
        exclude = ("user", "profile_completed")
        widgets = {
            "age": forms.NumberInput(attrs={"class": "form-control", "placeholder": "18"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "height": forms.TextInput(attrs={"class": "form-control", "placeholder": "5'9"}),
            "weight": forms.TextInput(attrs={"class": "form-control", "placeholder": "165 lbs"}),
            "activity_level": forms.Select(attrs={"class": "form-select"}),
            "dietary_preferences": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Vegetarian"}
            ),
            "allergies": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Peanuts"}
            ),
            "budget": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "250", "step": "25"}
            ),
        }

    def clean_fitness_goal(self):
        val = self.cleaned_data.get("fitness_goal") or ""
        allowed = {c[0] for c in self.fields["fitness_goal"].choices}
        if val and val not in allowed:
            raise forms.ValidationError("Invalid fitness goal.")
        return val