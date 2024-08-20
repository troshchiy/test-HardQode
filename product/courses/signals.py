from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from users.models import Subscription, CustomUser, Balance


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """Распределение нового студента в группу курса."""

    if created:
        pass
        # TODO


@receiver(post_save, sender=CustomUser)
def post_save_user(sender, instance: CustomUser, created, **kwargs):
    """Создание баланса при создании нового пользователя."""
    if created:
        user_balance = Balance(user=instance)
        user_balance.save()