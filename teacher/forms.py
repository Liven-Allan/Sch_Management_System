from django import forms
from django.contrib.auth.models import User
from .models import Teacher, Marks
from quiz.models import Class

class TeacherUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password']
        widgets = {'password': forms.PasswordInput()}

class TeacherForm(forms.ModelForm):
    assigned_classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # You can use a dropdown if preferred
        required=False
    )

    class Meta:
        model = Teacher
        fields = ['address', 'mobile', 'profile_pic', 'assigned_classes']

# Marks
class MarksForm(forms.ModelForm):
    MARK_CHOICES = [
        ('exam', 'Exam Marks'),
        ('test', 'Test Marks'),
    ]
    marks_type = forms.ChoiceField(choices=MARK_CHOICES)
    exam_year = forms.ChoiceField(choices=[], required=False)  # Dynamic choice
    exam_term = forms.ChoiceField(choices=[], required=False)  # Dynamic choice
    test_month = forms.ChoiceField(choices=[], required=False)  # Dynamic choice
    test_term = forms.ChoiceField(choices=[('I', 'Term I'), ('II', 'Term II'), ('III', 'Term III')], required=False)  # Dynamic choice
    subject_marks = forms.JSONField(required=False)  # Handles the JSON data

    class Meta:
        model = Marks
        fields = ['marks_type', 'exam_year', 'exam_term', 'test_month', 'test_term', 'subject_marks']  # Add fields you need        

"""
class TeacherUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }

class TeacherForm(forms.ModelForm):
    class Meta:
        model=models.Teacher
        fields=['address','mobile','profile_pic']


"""
