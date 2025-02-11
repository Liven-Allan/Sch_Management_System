# Generated by Django 5.1.4 on 2025-01-24 11:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0011_configuration'),
        ('student', '0005_student_learner_lin'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_fee', models.DecimalField(decimal_places=2, max_digits=10)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('balance', models.DecimalField(decimal_places=2, editable=False, max_digits=10)),
                ('last_payment_date', models.DateField(blank=True, null=True)),
                ('assigned_class', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='quiz.class')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fee_record', to='student.student')),
            ],
        ),
    ]
