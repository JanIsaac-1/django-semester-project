from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Application, Job


class UserRegisterForm(UserCreationForm):
    """Registration form requiring a unique email address."""

    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class JobForm(forms.ModelForm):
    """Form for creating or updating a job or internship listing."""

    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'job_type', 'description']


class ApplicationForm(forms.ModelForm):
    """Form for submitting an application to a job listing."""

    class Meta:
        model = Application
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write a brief cover letter...'}),
        }


class ApplicationStatusForm(forms.ModelForm):
    """Form for job owners to update an application's review status."""

    class Meta:
        model = Application
        fields = ['status']
