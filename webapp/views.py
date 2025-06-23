import uuid
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import render, redirect
from webapp.forms import RegisterForm, CheckoutForm, PaymentCardForm, AvatarUpdateForm, AddressForm, ProfileUpdateForm
from webapp.models import (TypeProduct, ViewProduct, InfoProduct, ProductDetail, ProductWarning, UserInfo, UserAddress,
                           PaymentCard, OrderItem, Order, Cart, WishlistItem, CartItem, Wishlist)
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth import logout, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import random
import string


def index(request):
    categories = TypeProduct.objects.all().order_by('order')
    context = {
        'categories': categories
    }
    return render(request, 'index.html', context)


def aboutus(request):
    return render(request, 'aboutus.html')


def FAQ(request):
    return render(request, 'FAQ.html')


def product_list_by_category(request, category_id):
    category = get_object_or_404(TypeProduct, id=category_id)
    products = ViewProduct.objects.filter(category=category).annotate(
        is_available=Case(
            When(is_active=True, quantity__gt=0, then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    )

    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('-is_available', 'price')
    elif sort == 'price_desc':
        products = products.order_by('-is_available', '-price')
    elif sort == 'popularity_asc':
        products = products.order_by('-is_available', 'views')
    elif sort == 'popularity_desc':
        products = products.order_by('-is_available', '-views')
    else:
        products = products.order_by('-is_available', '-created_at')

    material = request.GET.get('material')
    if material in ['gold', 'silver']:
        products = products.filter(type_material=material)

    # Добавляем информацию о наличии в избранном
    if request.user.is_authenticated:
        wishlist_products = set(WishlistItem.objects.filter(
            wishlist__user=request.user,
            product__in=products
        ).values_list('product_id', flat=True))

        for product in products:
            product.in_wishlist = product.id in wishlist_products
    else:
        for product in products:
            product.in_wishlist = False

    return render(request, 'category.html', {
        'category': category,
        'products': products,
        'current_sort': sort,
        'current_material': material,
    })


def product_detail(request, pk):
    product = get_object_or_404(ViewProduct, pk=pk)
    context = {'product': product}
    return render(request, 'product.html', context)


def helper(request):
    return render(request, 'helper.html')


@login_required
def profile(request):
    user_info = UserInfo.objects.get_or_create(user=request.user)[0]
    addresses = UserAddress.objects.filter(user=request.user)
    cards = PaymentCard.objects.filter(user=request.user).order_by('-is_default', '-created_at')  # Добавлен order_by
    orders = Order.objects.filter(user=request.user).order_by('-order_date')

    profile_form = ProfileUpdateForm(instance=user_info)
    address_form = AddressForm()
    card_form = PaymentCardForm()
    avatar_form = AvatarUpdateForm(instance=user_info)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=user_info)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Профиль успешно обновлен!')
                return redirect('profile')

        elif 'add_address' in request.POST:
            address_form = AddressForm(request.POST, request=request)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user
                address.save()
                messages.success(request, 'Адрес успешно добавлен!')
                return redirect('profile')

        elif 'add_card' in request.POST:
            card_form = PaymentCardForm(request.POST, request=request)
            if card_form.is_valid():
                card = card_form.save(commit=False)
                card.user = request.user
                card.save()
                messages.success(request, 'Карта успешно добавлена!')
                return redirect('profile')

        elif 'update_avatar' in request.POST:
            avatar_form = AvatarUpdateForm(request.POST, request.FILES, instance=user_info)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, 'Аватар успешно обновлен!')
                return redirect('profile')

    context = {
        'user_info': user_info,
        'addresses': addresses,
        'cards': cards,
        'orders': orders,
        'profile_form': profile_form,
        'address_form': address_form,
        'card_form': card_form,
        'avatar_form': avatar_form,
    }
    return render(request, 'profile.html', context)


@login_required
def set_default_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, 'Адрес установлен как основной')
    if request.user.is_superuser:
        return redirect(reverse('panel_admina') + '?section=addresses')
    return redirect('profile')


@login_required
def set_default_card(request, card_id):
    card = get_object_or_404(PaymentCard, id=card_id, user=request.user)
    PaymentCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
    card.is_default = True
    card.save()
    messages.success(request, 'Карта установлена как основная')
    if request.user.is_superuser:
        return redirect(reverse('panel_admina') + '?section=payment-methods')
    return redirect('profile')


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    if address.is_default and UserAddress.objects.filter(user=request.user).count() > 1:
        new_default = UserAddress.objects.filter(user=request.user).exclude(id=address_id).first()
        new_default.is_default = True
        new_default.save()
    address.delete()
    messages.success(request, 'Адрес успешно удалён')
    if request.user.is_superuser:
        return redirect(reverse('panel_admina') + '?section=addresses')
    return redirect('profile')


@login_required
def delete_card(request, card_id):
    card = get_object_or_404(PaymentCard, id=card_id, user=request.user)
    if card.is_default and PaymentCard.objects.filter(user=request.user).count() > 1:
        new_default = PaymentCard.objects.filter(user=request.user).exclude(id=card_id).first()
        new_default.is_default = True
        new_default.save()
    card.delete()
    messages.success(request, 'Карта успешно удалена')
    if request.user.is_superuser:
        return redirect(reverse('panel_admina') + '?section=payment-methods')
    return redirect('profile')


def delivery(request):
    return render(request, 'delivery.html')


def news(request):
    recent_date = timezone.now() - timedelta(days=30)
    categories = TypeProduct.objects.all()
    products_by_category = {}

    for category in categories:
        products = ViewProduct.objects.filter(
            category=category,
            created_at__gte=recent_date,
            is_active=True,
            quantity__gt=0
        )
        if products.exists():
            products_by_category[category] = products[:5]
    context = {'products_by_category': products_by_category}
    return render(request, 'news.html', context)


def gift(request):
    return render(request, 'gift.html')


def contact(request):
    return render(request, 'contact.html')


def product_view(request, pk):
    product = get_object_or_404(ViewProduct, pk=pk)
    info = InfoProduct.objects.filter(view_product=product).first()
    details = ProductDetail.objects.filter(product=info) if info else []
    warnings = ProductWarning.objects.filter(product=info) if info else []
    category = product.category
    category_id = request.GET.get('category_id')

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = WishlistItem.objects.filter(
            wishlist__user=request.user,
            product=product
        ).exists()

    if category_id:
        category = get_object_or_404(TypeProduct, id=category_id)
    else:
        category = product.category

    return render(request, 'product.html', {
        'product': product,
        'info': info,
        'details': details,
        'warnings': warnings,
        'category': category,
        'in_wishlist': in_wishlist,  # Добавляем в контекст
    })


def logout_view(request):
    logout(request)
    return redirect('main')


def register(request):
    if request.user.is_authenticated:
        return redirect('main')
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            middle_name = request.POST['middle_name']
            phone = request.POST['phone']
            birth_date = request.POST['birth_date']
            userinfo = UserInfo(
                user=user,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                phone=phone,
                birth_date=birth_date
            )
            Wishlist.objects.create(user=user)
            userinfo.save()

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('main')

    context = {'form': form}
    return render(request, 'register.html', context)


def catalog(request):
    categories = TypeProduct.objects.all()
    category_products = []

    for category in categories:
        products = ViewProduct.objects.filter(category=category).annotate(
            is_available=Case(
                When(is_active=True, quantity__gt=0, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-is_available', '-created_at')[:5]

        if request.user.is_authenticated:
            wishlist_products = set(WishlistItem.objects.filter(
                wishlist__user=request.user,
                product__in=products
            ).values_list('product_id', flat=True))

            for product in products:
                product.in_wishlist = product.id in wishlist_products
        else:
            for product in products:
                product.in_wishlist = False

        category_products.append((category, products))

    context = {'category_products': category_products}
    return render(request, 'catalog.html', context)


@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})


@require_POST
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(ViewProduct, pk=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if product.quantity < quantity:
        return JsonResponse({
            'success': False,
            'message': 'Недостаточно товара на складе'
        })

    cart, created = Cart.objects.get_or_create(user=request.user)
    try:
        cart.add_item(product, quantity)
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_items,
            'product_quantity': product.quantity - quantity,
            'message': f'{product.name_product} добавлен в корзину'
        })
    except Exception as e:
        error_msg = str(e).strip('[]"\'').strip()
        return JsonResponse({
            'success': False,
            'message': error_msg if error_msg else 'Произошла ошибка'
        }, status=400)


@require_POST
@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(ViewProduct, pk=product_id)
    cart = get_object_or_404(Cart, user=request.user)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        product.quantity += cart_item.quantity
        product.save()
        cart_item.delete()

        return JsonResponse({
            'success': True,
            'message': f'Товар "{product.name_product}" удалён из корзины',
            'cart_total': cart.total_items,
            'product_quantity': product.quantity
        })
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Товар не найден в корзине',
            'message': 'Товар не найден в корзине'
        }, status=404)


@require_POST
@login_required
def update_cart_item(request, product_id):
    product = get_object_or_404(ViewProduct, pk=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        diff = quantity - cart_item.quantity

        if diff > product.quantity:
            return JsonResponse({
                'success': False,
                'error': 'Недостаточно товара на складе',
                'message': 'Недостаточно товара на складе'
            })

        product.quantity -= diff
        product.save()

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()

        return JsonResponse({
            'success': True,
            'message': 'Корзина обновлена',
            'cart_total': cart.total_items,
            'product_quantity': product.quantity,
            'item_total': cart_item.total_price,
            'cart_total_price': cart.total_price
        })
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Товар не найден в корзине',
            'message': 'Товар не найден в корзине'
        })


@login_required
def check_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return JsonResponse({'has_items': cart.items.exists()})



def _detect_card_type(card_number):
    """Определяет тип карты по её номеру (Visa, Mastercard, Мир и т. д.)"""
    card_number = card_number.replace(" ", "")
    if card_number.startswith("4"):
        return "visa"
    elif card_number.startswith("5"):
        return "mastercard"
    elif card_number.startswith("2") or card_number.startswith("6"):
        return "mir"
    else:
        return "other"


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('view_cart')

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            phone = request.POST.get('phone')
            delivery_date = request.POST.get('delivery_date')
            delivery_time = request.POST.get('delivery_time')
            notes = request.POST.get('notes', '')

            # Обработка адреса
            saved_address_id = request.POST.get('saved_address')
            if saved_address_id and saved_address_id != 'None':
                address = get_object_or_404(UserAddress, id=saved_address_id, user=request.user)
            else:
                address = UserAddress.objects.create(
                    user=request.user,
                    address_line1=request.POST.get('address'),
                    city=request.POST.get('city'),
                    postal_code=request.POST.get('postal_code'),
                    country='Россия',
                    is_default=not UserAddress.objects.filter(user=request.user).exists()
                )

            # Обработка карты
            saved_card_id = request.POST.get('saved_card')
            if saved_card_id and saved_card_id != 'None':
                card = get_object_or_404(PaymentCard, id=saved_card_id, user=request.user)
            else:
                card_number = request.POST.get('card_number', '').replace(' ', '')
                expiry_parts = request.POST.get('card_expiry', '').split('/')
                if len(expiry_parts) != 2:
                    raise ValidationError('Неверный формат срока действия карты. Используйте MM/YY')

                card = PaymentCard.objects.create(
                    user=request.user,
                    card_holder=request.POST.get('card_name'),
                    card_number=card_number[-4:],
                    expiry_month=int(expiry_parts[0]),
                    expiry_year=2000 + int(expiry_parts[1]),
                    cvv=request.POST.get('card_cvv'),
                    card_type=_detect_card_type(card_number),
                    is_default=not PaymentCard.objects.filter(user=request.user).exists()
                )

            # Проверка на день рождения (скидка 20%)
            discount = Decimal('0')
            if hasattr(request.user, 'profile') and request.user.profile.birth_date:
                today = timezone.now().date()
                if (request.user.profile.birth_date.month == today.month and
                        request.user.profile.birth_date.day == today.day):
                    discount = (cart.total_price * Decimal('0.2')).quantize(Decimal('0.00'))
                    messages.success(request, 'С днем рождения! Ваша скидка 20%')

            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                phone=phone,
                shipping_address=address,
                billing_address=address,
                payment_card=card,
                delivery_date=delivery_date,
                delivery_time=delivery_time,
                subtotal=cart.total_price,
                shipping_cost=Decimal('450.00'),
                discount=discount,
                total=(cart.total_price + Decimal('450.00') - discount).quantize(Decimal('0.00')),
                email=request.user.email,
                notes=notes,
                status='pending',
            )

            # Переносим товары из корзины в заказ и уменьшаем количество на складе
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                    discounted_price=item.product.final_price if item.product.discount else item.product.price
                )
                # Уменьшаем количество товара на складе
                item.product.quantity -= item.quantity
                item.product.save()

            # Полностью очищаем корзину
            cart.items.all().delete()

            # Перенаправляем на страницу подтверждения заказа
            return redirect('order_confirmation', order_id=order.id)


        except Exception as e:

            print(f"Ошибка при оформлении заказа: {str(e)}")  # Логирование в консоль

            messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')

            return redirect('checkout')

    # Для GET запроса просто отображаем форму
    default_address = UserAddress.objects.filter(user=request.user, is_default=True).first()
    default_card = PaymentCard.objects.filter(user=request.user, is_default=True).first()

    return render(request, 'checkout.html', {
        'cart': cart,
        'default_address': default_address,
        'default_card': default_card,
        'delivery_date_min': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
        'delivery_date_max': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    })


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_superuser and order.user != request.user:
        raise Http404("Заказ не найден")
    return render(request, 'order_detail.html', {'order': order})


@login_required
def view_wishlist(request):
    wishlist = get_object_or_404(Wishlist, user=request.user)
    return render(request, 'wishlist.html', {'wishlist': wishlist})

@login_required
def wishlist_count(request):
    wishlist = get_object_or_404(Wishlist, user=request.user)
    return JsonResponse({'count': wishlist.items.count()})

@require_POST
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(ViewProduct, pk=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    try:
        if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
            return JsonResponse({
                'success': False,
                'message': 'Товар уже в избранном'
            })

        WishlistItem.objects.create(wishlist=wishlist, product=product)
        return JsonResponse({
            'success': True,
            'message': 'Товар добавлен в избранное',
            'wishlist_count': wishlist.items.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@require_POST
@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(ViewProduct, pk=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)

    try:
        deleted_count, _ = WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
        if deleted_count == 0:
            return JsonResponse({
                'success': False,
                'message': 'Товар не найден в избранном'
            }, status=404)

        return JsonResponse({
            'success': True,
            'message': 'Товар удален из избранного',
            'wishlist_count': wishlist.items.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@require_POST
@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(ViewProduct, pk=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    try:
        wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()

        if wishlist_item:
            wishlist_item.delete()
            message = 'Товар удален из избранного'
            is_added = False
        else:
            WishlistItem.objects.create(wishlist=wishlist, product=product)
            message = 'Товар добавлен в избранное'
            is_added = True

        return JsonResponse({
            'success': True,
            'is_added': is_added,
            'message': message,
            'wishlist_count': wishlist.items.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
def panel_admina(request):
    if not request.user.is_superuser:
        return redirect('profile')

    # Определяем активную секцию
    active_section = request.GET.get('section', 'orders')

    # Фильтрация заказов
    status_filter = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    orders = Order.objects.all().order_by('-order_date')

    if status_filter != 'all':
        orders = orders.filter(status=status_filter)

    if date_from:
        orders = orders.filter(order_date__gte=date_from)

    if date_to:
        orders = orders.filter(order_date__lte=date_to)

    # Статистика
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()
    delivered_orders = Order.objects.filter(status='delivered').count()

    admin_info = UserInfo.objects.get_or_create(user=request.user)[0]
    admin_addresses = UserAddress.objects.filter(user=request.user)
    admin_cards = PaymentCard.objects.filter(user=request.user)

    profile_form = ProfileUpdateForm(instance=admin_info)
    address_form = AddressForm()
    card_form = PaymentCardForm()

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=admin_info)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Профиль обновлен')
                return redirect(f"{reverse('panel_admina')}?section=personal-info")

        elif 'add_address' in request.POST:
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user
                address.save()
                messages.success(request, 'Адрес добавлен')
                return redirect(f"{reverse('panel_admina')}?section=addresses")

        elif 'add_card' in request.POST:
            card_form = PaymentCardForm(request.POST)
            if card_form.is_valid():
                card = card_form.save(commit=False)
                card.user = request.user
                card.save()
                messages.success(request, 'Карта добавлена')
                return redirect(f"{reverse('panel_admina')}?section=payment-methods")

    context = {
        'order_list': orders,
        'user_info': admin_info,
        'addresses': admin_addresses,
        'cards': admin_cards,
        'profile_form': profile_form,
        'address_form': address_form,
        'card_form': card_form,
        'status_choices': Order.ORDER_STATUS,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'delivered_orders': delivered_orders,
        'active_section': active_section,
    }
    return render(request, 'panel_admina.html', context)


@login_required
def update_order_status(request, order_id, new_status):
    if not request.user.is_superuser:
        return redirect('profile')

    order = get_object_or_404(Order, pk=order_id)
    available_statuses = [status[0] for status in order.get_available_statuses()]

    if new_status not in available_statuses:
        messages.error(request, 'Невозможно изменить статус на выбранный')
        return redirect('panel_admina')

    if new_status == 'cancelled':
        if request.method == 'POST':
            reason = request.POST.get('reason', '')
            if not reason:
                messages.error(request, 'Укажите причину отмены')
                return redirect('cancel_order', order_id=order.id)

            order.status = 'cancelled'
            order.cancellation_reason = reason
            order.save()
            messages.success(request, f'Заказ #{order.id} отменен')
            return redirect('panel_admina')
        else:
            return redirect('cancel_order', order_id=order.id)
    else:
        order.status = new_status
        if new_status == 'shipped':
            order.tracking_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        order.save()
        messages.success(request, f'Статус заказа #{order.id} изменен на "{order.get_status_display()}"')

    return redirect('panel_admina')


@login_required
def cancel_order(request, order_id):
    if not request.user.is_superuser:
        return redirect('profile')

    order = get_object_or_404(Order, pk=order_id)

    if not order.can_be_cancelled:
        messages.error(request, 'Этот заказ нельзя отменить')
        return redirect('panel_admina')

    if request.method == 'POST':
        return update_order_status(request, order_id, 'cancelled')

    return render(request, 'cancel.html', {'order': order})