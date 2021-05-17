from django import template

from chiffee.models import Product

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='divide_by')
def divide_by(dividend, divisor):
    return dividend / divisor


@register.filter(name='next_page')
def next_page(current_page, pages):
    page = current_page + 1

    if page > pages[-1]:
        page = pages[-1]

    return page


@register.filter(name='next_page_section')
def next_page_section(pages):
    return pages[pages.index('next_page_section') - 1] + 1


@register.filter(name='prev_page')
def prev_page(current_page):
    page = current_page - 1

    if page < 1:
        page = 1

    return page


@register.filter(name='prev_page_section')
def prev_page_section(pages):
    return pages[pages.index('prev_page_section') + 1] - 1


@register.filter(name='purchase_group_total')
def purchase_group_total(purchase_group):
    total = 0

    for purchase in purchase_group:
        total += purchase.product.price * purchase.quantity

    return total


@register.filter(name='total_price')
def total_price(product, quantity):
    return Product.objects.get(name=product).price * quantity
