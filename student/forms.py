from django import forms
from django.contrib.auth.models import User
from .models import AcademicYear, Enrollment, Student, Payment, StudentFee, Term
from quiz.models import Class, Subject

class StudentUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {'password': forms.PasswordInput()}

class StudentForm(forms.ModelForm):
    # Ensure that assigned_subjects is a ManyToManyField and rendered as a multiple selection field
    assigned_subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),  # Fetch all subjects
        widget=forms.CheckboxSelectMultiple,  # Or you can use forms.SelectMultiple if you want a dropdown
        required=False  # Optional, depending on whether the field is mandatory
    )
    
    class Meta:
        model = Student
        fields = ['address', 'mobile', 'profile_pic', 'assigned_class', 'assigned_subjects', 'learner_lin']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_amount', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'})
        }

class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['year_name']

class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['term_name']

class EnrollmentForm(forms.Form):
    assigned_class = forms.ModelChoiceField(
        queryset=Class.objects.all(), 
        label="Select Class"
    )
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(), 
        widget=forms.CheckboxSelectMultiple,  # Allows multiple selections
        label="Select Students"
    )
