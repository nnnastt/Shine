from django.shortcuts import render,redirect
from webapp.forms import RegisterForm
from webapp.models import TypeProduct, ViewProduct, InfoProduct, ProductDetail, ProductWarning, Wishlist, Cart, UserInfo
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth import logout, login
from django.contrib import messages
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



def logout_view(request):
    logout(request)
    return redirect('main')


def register(request):
    if request.user.is_authenticated:
        return redirect('main')
    form = RegisterForm()
    if request.method == 'POST':
        form=RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            first_name = request.POST['first_name'],
            last_name = request.POST['last_name'],
            middle_name = request.POST['middle_name'],
            phone = request.POST['phone'],
            birth_date = request.POST['birth_date']
            userinfo = UserInfo(user=user,first_name = first_name,last_name=last_name,middle_name=middle_name,phone=phone,birth_date=birth_date)
            userinfo.save()

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile')

    context={'form':form}
    return render(request,'register.html',context)