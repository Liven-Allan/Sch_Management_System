# Generated by Django 5.1.4 on 2025-01-10 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_alter_student_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='learner_lin',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
