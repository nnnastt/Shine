from .models import Cart

def cart_items_count(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return {'cart_items_count': cart.total_items}
    return {'cart_items_count': 0}