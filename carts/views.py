from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from store.models import Product, Color
from .models import Cart, CartItem
from orders.models import Order, OrderItem
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .utils import generate_order_qr_code
from django.urls import reverse
from django.conf import settings
from email.mime.image import MIMEImage
from weasyprint import HTML
import tempfile
import qrcode
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
import weasyprint
from django.utils import timezone
import razorpay
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        request.session['cart_id'] = cart.cart_id
        return cart
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(cart_id=cart_id, user__isnull=True)
                return cart
            except Cart.DoesNotExist:
                pass
        cart = Cart.objects.create(user=None)
        request.session['cart_id'] = cart.cart_id
        request.session.modified = True
        return cart

def sync_session_with_cart(request, cart):
    session_cart = request.session.get('cart', {})
    logger.debug(f"Syncing cart {cart.cart_id} with session: {session_cart}")

    # Create a set of cart keys from the session for comparison
    session_keys = set(session_cart.keys())

    # Update or create CartItems based on session
    for cart_key, quantity in session_cart.items():
        try:
            parts = cart_key.split('_')
            product_id = parts[0]
            color_option = parts[1] if len(parts) > 1 else ''
            size_option = parts[2] if len(parts) > 2 else ''
            
            product = get_object_or_404(Product, id=int(product_id))
            color = product.colors.filter(color_name=color_option).first() if color_option else None

            if quantity > product.stock:
                logger.warning(f"Adjusting quantity {quantity} to stock {product.stock} for product {product.product_name}")
                quantity = product.stock
                session_cart[cart_key] = quantity
                request.session['cart'] = session_cart
                request.session.modified = True

            if quantity > 0:
                cart_item, created = CartItem.objects.update_or_create(
                    cart=cart,
                    product=product,
                    color=color,
                    size=size_option,
                    defaults={'quantity': quantity, 'is_active': True}
                )
                logger.debug(f"{'Created' if created else 'Updated'} CartItem: {cart_item}")
            else:
                logger.warning(f"Removing item with zero quantity: {cart_key}")
                del session_cart[cart_key]
                request.session['cart'] = session_cart
                request.session.modified = True
        except (ValueError, Product.DoesNotExist):
            logger.warning(f"Invalid product ID {product_id} found in cart")
            del session_cart[cart_key]
            request.session['cart'] = session_cart
            request.session.modified = True
            continue

    # Remove CartItems that are no longer in the session
    cart.cartitem_set.exclude(
        product__id__in=[int(k.split('_')[0]) for k in session_keys],
        color__color_name__in=[k.split('_')[1] if len(k.split('_')) > 1 else '' for k in session_keys],
        size__in=[k.split('_')[2] if len(k.split('_')) > 2 else '' for k in session_keys]
    ).delete()

    logger.debug(f"Cart {cart.cart_id} synced successfully")
    
    
def calculate_cart_totals(session_cart):
    subtotal = Decimal('0.00')
    for key, qty in session_cart.items():
        try:
            prod_id = key.split('_')[0]
            prod = Product.objects.get(id=int(prod_id))
            subtotal += Decimal(str(prod.price)) * Decimal(str(qty))
        except (ValueError, Product.DoesNotExist):
            logger.warning(f"Invalid product in cart key: {key}")
            continue
    tax = subtotal * Decimal('0.18')
    total = subtotal + tax
    return {
        'subtotal': float(subtotal),
        'tax': float(tax),
        'total': float(total)
    }

def cart(request):
    cart = get_or_create_cart(request)
    sync_session_with_cart(request, cart)
    session_cart = request.session.get('cart', {})
    logger.debug(f"Rendering cart view with session: {session_cart}")

    if not session_cart:
        messages.info(request, "Your cart is empty.")
        return render(request, 'store/carts.html', {
            'cart_items': [],
            'cart_item_count': 0,
            'cart_totals': {'subtotal': 0.00, 'tax': 0.00, 'total': 0.00},
        })

    products = []
    subtotal = Decimal('0.00')
    cart_item_count = 0

    for cart_key, qty in list(session_cart.items()):
        try:
            product_id = cart_key.split('_')[0]
            product = get_object_or_404(Product, id=int(product_id))
        except (ValueError, Product.DoesNotExist):
            logger.warning(f"Invalid product ID {product_id} in cart")
            del session_cart[cart_key]
            request.session['cart'] = session_cart
            request.session.modified = True
            continue

        url = product.get_url() if hasattr(product, 'get_url') else '#'
        total_price = Decimal(str(product.price)) * Decimal(str(qty))
        subtotal += total_price
        cart_item_count += qty

        parts = cart_key.split('_')
        color_option = parts[1] if len(parts) > 1 else ''
        size_option = parts[2] if len(parts) > 2 else ''
        
        description_parts = []
        if product.description:
            description_parts.append(product.description)
        if color_option:
            description_parts.append(f"Color: {color_option}")
        if size_option:
            description_parts.append(f"Size: {size_option}")
        
        description = ", ".join(description_parts) if description_parts else "No description available"

        products.append({
            'id': product.id,
            'name': product.product_name,
            'description': description,
            'image': product.image1.url if product.image1 else '',
            'slug': product.slug,
            'category_slug': product.category.slug if product.category else '',
            'url': url,
            'quantity': qty,
            'unit_price': float(product.price),
            'total_price': float(total_price),
            'color': color_option,
            'size': size_option,
        })

    tax = subtotal * Decimal('0.18')
    total = subtotal + tax

    cart_totals = {
        'subtotal': float(subtotal),
        'tax': float(tax),
        'total': float(total),
    }

    return render(request, 'store/carts.html', {
        'cart_items': products,
        'cart_item_count': cart_item_count,
        'cart_totals': cart_totals,
    })
def add_cart(request, product_id):
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    session_cart = request.session.get('cart', {})

    color_option = request.POST.get('color', '')
    size_option = request.POST.get('size', '')
    quantity = int(request.POST.get('quantity', 1))

    color = None
    if color_option:
        color = product.colors.filter(color_name=color_option).first()
        if not color:
            messages.error(request, f"Color {color_option} is not available for {product.product_name}.")
            return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

    if size_option and size_option not in dict(CartItem.SIZE_CHOICES).keys():
        messages.error(request, f"Size {size_option} is not valid for {product.product_name}.")
        return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

    cart_key = f"{product_id}"
    if color_option:
        cart_key += f"_{color_option}"
    if size_option:
        cart_key += f"_{size_option}"

    current_quantity = session_cart.get(cart_key, 0)
    if current_quantity + quantity > product.stock:
        messages.error(request, f"Sorry, only {product.stock} units of {product.product_name} are available.")
        return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

    session_cart[cart_key] = current_quantity + quantity
    request.session['cart'] = session_cart
    request.session.modified = True
    sync_session_with_cart(request, cart)
    messages.success(request, f"{product.product_name} (Color: {color_option or 'N/A'}, Size: {size_option or 'N/A'}) has been added to your cart.")
    return redirect('cart')

def buy_now(request, product_id):
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    session_cart = request.session.get('cart', {})

    color_option = request.POST.get('color', '')
    size_option = request.POST.get('size', '')

    color = None
    if color_option:
        color = product.colors.filter(color_name=color_option).first()
        if not color:
            messages.error(request, f"Color {color_option} is not available for {product.product_name}.")
            return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

    if size_option and size_option not in dict(CartItem.SIZE_CHOICES).keys():
        messages.error(request, f"Size {size_option} is not valid for {product.product_name}.")
        return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

    cart_key = f"{product_id}"
    if color_option:
        cart_key += f"_{color_option}"
    if size_option:
        cart_key += f"_{size_option}"

    if session_cart.get(cart_key, 0) + 1 > product.stock:
        messages.error(request, f"Sorry, only {product.stock} units of {product.product_name} are available.")
        return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

    session_cart[cart_key] = 1
    request.session['cart'] = session_cart
    request.session.modified = True
    sync_session_with_cart(request, cart)
    messages.success(request, f"{product.product_name} (Color: {color_option or 'N/A'}, Size: {size_option or 'N/A'}) has been added to your cart.")
    return redirect('place_order')

def cart_remove(request, product_id):
    cart = get_or_create_cart(request)
    session_cart = request.session.get('cart', {})

    keys_to_remove = [key for key in session_cart.keys() if key.startswith(f"{product_id}_") or key == str(product_id)]
    for key in keys_to_remove:
        del session_cart[key]

    request.session['cart'] = session_cart
    request.session.modified = True
    sync_session_with_cart(request, cart)
    product = get_object_or_404(Product, id=product_id)
    messages.success(request, f"{product.product_name} has been removed from your cart.")
    return redirect('cart')

@require_POST
def increase_cart(request, product_id):
    try:
        cart = get_or_create_cart(request)
        product = get_object_or_404(Product, id=product_id)
        session_cart = request.session.get('cart', {})
        logger.debug(f"Before increase - Session cart: {session_cart}")

        color_option = request.POST.get('color', '')
        size_option = request.POST.get('size', '')

        cart_key = f"{product_id}"
        if color_option:
            cart_key += f"_{color_option}"
        if size_option:
            cart_key += f"_{size_option}"

        current_quantity = session_cart.get(cart_key, 0)
        if current_quantity + 1 > product.stock:
            return JsonResponse({'success': False, 'error': 'Insufficient stock.'}, status=400)

        session_cart[cart_key] = current_quantity + 1
        request.session['cart'] = session_cart
        request.session.modified = True  # Explicitly mark session as modified
        logger.debug(f"After increase - Session cart: {session_cart}")

        sync_session_with_cart(request, cart)  # Sync session with database
        cart_totals = calculate_cart_totals(session_cart)

        return JsonResponse({
            'success': True,
            'message': f"{product.product_name} increased.",
            'quantity': session_cart[cart_key],
            'cart_totals': cart_totals,
        })

    except Exception as e:
        logger.error(f"Increase error: {str(e)}")
        return JsonResponse({'success': False, 'error': f"Error: {str(e)}"}, status=500)

@require_POST
def decrease_cart(request, product_id):
    try:
        cart = get_or_create_cart(request)
        product = get_object_or_404(Product, id=product_id)
        session_cart = request.session.get('cart', {})

        color_option = request.POST.get('color', '')
        size_option = request.POST.get('size', '')

        cart_key = f"{product_id}"
        if color_option:
            cart_key += f"_{color_option}"
        if size_option:
            cart_key += f"_{size_option}"

        if cart_key not in session_cart:
            return JsonResponse({'success': False, 'error': 'Item not found in cart.'}, status=404)

        new_quantity = session_cart[cart_key] - 1

        if new_quantity > 0:
            session_cart[cart_key] = new_quantity
        else:
            del session_cart[cart_key]

        request.session['cart'] = session_cart
        request.session.modified = True
        sync_session_with_cart(request, cart)
        cart_totals = calculate_cart_totals(session_cart)

        return JsonResponse({
            'success': True,
            'message': f"{product.product_name} decreased.",
            'quantity': max(new_quantity, 0),
            'cart_totals': cart_totals,
        })

    except Exception as e:
        logger.error(f"Decrease error: {str(e)}")
        return JsonResponse({'success': False, 'error': f"Error: {str(e)}"}, status=500)


@require_POST
def remove_cart_item(request, product_id):
    try:
        cart = get_or_create_cart(request)
        product = get_object_or_404(Product, id=product_id)
        session_cart = request.session.get('cart', {})

        color_option = request.POST.get('color', '')
        size_option = request.POST.get('size', '')

        cart_key = f"{product_id}"
        if color_option:
            cart_key += f"_{color_option}"
        if size_option:
            cart_key += f"_{size_option}"

        if cart_key in session_cart:
            del session_cart[cart_key]

        request.session['cart'] = session_cart
        request.session.modified = True
        sync_session_with_cart(request, cart)
        cart_totals = calculate_cart_totals(session_cart)

        return JsonResponse({
            'success': True,
            'message': f"{product.product_name} removed.",
            'quantity': 0,
            'cart_totals': cart_totals,
        })

    except Exception as e:
        logger.error(f"Remove error: {str(e)}")
        return JsonResponse({'success': False, 'error': f"Error: {str(e)}"}, status=500)

def redirect_back(request):
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('cart')

@require_POST
def apply_coupon(request):
    try:
        coupon_code = request.POST.get('coupon_code', '').strip()
        cart = get_or_create_cart(request)
        session_cart = request.session.get('cart', {})

        subtotal = Decimal('0.00')
        for cart_key, qty in session_cart.items():
            product_id = cart_key.split('_')[0]
            try:
                product = Product.objects.get(id=int(product_id))
                subtotal += Decimal(str(product.price)) * Decimal(qty)
            except Product.DoesNotExist:
                continue

        if coupon_code.lower() == 'save50':
            discount = Decimal('50.00')
            request.session['discount'] = float(discount)
            request.session['coupon_code'] = coupon_code
            messages.success(request, f'Coupon "{coupon_code}" applied successfully! You saved ₹50.')
        else:
            request.session['discount'] = 0
            request.session['coupon_code'] = ''
            messages.error(request, 'Invalid coupon code.')

        request.session.modified = True
        return redirect('place_order')
    except Exception as e:
        logger.error(f"Error in apply_coupon: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Server error: {str(e)}"
        }, status=500)

def place_order(request):
    try:
        logger.debug("Entering place_order view")
        cart = get_or_create_cart(request)
        sync_session_with_cart(request, cart)

        session_cart = request.session.get('cart', {})
        if not session_cart:
            messages.info(request, "Your cart is empty.")
            return redirect('cart')

        cart_items = []
        subtotal = Decimal('0.00')

        for cart_key, qty in list(session_cart.items()):
            try:
                product_id = cart_key.split('_')[0]
                product_id_int = int(product_id)
                product = get_object_or_404(Product, id=product_id_int)
            except (ValueError, Product.DoesNotExist):
                logger.warning(f"Invalid product ID {product_id} in cart")
                del session_cart[cart_key]
                request.session['cart'] = session_cart
                request.session.modified = True
                continue

            total_price = Decimal(str(product.price)) * Decimal(str(qty))
            subtotal += total_price

            parts = cart_key.split('_')
            color_option = parts[1] if len(parts) > 1 else ''
            size_option = parts[2] if len(parts) > 2 else ''

            cart_items.append({
                'product': product,
                'quantity': qty,
                'total_price': total_price,
                'color': color_option,
                'size': size_option,
            })

        tax = subtotal * Decimal('0.18')
        session_discount = request.session.get('discount', 0)
        discount = Decimal(str(session_discount)) if session_discount > 0 else (subtotal * Decimal('0.30') if subtotal > Decimal('2000') else Decimal('0.00'))
        delivery_charge = Decimal('40.00') if request.POST.get('express_delivery') == 'on' else (Decimal('0.00') if subtotal > Decimal('1000') else Decimal('50.00'))
        total = subtotal + tax + delivery_charge - discount

        user = request.user if request.user.is_authenticated else None

        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            country_code = request.POST.get('country_code')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            country = request.POST.get('country')
            street = request.POST.get('street')
            delivery_slot = request.POST.get('delivery_slot')
            payment_method = request.POST.get('payment_method')
            coupon_code = request.POST.get('coupon_code', '')

            if not all([first_name, last_name, email, phone, country, street, delivery_slot, payment_method]):
                return JsonResponse({'success': False, 'error': 'Please fill in all required fields.'}, status=400)

            if country_code == '+91' and not (phone.isdigit() and len(phone) == 10):
                return JsonResponse({'success': False, 'error': 'Please enter a valid 10-digit phone number for India.'}, status=400)

            request.session['first_name'] = first_name
            request.session['last_name'] = last_name
            request.session['country_code'] = country_code
            request.session['phone'] = phone
            request.session['email'] = email
            request.session['country'] = country
            request.session['street'] = street
            request.session['state'] = request.POST.get('state', '')
            request.session['building'] = request.POST.get('building', '')
            request.session['house'] = request.POST.get('house', '')
            request.session['postal'] = request.POST.get('postal', '')
            request.session['zip'] = request.POST.get('zip', '')
            request.session['delivery_slot'] = delivery_slot
            request.session['express_delivery'] = request.POST.get('express_delivery') == 'on'
            request.session['payment_method'] = payment_method
            request.session.modified = True

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            order = Order.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                country_code=country_code,
                country=country,
                state=request.POST.get('state', ''),
                street=street,
                building=request.POST.get('building', ''),
                house=request.POST.get('house', ''),
                postal_code=request.POST.get('postal', ''),
                zip_code=request.POST.get('zip', ''),
                delivery_slot=delivery_slot,
                express_delivery=request.POST.get('express_delivery') == 'on',
                payment_method=payment_method,
                coupon_code=coupon_code,
                subtotal=subtotal,
                tax=tax,
                delivery_charge=delivery_charge,
                discount=discount,
                total=total,
                order_status='pending',
                payment_status='pending' if payment_method in ['upi', 'credit'] else 'completed'
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_id=item['product'].id,
                    product_name=item['product'].product_name,
                    price=Decimal(item['product'].price),
                    image1=item['product'].image1 if getattr(item['product'], 'image1', None) else None,
                    image2=item['product'].image2 if getattr(item['product'], 'image2', None) else None,
                    quantity=item['quantity'],
                    color=item['color'],
                    size=item['size'],
                    total_price=item['total_price']
                )

            if payment_method in ['upi', 'credit']:
                order_data = {
                    'amount': int(total * 100),
                    'currency': 'INR',
                    'receipt': f'order_{order.id}',
                    'payment_capture': 1
                }
                try:
                    razorpay_order = client.order.create(data=order_data)
                    order.razorpay_order_id = razorpay_order['id']
                    order.save()
                    logger.debug(f"Razorpay order created: {razorpay_order['id']}")
                    return JsonResponse({
                        'success': True,
                        'razorpay_order_id': razorpay_order['id'],
                        'amount': order_data['amount'],
                        'order_detail_url': reverse('order_success', args=[order.id])
                    })
                except razorpay.errors.BadRequestError as e:
                    order.order_status = 'cancelled'
                    order.payment_status = 'failed'
                    order.save()
                    logger.error(f"Razorpay error: {str(e)}")
                    return JsonResponse({'success': False, 'error': f'Razorpay error: {str(e)}'}, status=400)
            else:
                order.order_status = 'confirmed'
                order.payment_status = 'completed'
                order.save()
                request.session['cart'] = {}
                request.session['discount'] = 0
                request.session.modified = True
                sync_session_with_cart(request, cart)
                logger.debug(f"Order {order.id} confirmed for COD")
                return JsonResponse({
                    'success': True,
                    'order_detail_url': reverse('order_success', args=[order.id])
                })
        else:
            form_data = {
                'first_name': request.POST.get('first_name') or request.session.get('first_name') or (user.first_name if user else ''),
                'last_name': request.POST.get('last_name') or request.session.get('last_name') or (user.last_name if user else ''),
                'email': request.POST.get('email') or request.session.get('email') or (user.email if user else ''),
                'phone': request.POST.get('phone') or request.session.get('phone') or (user.phone_number if user and hasattr(user, 'phone_number') else ''),
                'country_code': request.POST.get('country_code') or request.session.get('country_code', '+91'),
                'country': request.POST.get('country') or request.session.get('country', 'IN'),
                'state': request.POST.get('state') or request.session.get('state', ''),
                'street': request.POST.get('street') or request.session.get('street', ''),
                'building': request.POST.get('building') or request.session.get('building', ''),
                'house': request.POST.get('house') or request.session.get('house', ''),
                'postal': request.POST.get('postal') or request.session.get('postal', ''),
                'zip': request.POST.get('zip') or request.session.get('zip', ''),
                'delivery_slot': request.POST.get('delivery_slot') or request.session.get('delivery_slot', ''),
                'express_delivery': request.POST.get('express_delivery') == 'on' or request.session.get('express_delivery', False),
                'payment_method': request.POST.get('payment_method') or request.session.get('payment_method', 'upi'),
                'coupon_code': request.session.get('coupon_code', '')
            }

            context = {
                'cart_items': cart_items,
                'subtotal': float(subtotal),
                'tax': float(tax),
                'delivery_charge': float(delivery_charge),
                'discount': float(discount),
                'total': float(total),
                'form_data': form_data,
                'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID
            }
            return render(request, 'store/place_order.html', context)
    except Exception as e:
        logger.error(f"Error in place_order: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Server error: {str(e)}"
        }, status=500)

@csrf_exempt
def verify_payment(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

        data = json.loads(request.body)
        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        client.utility.verify_payment_signature(params_dict)
        order = get_object_or_404(Order, razorpay_order_id=params_dict['razorpay_order_id'])
        order.payment_status = 'completed'
        order.order_status = 'confirmed'
        order.save()
        request.session['cart'] = {}
        request.session['discount'] = 0
        request.session.modified = True
        sync_session_with_cart(request, get_or_create_cart(request))
        return JsonResponse({
            'success': True,
            'order_detail_url': reverse('order_success', args=[order.id])
        })
    except json.JSONDecodeError:
        logger.error("Invalid JSON in verify_payment")
        return JsonResponse({'success': False, 'error': 'Invalid payment data'}, status=400)
    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"Payment verification failed: {str(e)}")
        order = get_object_or_404(Order, razorpay_order_id=params_dict['razorpay_order_id'])
        order.payment_status = 'failed'
        order.order_status = 'cancelled'
        order.save()
        return JsonResponse({'success': False, 'error': f'Payment verification failed: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in verify_payment: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)

def order_success(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)

        if order.order_status != 'confirmed':
            messages.error(request, "Order is not confirmed yet.")
            return redirect('cart')

        order_items = OrderItem.objects.filter(order=order)
        subtotal = sum(item.price * item.quantity for item in order_items)
        qr_code = generate_order_qr_code(order)

        try:
            send_order_confirmation_email(request, order, order_items)
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")

        context = {
            'order': order,
            'order_items': order_items,
            'subtotal': float(subtotal),
            'qr_code': qr_code,
        }
        return render(request, 'store/order_success.html', context)
    except Exception as e:
        logger.error(f"Error in order_success: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Server error: {str(e)}"
        }, status=500)

def send_order_confirmation_email(request, order, order_items):
    try:
        subject = f"Order #{order.id} Confirmation"
        to_email = order.email
        from_email = settings.DEFAULT_FROM_EMAIL
        qr_data = f"Order ID: {order.id}\nName: {order.first_name} {order.last_name}\nTotal: ₹{order.total}"
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_img_data = buffer.getvalue()
        track_url = request.build_absolute_uri(reverse('track_order', args=[order.id]))
        account_url = request.build_absolute_uri(reverse('my_account'))
        html_content = render_to_string('emails/order_confirmation_email.html', {
            'order': order,
            'order_items': order_items,
            'track_url': track_url,
            'account_url': account_url,
        })
        email = EmailMultiAlternatives(subject, '', from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        image = MIMEImage(qr_img_data)
        image.add_header('Content-ID', '<order_qr_code>')
        image.add_header('Content-Disposition', 'inline', filename="order_qr.png")
        email.attach(image)
        email.send()
    except Exception as e:
        logger.error(f"Error in send_order_confirmation_email: {str(e)}")
        raise