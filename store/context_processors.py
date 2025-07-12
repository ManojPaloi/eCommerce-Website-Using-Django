from .models import Wishlist

def cart_item_count(request):
    cart = request.session.get('cart', {})
    count = sum(cart.values())
    return {'cart_item_count': count}

def wishlist_count(request):
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
        return {'wishlist_count': count}
    return {'wishlist_count': 0}