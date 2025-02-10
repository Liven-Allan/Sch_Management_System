from django import forms
from django.contrib.auth.models import User
from . import models

class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

class TeacherSalaryForm(forms.Form):
    salary=forms.IntegerField()

class CourseForm(forms.ModelForm):
    class Meta:
        model=models.Course
        fields=['course_name','question_number','total_marks']

class QuestionForm(forms.ModelForm):
    
    #this will show dropdown __str__ method course model is shown on html so override it
    #to_field_name this will fetch corresponding value  user_id present in course model and return it
    courseID=forms.ModelChoiceField(queryset=models.Course.objects.all(),empty_label="Course Name", to_field_name="id")
    class Meta:
        model=models.Question
        fields=['marks','question','option1','option2','option3','option4','answer']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'cols': 50})
        }

# class
class ClassForm(forms.ModelForm):
    class Meta:
        model = models.Class
        fields = ['class_name']  # Add more fields if necessary
        widgets = {
            'class_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class Name'})
        }

# subject
class SubjectForm(forms.ModelForm):
    class Meta:
        model = models.Subject
        fields = ['class_name', 'subject_name']
        widgets = {
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'subject_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Name'}),
        }

# exam
class ExamForm(forms.ModelForm):
    class Meta:
        model = models.Exam
        fields = ['year', 'term']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
        }

# test
class TestForm(forms.ModelForm):
    class Meta:
        model = models.Test
        fields = ['year', 'month', 'term']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
            'month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Month'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
        }
