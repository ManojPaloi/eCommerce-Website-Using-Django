def cart_quantity(request):
    cart = request.session.get("cart", {})
    total_quantity = sum(cart.values())
    return {"total_quantity": total_quantity}
