# Generated by Django 4.2.10 on 2024-08-19 21:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_course_is_available_course_price_group_course_and_more'),
        ('users', '0002_balance_bonuses_balance_user_subscription_course_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribers', to='courses.course', verbose_name='Курс'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to=settings.AUTH_USER_MODEL, verbose_name='Студент'),
        ),
    ]