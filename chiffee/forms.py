from django import forms

from .models import Product, User


class DepositForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(),
                                  label='Benutzer',
                                  empty_label='',)
    deposit = forms.DecimalField(initial=0,
                                 label='Anzahlung')


class ActiveProductsForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(active=True).order_by('category',
                                                              'name'),
        label='',
        empty_label='')


class InactiveProductsForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(active=False),
        label='',
        empty_label='',
        widget=forms.Select(attrs={'id': 'inactive-products'}))


class PictureForm(forms.Form):
    picture = forms.ImageField(
        widget=forms.FileInput(attrs={'accept': 'image/*',
                                      'id': 'profile-picture-upload',
                                      'name': 'upload',
                                      'onchange': 'form.submit();'}),
        label='',
        required=False)
