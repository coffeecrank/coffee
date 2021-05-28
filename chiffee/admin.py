import django.contrib.auth.models
from django.contrib import admin

from .models import Deposit, Employee, Product, Purchase, User


# Register your models here.

class DepositAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'date']


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance']


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'active']


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'total_price', 'date']


class UserAdmin(admin.ModelAdmin):
    list_display = ['username',
                    'last_name',
                    'first_name',
                    'email',
                    'is_staff',
                    'is_superuser',
                    'is_active']


admin.site.register(Deposit, DepositAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.unregister(django.contrib.auth.models.User)
admin.site.register(User, UserAdmin)
