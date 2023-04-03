from django import forms
from .models import Task
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm



class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'

class TaskDescriptionForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('description',)
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'cols': 40 })
        }

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists, try another one...")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")


class UserUpdateForm(UserChangeForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('Email address must be unique')
        return email
