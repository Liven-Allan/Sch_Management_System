from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/Student/', null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)
    assigned_class = models.ForeignKey('quiz.Class', on_delete=models.SET_NULL, null=True)  # Use string reference
    assigned_subjects = models.ManyToManyField('quiz.Subject', blank=True)
    learner_lin = models.CharField(max_length=50, null=True, blank=True)  # New field for Learner's LIN

    @property
    def get_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def get_learner_lin(self):
        # You can apply any formatting here if needed
        return self.learner_lin or "N/A"  # Return "N/A" if learner_lin is None or blank

    def __str__(self):
        return self.user.first_name
    
class AcademicYear(models.Model):
    year_name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.year_name

class Term(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    term_name = models.CharField(max_length=20)

    class Meta:
        unique_together = ('academic_year', 'term_name')

    def __str__(self):
        return f"{self.term_name} ({self.academic_year.year_name})"

class Enrollment(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    assigned_class = models.ForeignKey('quiz.Class', on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('student', 'academic_year', 'term', 'assigned_class')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assigned_class.class_name if self.assigned_class else 'Unassigned'}"

class StudentFee(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='fee_records')
    assigned_class = models.ForeignKey('quiz.Class', on_delete=models.SET_NULL, null=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)

    class Meta:
        unique_together = ('student', 'academic_year', 'term', 'assigned_class')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.balance = self.total_fee
        else:
            total_payments = sum(payment.payment_amount for payment in self.payments.all())
            self.balance = self.total_fee - Decimal(total_payments)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.academic_year.year_name if self.academic_year else 'No Year'} - {self.term.term_name if self.term else 'No Term'}"


class Payment(models.Model):
    student_fee = models.ForeignKey(StudentFee, on_delete=models.CASCADE, related_name='payments')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the associated StudentFee balance after saving a payment
        student_fee = self.student_fee
        total_payments = sum(payment.payment_amount for payment in student_fee.payments.all())
        student_fee.balance = student_fee.total_fee - Decimal(total_payments)
        student_fee.save()

    def __str__(self):
        return f"Payment of {self.payment_amount} on {self.payment_date} for {self.student_fee.student.user.get_full_name()}"    