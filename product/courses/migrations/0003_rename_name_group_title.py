# Generated by Django 4.2.10 on 2024-08-20 18:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_course_is_available_course_price_group_course_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='name',
            new_name='title',
        ),
    ]
