from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from education.models import StudentProfile



class StudentRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit)

        StudentProfile.objects.create(user=user)

        return user


class TeacherRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit)

        # Педагог НЕ одобрен по умолчанию
        user.is_approved = False
        user.save()

        return user
