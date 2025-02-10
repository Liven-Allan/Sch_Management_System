# Generated by Django 5.1.5 on 2025-01-25 18:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0011_configuration'),
        ('student', '0007_remove_studentfee_amount_paid_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year_name', models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term_name', models.CharField(max_length=20)),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='terms', to='student.academicyear')),
            ],
            options={
                'unique_together': {('academic_year', 'term_name')},
            },
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.academicyear')),
                ('assigned_class', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='quiz.class')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.student')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.term')),
            ],
            options={
                'unique_together': {('student', 'academic_year', 'term', 'assigned_class')},
            },
        ),
    ]
