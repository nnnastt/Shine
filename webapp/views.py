from importlib.resources import read_text

from django.shortcuts import render,redirect
from webapp.models import TypeProduct, ViewProduct, InfoProduct, ProductDetail, ProductWarning, Wishlist, Cart
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
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
    return render(request, 'product_detail.html', {'product': product})

def helper(request):
    return render(request, 'helper.html')


def profile(request):
    return render(request, 'profile.html')

def delivery(request):
    return render(request, 'delivery.html')


def news(request):
    return render(request, 'news.html')


def gift(request):
    return render(request, 'gift.html')




def contact(request):
    return render(request, 'contact.html')


def product_view(request, pk):
    product = get_object_or_404(ViewProduct, pk=pk)
    info = InfoProduct.objects.filter(view_product=product).first()
    details = ProductDetail.objects.filter(product=info) if info else []
    warnings = ProductWarning.objects.filter(product=info) if info else []

    return render(request, 'product.html', {
        'product': product,
        'info': info,
        'details': details,
        'warnings': warnings,
    })

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(ViewProduct, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist.add_product(product)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(ViewProduct, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.remove_product(product)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(ViewProduct, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.add_product(product)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(ViewProduct, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    cart.remove_product(product)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def logout_view(request):
    logout(request)
    return redirect('main')