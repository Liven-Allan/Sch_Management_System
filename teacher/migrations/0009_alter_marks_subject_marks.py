# Generated by Django 5.1.4 on 2024-12-31 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0008_auto_20241231_0134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marks',
            name='subject_marks',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
