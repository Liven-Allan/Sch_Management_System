# Generated by Django 3.0.5 on 2024-12-28 18:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0005_auto_20241228_2145'),
    ]

    operations = [
        migrations.RenameField(
            model_name='teacher',
            old_name='assigned_class',
            new_name='assigned_classes',
        ),
    ]
