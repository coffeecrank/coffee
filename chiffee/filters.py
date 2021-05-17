import django_filters
from django import forms
from django.contrib.auth.models import User
from django_filters import widgets

from .models import Product, Purchase


def get_full_names():
    full_names = ()
    users = User.objects.all().order_by('last_name', 'first_name')

    for user in users:
        full_names += (user.pk, f'{user.last_name}, {user.first_name}'),

    return full_names


class DateRangeWidget(widgets.RangeWidget):
    template_name = 'chiffee/date-range-widget.html'


class PurchaseFilter(django_filters.FilterSet):
    username = django_filters.ChoiceFilter(
        field_name='user',
        choices=get_full_names(),
        widget=forms.Select(attrs={'id': 'grid-search-username'}))
    product = django_filters.ModelChoiceFilter(
        field_name='product',
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'id': 'grid-search-product'}))
    date_range = django_filters.DateRangeFilter(
        field_name='date',
        widget=forms.Select(attrs={'id': 'grid-search-date-range'}))
    date_from_to = django_filters.DateFromToRangeFilter(
        field_name='date',
        widget=DateRangeWidget(attrs={'id': 'grid-search-date-from-to',
                                      'type': 'date'}))

    class Meta:
        model = Purchase
        fields = ['user', 'product', 'date']
