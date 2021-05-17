from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (AdminAccountsView,
                    AddToCartView,
                    AdminPurchasesView,
                    CancelPurchaseView,
                    CheckoutView,
                    ConfirmView,
                    AdminDepositsView,
                    AdminProductsView,
                    CustomLoginView,
                    IndexView,
                    ProfileView,
                    PurchaseView,
                    RedirectView)

urlpatterns = [
    path('admin/accounts/', AdminAccountsView.as_view(), name='admin-accounts'),
    path('admin/deposits/', AdminDepositsView.as_view(), name='admin-deposits'),
    path('admin/products/', AdminProductsView.as_view(), name='admin-products'),
    path('admin/purchases/',
         AdminPurchasesView.as_view(),
         name='admin-purchases'),

    path('add-to-cart/', AddToCartView.as_view(), name='add-to-cart'),
    path('cancel-purchase/<str:key>/',
         CancelPurchaseView.as_view(),
         name='cancel-purchase'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('confirm/', ConfirmView.as_view(), name='confirm'),
    path('login/',
         CustomLoginView.as_view(template_name='chiffee/login.html',
                                 redirect_authenticated_user=True),
         name='login'),
    path('logout/',
         auth_views.LogoutView.as_view(next_page='chiffee:index'),
         name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('purchase/', PurchaseView.as_view(), name='purchase'),
    path('redirect/', RedirectView.as_view(), name='redirect'),
    path('', IndexView.as_view(), name='index'),
]
