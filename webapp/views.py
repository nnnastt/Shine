from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from webapp.forms import RegisterForm, PaymentCardForm, AvatarUpdateForm, AddressForm, ProfileUpdateForm
from webapp.models import TypeProduct, ViewProduct, InfoProduct, ProductDetail, ProductWarning, UserInfo, UserAddress, \
    PaymentCard
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth import logout, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# Create your views here.
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
    cards = PaymentCard.objects.filter(user=request.user)
    orders = []

    # Формы
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
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user
                address.save()
                messages.success(request, 'Адрес успешно добавлен!')
                return redirect('profile')

        elif 'add_card' in request.POST:
            card_form = PaymentCardForm(request.POST)
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
    address.is_default = True
    address.save()
    messages.success(request, 'Основной адрес успешно изменен')
    return redirect('profile')

@login_required
def set_default_card(request, card_id):
    card = get_object_or_404(PaymentCard, id=card_id, user=request.user)
    card.is_default = True
    card.save()
    messages.success(request, 'Основная карта успешно изменена')
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
            first_name = request.POST['first_name'],
            last_name = request.POST['last_name'],
            middle_name = request.POST['middle_name'],
            phone = request.POST['phone'],
            birth_date = request.POST['birth_date']
            userinfo = UserInfo(user=user, first_name=first_name,
                                last_name=last_name,
                                middle_name=middle_name,
                                phone=phone,
                                birth_date=birth_date)
            userinfo.save()

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile')

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

        category_products.append((category, products))
    context = {'category_products': category_products}
    return render(request, 'catalog.html', context)