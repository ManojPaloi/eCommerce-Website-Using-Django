def cart_item_count(request):
    cart = request.session.get('cart', {})
    count = sum(cart.values())
    return {'cart_item_count': count}
