import os
import secrets
from decimal import Decimal

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import OperationalError
from django.shortcuts import redirect, render, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from chiffee import forms
from coffee.settings import MEDIA_URL
from .filters import PurchaseFilter
from .forms import DepositForm, InactiveProductsForm
from .models import (CATEGORIES, Deposit, Employee, Product, Purchase,
                     USER_PICTURES_DIR, User)

EMAIL_ADDRESS = 'kaffeekasse@chi.uni-hannover.de'
EMAIL_SUBJECT = 'Kauf Kaffeekasse'

PAGES_TOTAL = 7


def count_shopping_cart(shopping_cart):
    if shopping_cart is None:
        return 0

    return sum(shopping_cart.values())


def generate_key():
    while True:
        key = secrets.token_hex(32)

        try:
            if not Purchase.objects.filter(key=key).exists():
                break
        except OperationalError:
            break

    return key


def get_current_page(page, pages_total):
    if page is not None:
        try:
            page = int(page)
        except ValueError:
            return None

        if page < 1:
            page = 1
        elif page > pages_total:
            page = pages_total

        current_page = page
    else:
        current_page = 1

    return current_page


def get_pages(current_page, pages_total):
    if pages_total <= PAGES_TOTAL:
        pages = [page for page in range(1, pages_total + 1)]
    else:
        pages_left = current_page - 1
        pages_right = pages_total - current_page
        pages = []

        if pages_left <= PAGES_TOTAL // 2:
            difference = PAGES_TOTAL // 2 - pages_left
            max_page_right = current_page + PAGES_TOTAL // 2 + difference - 2
            pages += [page for page in range(1, max_page_right + 1)]
            pages += ['next_page_section', pages_total]
        elif pages_right <= PAGES_TOTAL // 2:
            difference = PAGES_TOTAL // 2 - pages_right
            min_page_left = current_page - PAGES_TOTAL // 2 - difference + 2
            pages += [1, 'prev_page_section']
            pages += [page for page in range(min_page_left, pages_total + 1)]
        else:
            min_page_left = current_page - PAGES_TOTAL // 2 + 2
            max_page_right = current_page + PAGES_TOTAL // 2 - 2
            pages += [1, 'prev_page_section']
            pages += [page for page in range(min_page_left, max_page_right + 1)]
            pages += ['next_page_section', pages_total]

    return pages


def get_check(shopping_cart):
    check = 0

    for product_name, quantity in shopping_cart.items():
        product = Product.objects.get(name=product_name)
        check += product.price * quantity

    return check


def get_users():
    groups = ['prof', 'wimi', 'stud']
    users = User.objects.filter(groups__name__in=groups,
                                is_active=True).order_by('last_name',
                                                         'first_name')

    return users


def group_purchases_by_date(purchases):
    distinct_dates = set([purchase.date for purchase in purchases])
    purchases_grouped = []

    for date in sorted(distinct_dates, reverse=True):
        group = []

        for purchase in purchases:
            if purchase.date == date:
                group.append(purchase)

        purchases_grouped.append(group)

    return purchases_grouped


def purchase_products(shopping_cart, user, employee, url):
    now = timezone.now()
    key = generate_key()
    check = 0
    purchases = ''

    for product_name, quantity in shopping_cart.items():
        product = Product.objects.get(name=product_name)
        total_price = product.price * quantity
        check += total_price
        purchases += f'{quantity} {product.name} für €{total_price}\n'
        Purchase.objects.create(user=user,
                                product=product,
                                quantity=quantity,
                                total_price=total_price,
                                date=now,
                                key=key)

    employee.balance -= check
    employee.save()

    url += reverse('chiffee:cancel-purchase', kwargs={'key': key})

    if employee.get_emails_purchases:
        message = (f'Hallo {user.first_name} {user.last_name}!\n\n'
                   f'Sie haben diese Produkte gekauft:\n'
                   f'{purchases}\n'
                   f'Ihr aktueller Kontostand beträgt €{employee.balance}.\n\n'
                   f'Wenn Sie diesen Kauf stornieren möchten, '
                   f'klicken Sie bitte hier: {url}')

        send_mail(EMAIL_SUBJECT,
                  message,
                  EMAIL_ADDRESS,
                  [user.email],
                  fail_silently=False)


class AdminAccountsView(View):
    template_name = 'chiffee/admin-accounts.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda user: user.is_superuser))
    def get(self, request, *args, **kwargs):
        users = get_users()
        paginator = Paginator(users, 10)

        current_page = get_current_page(request.GET.get('page'),
                                        paginator.num_pages)

        context = {'current_page': current_page,
                   'pages': get_pages(current_page, paginator.num_pages),
                   'shopping_cart_counter': count_shopping_cart(
                       request.session.get('shopping_cart')),
                   'users': paginator.page(current_page).object_list}

        return render(request, self.template_name, context)


class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        if 'product' not in request.POST:
            return RedirectView.as_view()(request)
        try:
            product = Product.objects.get(name=request.POST['product'])
        except Product.DoesNotExist:
            return RedirectView.as_view()(request)

        shopping_cart = request.session.get('shopping_cart', {})

        if product.name in shopping_cart:
            shopping_cart[product.name] += 1
        else:
            shopping_cart[product.name] = 1

        request.session['shopping_cart'] = shopping_cart

        return redirect(reverse('chiffee:index'))


class AdminDepositsView(View):
    template_name = 'chiffee/admin-deposits.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda user: user.is_superuser))
    def get(self, request, *args, **kwargs):
        context = {'form': forms.DepositForm(),
                   'shopping_cart_counter': count_shopping_cart(
                       request.session.get('shopping_cart'))}

        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda user: user.is_superuser))
    @method_decorator(user_passes_test(lambda user: user.is_superuser))
    def post(self, request, *args, **kwargs):
        form = DepositForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data['user']
            deposit = form.cleaned_data['deposit']

            if deposit != 0:
                try:
                    employee = user.employee
                except Employee.DoesNotExist:
                    employee = Employee.objects.create(user=user)

                employee.balance += Decimal(deposit)
                employee.save()

                Deposit.objects.create(user=user, amount=deposit)

                if employee.get_emails_deposits:
                    message = (f'Hallo {user.first_name} {user.last_name}!\n\n'
                               f'Geld wurde auf Ihr Konto eingezahlt: '
                               f'€{deposit}\n\n'
                               f'Ihr aktueller Kontostand beträgt '
                               f'€{employee.balance}.')

                    send_mail(EMAIL_SUBJECT,
                              message,
                              EMAIL_ADDRESS,
                              [user.email],
                              fail_silently=False)

                return RedirectView.as_view()(request, success=True)

        return RedirectView.as_view()(request)


class AdminProductsView(View):
    template_name = 'chiffee/admin-products.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda user: user.is_superuser))
    def get(self, request, *args, **kwargs):
        active_products = Product.objects.filter(
            active=True).order_by('category', 'name')
        paginator = Paginator(active_products, 10)

        current_page = get_current_page(request.GET.get('page'),
                                        paginator.num_pages)

        context = {'categories': CATEGORIES,
                   'current_page': current_page,
                   'pages': get_pages(current_page, paginator.num_pages),
                   'active_products': paginator.page(current_page).object_list,
                   'shopping_cart_counter': count_shopping_cart(
                       request.session.get('shopping_cart'))}

        if len(Product.objects.filter(active=False)) > 0:
            context['inactive_products'] = InactiveProductsForm()

        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda user: user.is_superuser))
    def post(self, request, *args, **kwargs):
        if 'product' in request.POST and 'restore' not in request.POST:
            try:
                product = Product.objects.get(name=request.POST['product'])
            except Product.DoesNotExist:
                return RedirectView.as_view()(request)

            if product.name not in request.POST:
                return RedirectView.as_view()(request)

            try:
                price = request.POST[product.name]
                price = price.replace('€', '').replace(',', '.')
                price = float(price)
            except ValueError:
                return RedirectView.as_view()(request)

            product.price = price
            product.save()
        elif 'restore' in request.POST:
            try:
                product = Product.objects.get(pk=request.POST['product'])
            except Product.DoesNotExist:
                return RedirectView.as_view()(request)

            product.active = True
            product.save()
        elif 'deactivate' in request.POST:
            try:
                product = Product.objects.get(name=request.POST['deactivate'])
            except Product.DoesNotExist:
                return RedirectView.as_view()(request)

            product.active = False
            product.save()
        else:
            return RedirectView.as_view()(request)

        return redirect(reverse('chiffee:admin-products'))


class AdminPurchasesView(View):
    template_name = 'chiffee/admin-purchases.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda user: user.is_superuser))
    def get(self, request, *args, **kwargs):
        purchase_filter = PurchaseFilter(request.GET)
        purchases = purchase_filter.qs
        paginator = Paginator(purchases, 10)

        current_page = get_current_page(request.GET.get('page'),
                                        paginator.num_pages)

        context = {'categories': CATEGORIES,
                   'current_page': current_page,
                   'filter': purchase_filter,
                   'pages': get_pages(current_page, paginator.num_pages),
                   'purchases': group_purchases_by_date(
                       paginator.page(current_page).object_list),
                   'shopping_cart_counter': count_shopping_cart(
                       request.session.get('shopping_cart'))}

        return render(request, self.template_name, context)


class CancelPurchaseView(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('key') is None:
            return RedirectView.as_view()(request)

        purchases = Purchase.objects.filter(key=kwargs.get('key'))

        if not purchases.exists():
            return RedirectView.as_view()(request)

        user = purchases[0].user
        employee = user.employee
        cancelled_purchases = ''

        for purchase in purchases:
            employee.balance += purchase.total_price
            cancelled_purchases += (f'{purchase.quantity} '
                                    f'{purchase.product.name} '
                                    f'für €{purchase.total_price}\n')
            purchase.delete()

        employee.save()

        message = (f'Hallo {user.first_name} {user.last_name}!\n\n'
                   f'Sie haben den folgenden Kauf erfolgreich storniert:\n'
                   f'{cancelled_purchases}\n'
                   f'Ihr aktueller Kontostand beträgt €{employee.balance}.')

        send_mail(EMAIL_SUBJECT,
                  message,
                  EMAIL_ADDRESS,
                  [user.email],
                  fail_silently=False)

        return RedirectView.as_view()(request, success=True)


class CheckoutView(View):
    template_name = 'chiffee/checkout.html'

    def get(self, request, *args, **kwargs):
        shopping_cart = request.session.get('shopping_cart', {})
        paginator = Paginator(tuple(shopping_cart.items()), 10)

        current_page = get_current_page(request.GET.get('page'),
                                        paginator.num_pages)

        context = {'check': get_check(shopping_cart),
                   'current_page': current_page,
                   'pages': get_pages(current_page, paginator.num_pages),
                   'shopping_cart': dict(
                       paginator.page(current_page).object_list),
                   'shopping_cart_counter': count_shopping_cart(shopping_cart),
                   'users': get_users()}

        if kwargs.get('username') is not None:
            try:
                user = User.objects.get(username=kwargs.get('username'))
            except User.DoesNotExist:
                return RedirectView.as_view()(request)

            context['username'] = user.username

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if 'decrease' in request.POST:
            try:
                product = Product.objects.get(name=request.POST['decrease'])
            except Product.DoesNotExist:
                return RedirectView.as_view()(request)

            shopping_cart = request.session.get('shopping_cart', {})

            if product.name in shopping_cart:
                shopping_cart[product.name] -= 1

                if shopping_cart[product.name] == 0:
                    shopping_cart.pop(product.name)

                request.session['shopping_cart'] = shopping_cart
        elif 'increase' in request.POST:
            try:
                product = Product.objects.get(name=request.POST['increase'])
            except Product.DoesNotExist:
                return RedirectView.as_view()(request)

            shopping_cart = request.session.get('shopping_cart', {})

            if product.name in shopping_cart:
                shopping_cart[product.name] += 1
                request.session['shopping_cart'] = shopping_cart
        elif 'delete' in request.POST:
            try:
                product = Product.objects.get(name=request.POST['delete'])
            except Product.DoesNotExist:
                return RedirectView.as_view()(request)

            shopping_cart = request.session.get('shopping_cart', {})

            if product.name in shopping_cart:
                shopping_cart.pop(product.name)
                request.session['shopping_cart'] = shopping_cart
        elif 'username' in request.POST:
            try:
                user = User.objects.get(username=request.POST['username'])
            except User.DoesNotExist:
                return RedirectView.as_view()(request)

            return CheckoutView.get(CheckoutView(),
                                    request,
                                    username=user.username)

        return redirect(reverse('chiffee:checkout'))


class ConfirmView(View):
    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            if 'username' not in request.POST:
                return redirect(reverse('chiffee:checkout'))

            try:
                user = User.objects.get(username=request.POST['username'])
            except User.DoesNotExist:
                return RedirectView.as_view()(request)

            try:
                employee = user.employee
            except Employee.DoesNotExist:
                employee = Employee.objects.create(user=user)

            shopping_cart = request.session.get('shopping_cart')

            if shopping_cart is None:
                return RedirectView.as_view()(request)

            purchase_products(shopping_cart,
                              user,
                              employee,
                              request.get_raw_uri().replace(
                                  request.get_full_path(),
                                  ''))

            request.session.pop('shopping_cart')

            return RedirectView.as_view()(request, success=True)
        elif 'cancel' in request.POST:
            request.session.pop('shopping_cart', None)

            return redirect(reverse('chiffee:index'))

        RedirectView.as_view()(request)


class CustomLoginView(auth_views.LoginView):
    def form_valid(self, form):
        user = User.objects.get(username=form.get_user().username)

        try:
            user.employee
        except Employee.DoesNotExist:
            Employee.objects.create(user=user)

        return super().form_valid(form)


class IndexView(View):
    template_name = 'chiffee/index.html'

    def get(self, request, *args, **kwargs):
        context = {'categories': CATEGORIES,
                   'products': Product.objects.filter(active=True).order_by(
                       'category', 'name'),
                   'shopping_cart_counter': count_shopping_cart(
                       request.session.get('shopping_cart'))}

        return render(request, self.template_name, context)


class ProfileView(View):
    template_name = 'chiffee/profile.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            balance = request.user.employee.balance
        except Employee.DoesNotExist:
            balance = 0

        purchases = Purchase.objects.filter(user=request.user)
        paginator = Paginator(purchases, 10)

        current_page = get_current_page(request.GET.get('page'),
                                        paginator.num_pages)

        context = {
            'balance': balance,
            'categories': CATEGORIES,
            'current_page': current_page,
            'form': forms.PictureForm(),
            'get_emails_deposits': request.user.employee.get_emails_deposits,
            'get_emails_purchases': request.user.employee.get_emails_purchases,
            'pages': get_pages(current_page, paginator.num_pages),
            'placeholder_picture': os.path.join(MEDIA_URL,
                                                USER_PICTURES_DIR,
                                                'placeholder.jpg'),
            'purchases': group_purchases_by_date(
                paginator.page(current_page).object_list),
            'shopping_cart_counter': count_shopping_cart(
                request.session.get('shopping_cart'))}

        return render(request, self.template_name, context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        employee = Employee.objects.get(user=request.user)

        if 'delete' in request.POST:
            employee.picture.delete()
        elif 'picture' in request.FILES:
            form = forms.PictureForm(request.POST, request.FILES)

            if form.is_valid():
                employee.picture.delete()
                employee.picture = request.FILES['picture']
                employee.save()
        else:
            if 'get-emails-purchases' in request.POST:
                employee.get_emails_purchases = True
            else:
                employee.get_emails_purchases = False

            if 'get-emails-deposits' in request.POST:
                employee.get_emails_deposits = True
            else:
                employee.get_emails_deposits = False

            employee.save()

        return redirect(reverse('chiffee:profile'))


class PurchaseView(View):
    template_name = 'chiffee/purchase.html'

    def get(self, request, *args, **kwargs):
        if 'product' not in request.GET:
            return RedirectView.as_view()(request)

        try:
            product = Product.objects.get(name=request.GET['product'])
        except Product.DoesNotExist:
            return RedirectView.as_view()(request)

        context = {'product': product.name,
                   'shopping_cart_counter': count_shopping_cart(
                       request.session.get('shopping_cart')),
                   'users': get_users()}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if 'username' not in request.POST and not request.user.is_authenticated:
            return RedirectView.as_view()(request)

        if request.user.is_authenticated:
            user = request.user
        else:
            try:
                user = User.objects.get(username=request.POST['username'])
            except User.DoesNotExist:
                return RedirectView.as_view()(request)

        try:
            employee = user.employee
        except Employee.DoesNotExist:
            employee = Employee.objects.create(user=user)

        if 'product' not in request.POST:
            return RedirectView.as_view()(request)

        try:
            product = Product.objects.get(name=request.POST['product'])
        except Product.DoesNotExist:
            return RedirectView.as_view()(request)

        shopping_cart = {product.name: 1}
        purchase_products(shopping_cart,
                          user,
                          employee,
                          request.get_raw_uri().replace(request.get_full_path(),
                                                        ''))

        request.session.pop('shopping_cart', None)

        return RedirectView.as_view()(request, success=True)


class RedirectView(View):
    template_name = 'chiffee/redirect.html'
    context = {'success': False}

    def get(self, request, *args, **kwargs):
        if kwargs.get('success') is not None and kwargs.get('success') is True:
            self.context['success'] = True

        self.context['shopping_cart_counter'] = count_shopping_cart(
            request.session.get('shopping_cart'))

        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        if kwargs.get('success') is not None and kwargs.get('success') is True:
            self.context['success'] = True

        self.context['shopping_cart'] = count_shopping_cart(
            request.session.get('shopping_cart'))

        return render(request, self.template_name, self.context)
