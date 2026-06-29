from django import forms
from django.contrib.auth import get_user_model
from .models import User, Profile, Project, Task, Comment, Attachment

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role']

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'email', 'department', 'designation', 'phone_number', 'profile_image']

class ProjectForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'members']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude Admins from being assigned as members
        self.fields['members'].queryset = User.objects.exclude(role='Admin')

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assigned_user', 'priority', 'start_date', 'due_date', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        project_qs = kwargs.pop('project_qs', None)
        super().__init__(*args, **kwargs)
        if project_qs is not None:
            self.fields['project'].queryset = project_qs
        # Filter assigned_user to non-admins
        self.fields['assigned_user'].queryset = User.objects.exclude(role='Admin')

class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a comment or reply...'}),
        }

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']
