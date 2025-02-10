from django.db import models
from django.contrib.auth.models import User
import json

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/Teacher/', null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)
    assigned_classes = models.ManyToManyField('quiz.Class', blank=True, related_name='other_teachers')  # Use string reference
    assigned_subjects = models.ManyToManyField('quiz.Subject', blank=True)
    status = models.BooleanField(default=False)
    salary = models.PositiveIntegerField(null=True)

    @property
    def get_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return self.user.first_name

# Marks model
class Marks(models.Model):
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE)
    exam = models.ForeignKey('quiz.Exam', null=True, blank=True, on_delete=models.CASCADE)
    test = models.ForeignKey('quiz.Test', null=True, blank=True, on_delete=models.CASCADE)
    
    # Use JSONField for subject_marks
    subject_marks = models.JSONField(null=True, blank=True)

    def __str__(self):
       if self.exam:
          return f"{self.student.get_name} - {self.exam.year} {self.exam.term} marks"
       elif self.test:
          return f"{self.student.get_name} - {self.test.year} {self.test.month} {self.test.term} test marks"
       else:
          return f"{self.student.get_name} - Marks without exam or test"




"""
class Teacher(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/Teacher/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    status= models.BooleanField(default=False)
    salary=models.PositiveIntegerField(null=True)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_instance(self):
        return self
    def __str__(self):
        return self.user.first_name
"""
