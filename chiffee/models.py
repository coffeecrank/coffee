import os

import django.contrib.auth.models
from django.db import models
from django_resized import ResizedImageField

CATEGORIES = ((1, 'Trinken'), (2, 'Snacks'), (3, 'Eis'))
USER_PICTURES_DIR = 'user-pictures'


def create_picture_path(instance, filename):
    return os.path.join(USER_PICTURES_DIR,
                        f'{instance.user.pk}.{filename.rsplit(".", 1)[1]}')


class User(django.contrib.auth.models.User):
    class Meta:
        proxy = True
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name}, {self.first_name}'


class Deposit(models.Model):
    class Meta:
        ordering = ['-date', 'user']

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    date = models.DateTimeField(auto_now_add=True)


class Employee(models.Model):
    class Meta:
        ordering = ['user']

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(default=0.0, decimal_places=2, max_digits=9)
    picture = ResizedImageField(upload_to=create_picture_path,
                                null=True,
                                crop=['middle', 'center'])
    picture_placeholder = models.ImageField(
        default=os.path.join(USER_PICTURES_DIR, 'placeholder.jpg'))
    get_emails_deposits = models.BooleanField(default=True)
    get_emails_purchases = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.last_name}, {self.user.first_name}'


class Product(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=200)
    price = models.DecimalField(decimal_places=2, max_digits=9)
    category = models.IntegerField(choices=CATEGORIES)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    class Meta:
        ordering = ['user']

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.ImageField(null=True)


class Purchase(models.Model):
    class Meta:
        ordering = ['-date', 'user', 'product']

    user = models.ForeignKey(User, default=None, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    total_price = models.DecimalField(decimal_places=2, max_digits=9)
    date = models.DateTimeField()
    key = models.CharField(max_length=64)
