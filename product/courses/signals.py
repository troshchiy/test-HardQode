from tokenize import group

from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from courses.models import Group
from users.models import Subscription, CustomUser, Balance


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """Распределение нового студента в группу курса."""

    if created:
        user = CustomUser.objects.get(pk=instance.student.pk)
        groups = Group.objects.filter(course=instance.course).annotate(u_count=Count('users')).order_by('u_count')
        # Если создано меньше 10 групп, создаем новую группу для равномерного распределения
        if groups.count() < 10:
            new_group = Group(name=f'Group {groups.count()+1}', course=instance.course)
            new_group.save()
        else:    # Если созданы все 10 групп, добавляем пользователя в наименее заполненную
            user.groups.add(groups[0])


@receiver(post_save, sender=CustomUser)
def post_save_user(sender, instance: CustomUser, created, **kwargs):
    """Создание баланса при создании нового пользователя."""
    if created:
        user_balance = Balance(user=instance)
        user_balance.save()