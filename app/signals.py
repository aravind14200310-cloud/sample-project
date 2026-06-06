from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Category, Profile


DEFAULT_CATEGORIES = [
    ('Salary', 'income'),
    ('Gift', 'income'),
    ('Business', 'income'),
    ('Food', 'expense'),
    ('Transport', 'expense'),
    ('Shopping', 'expense'),
    ('Education', 'expense'),
    ('Entertainment', 'expense'),
    ('Bills', 'expense'),
    ('Healthcare', 'expense'),
    ('Others', 'expense'),
]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        for name, category_type in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(
                name=name,
                category_type=category_type,
                user=instance,
            )
