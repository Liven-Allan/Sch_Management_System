from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver

from student.models import Student

@receiver(post_save, sender=User)
def add_student_group(sender, instance, created, **kwargs):
    if created:  # If it's a new user
        student_group, created = Group.objects.get_or_create(name='TEACHER')
        instance.groups.add(student_group)

# class
class Class(models.Model):
    class_name = models.CharField(max_length=100)
    

    def __str__(self):
        return self.class_name
    
# subject
class Subject(models.Model):
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='subjects')
    subject_name = models.CharField(max_length=100)

    def __str__(self):
        return self.subject_name    

# exam
class Exam(models.Model):
    year = models.IntegerField()
    term = models.CharField(max_length=10, choices=[('I', 'Term I'), ('II', 'Term II'), ('III', 'Term III')])

    def __str__(self):
        return f"{self.year} - {self.term}"

# test
class Test(models.Model):
    year = models.IntegerField()
    month = models.CharField(max_length=20)
    term = models.CharField(max_length=10, choices=[('I', 'Term I'), ('II', 'Term II'), ('III', 'Term III')])

    def __str__(self):
        return f"{self.year} - {self.month} - {self.term}"
    
# configurations
class Configuration(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"    


#
class Course(models.Model):
   course_name = models.CharField(max_length=50)
   question_number = models.PositiveIntegerField()
   total_marks = models.PositiveIntegerField()
   def __str__(self):
        return self.course_name

class Question(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    marks=models.PositiveIntegerField()
    question=models.CharField(max_length=600)
    option1=models.CharField(max_length=200)
    option2=models.CharField(max_length=200)
    option3=models.CharField(max_length=200)
    option4=models.CharField(max_length=200)
    cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
    answer=models.CharField(max_length=200,choices=cat)

class Result(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    exam = models.ForeignKey(Course,on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)