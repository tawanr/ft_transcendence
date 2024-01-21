from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField(required=False, max_length=150)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if len(username) < 6:
            raise forms.ValidationError("Username must be at least 4 characters long")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long")
        return password


class UploadAvatarForm(forms.Form):
    image = forms.ImageField()
