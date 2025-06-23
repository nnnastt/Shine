from webapp.models import Cart, Wishlist


def cart_items_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        return {'cart_items_count': cart.total_items if cart else 0}
    return {'cart_items_count': 0}

def wishlist_items_count(request):
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        return {'wishlist_items_count': wishlist.items.count() if wishlist else 0}
    return {'wishlist_items_count': 0}