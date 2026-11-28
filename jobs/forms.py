from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Application, Job


def _validate_unique_email(email, exclude_user_id=None):
    """Ensure the provided email is not already assigned to another user."""
    cleaned = email.strip()
    qs = User.objects.filter(email__iexact=cleaned)
    if exclude_user_id is not None:
        qs = qs.exclude(pk=exclude_user_id)
    if qs.exists():
        raise forms.ValidationError('An account with this email already exists.')
    return cleaned


class UserRegisterForm(UserCreationForm):
    """Registration form requiring a unique email address."""

    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        return _validate_unique_email(self.cleaned_data.get('email', ''))


class UserProfileForm(forms.ModelForm):
    """Form allowing users to update their account details."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
        }

    def clean_email(self):
        return _validate_unique_email(
            self.cleaned_data.get('email', ''),
            exclude_user_id=self.instance.pk,
        )


class UserLoginForm(AuthenticationForm):
    """Login form accepting either a username or email address."""

    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'Enter your username or email',
        }),
    )


class JobForm(forms.ModelForm):
    """Form for creating or updating a job or internship listing."""

    class Meta:
        model = Job
        fields = [
            'title',
            'company',
            'location',
            'job_type',
            'work_mode',
            'salary',
            'application_deadline',
            'description',
            'requirements',
        ]
        labels = {
            'title': 'Job Title',
            'company': 'Company / Organization',
            'location': 'Location',
            'job_type': 'Employment Type',
            'work_mode': 'Work Mode',
            'salary': 'Salary / Stipend (Optional)',
            'application_deadline': 'Application Deadline (Optional)',
            'description': 'Role Description',
            'requirements': 'Requirements & Skills (Optional)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Junior Python / Django Developer Intern'}),
            'company': forms.TextInput(attrs={'placeholder': 'e.g. TechPulse Solutions'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Nairobi, Kenya'}),
            'salary': forms.TextInput(attrs={'placeholder': 'e.g. KSh 30,000 / month or Unpaid'}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe day-to-day responsibilities, team structure, and what the candidate will learn...',
            }),
            'requirements': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'List key skills, coursework, or qualifications (one per line)...',
            }),
        }


class ApplicationForm(forms.ModelForm):
    """Form for submitting an application with an optional CV upload."""

    class Meta:
        model = Application
        fields = ['cover_letter', 'cv']
        labels = {
            'cv': 'Upload CV (PDF, DOC, or DOCX)',
        }
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write a brief cover letter...'}),
            'cv': forms.ClearableFileInput(attrs={'accept': '.pdf,.doc,.docx'}),
        }

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if not cv:
            return cv
        allowed_extensions = ('.pdf', '.doc', '.docx')
        if not cv.name.lower().endswith(allowed_extensions):
            raise forms.ValidationError('Only PDF, DOC, or DOCX files are allowed.')
        if cv.size > 5 * 1024 * 1024:
            raise forms.ValidationError('CV file size must be 5 MB or smaller.')
        return cv


class ApplicationStatusForm(forms.ModelForm):
    """Form for job owners to update an application's review status."""

    class Meta:
        model = Application
        fields = ['status']
