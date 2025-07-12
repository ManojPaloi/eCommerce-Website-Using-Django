from django.shortcuts import get_object_or_404, render, redirect
from .models import Product, Review, ReviewInteraction, Wishlist
from category.models import Category
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from carts.views import get_or_create_cart, sync_session_with_cart
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from carts.models import CartItem
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

def store(request, category_slug=None):
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)

    # Category filter
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # Search filter
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(product_name__icontains=search_query)

    # Price filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        try:
            products = products.filter(price__gte=int(min_price), price__lte=int(max_price))
        except ValueError:
            pass

    # Sizes filter
    selected_sizes = request.GET.getlist('sizes')
    if selected_sizes:
        products = products.filter(size__in=selected_sizes)

    # Pagination
    paginator = Paginator(products, 6)  # 6 products per page
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Wishlist product IDs for authenticated users
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product__id', flat=True)

    context = {
        'categories': categories,
        'products': paged_products,
        'product_count': products.count(),
        'sizes_list': ['XS', 'SM', 'M', 'L', 'XL', 'XXL'],
        'selected_sizes': selected_sizes,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'search_query': search_query or '',
        'current_category_slug': category_slug,
        'wishlist_product_ids': wishlist_product_ids,
    }

    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    # Fetch the product, ensuring it's available
    single_product = get_object_or_404(
        Product,
        category__slug=category_slug,
        slug=product_slug,
        is_available=True
    )

    # Fetch reviews for the product
    reviews = single_product.reviews.all().order_by('-created_at')

    # Add like/dislike counts to each review
    for review in reviews:
        review.total_likes = review.interactions.filter(interaction_type='like').count()
        review.total_dislikes = review.interactions.filter(interaction_type='dislike').count()
        if request.user.is_authenticated:
            review.user_interaction = review.interactions.filter(user=request.user).first()
        else:
            review.user_interaction = None

    # Fetch recommended products (same category, exclude current product)
    recommended_products = Product.objects.filter(
        category=single_product.category,
        is_available=True
    ).exclude(id=single_product.id)[:4]

    # Wishlist product IDs for authenticated users
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product__id', flat=True)

    context = {
        'single_product': single_product,
        'reviews': reviews,
        'recommended_products': recommended_products,
        'wishlist_product_ids': wishlist_product_ids,
        'size_choices': CartItem.SIZE_CHOICES,  # Added to provide size options
    }
    return render(request, 'store/product_detail.html', context)

# @require_POST
# def add_to_cart(request, product_id):
#     # Get or create cart
#     cart = get_or_create_cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # Get quantity from POST data
#     try:
#         quantity = int(request.POST.get('quantity', 1))
#         if quantity < 1:
#             quantity = 1
#     except (TypeError, ValueError):
#         quantity = 1

#     # Get color and size from POST data
#     color_option = request.POST.get('color_option', '')
#     size_option = request.POST.get('size_option', '')

#     # Check stock availability
#     if quantity > product.stock:
#         messages.error(request, f"Sorry, only {product.stock} units of {product.product_name} are available.")
#         return redirect(request.META.get('HTTP_REFERER', '/'))

#     # Get session cart
#     session_cart = request.session.get('cart', {})

#     # Create a unique key based on product_id, color and size
#     cart_key = f"{product_id}_{color_option}_{size_option}"
    
#     # Update session cart with the unique key
#     session_cart[cart_key] = session_cart.get(cart_key, 0) + quantity

#     # Save session cart
#     request.session['cart'] = session_cart
#     request.session.modified = True

#     # Sync with Cart and CartItem models
#     sync_session_with_cart(request, cart)

#     messages.success(request, f"{product.product_name} has been added to your cart!")
    
#     # Check if this is a "Buy Now" action
#     if request.POST.get('buy_now') == 'true':
#         return redirect('place_order')
    
#     return redirect(request.META.get('HTTP_REFERER', '/'))

def search(request):
    categories = Category.objects.all()
    sizes_list = ['XS', 'SM', 'M', 'L', 'XL', 'XXL']
    selected_sizes = request.GET.getlist('sizes')
    keyword = request.GET.get('keyword', '').strip()

    products = Product.objects.filter(is_available=True)

    if keyword:
        products = products.filter(
            Q(product_name__icontains=keyword) | Q(description__icontains=keyword)
        )

    if selected_sizes:
        products = products.filter(size__in=selected_sizes)

    # Pagination
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Wishlist product IDs for authenticated users
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product__id', flat=True)

    context = {
        'categories': categories,
        'sizes_list': sizes_list,
        'selected_sizes': selected_sizes,
        'products': paged_products,
        'keyword': keyword,
        'product_count': products.count(),
        'wishlist_product_ids': wishlist_product_ids,
    }

    return render(request, 'store/store.html', context)

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = int(request.POST.get('rating'))
        review_text = request.POST.get('review_text')
        if rating not in range(1, 6) or not review_text.strip():
            messages.error(request, 'Please provide a valid rating and review.')
            return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)
        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            review_text=review_text
        )
        messages.success(request, 'Thank you for your review!')
    return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

@login_required
@require_POST
def review_interaction(request):
    data = json.loads(request.body)
    review_id = data.get('review_id')
    interaction_type = data.get('interaction_type')

    if interaction_type not in ['like', 'dislike']:
        return JsonResponse({'status': 'error', 'message': 'Invalid interaction type'}, status=400)

    review = get_object_or_404(Review, id=review_id)
    user = request.user

    # Check if the user already interacted
    interaction = ReviewInteraction.objects.filter(review=review, user=user).first()

    if interaction:
        if interaction.interaction_type == interaction_type:
            # User is clicking the same button again (toggle off)
            interaction.delete()
            action = 'removed'
        else:
            # User is switching from like to dislike or vice versa
            interaction.interaction_type = interaction_type
            interaction.save()
            action = 'updated'
    else:
        # New interaction
        ReviewInteraction.objects.create(review=review, user=user, interaction_type=interaction_type)
        action = 'added'

    # Recalculate totals
    total_likes = review.interactions.filter(interaction_type='like').count()
    total_dislikes = review.interactions.filter(interaction_type='dislike').count()

    return JsonResponse({
        'status': 'success',
        'action': action,
        'interaction_type': interaction_type,
        'total_likes': total_likes,
        'total_dislikes': total_dislikes,
    })

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'store/wishlist.html', context)

@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        wishlist.delete()
        messages.success(request, f"{product.product_name} removed from your wishlist!")
        return JsonResponse({'status': 'removed'})
    
    messages.success(request, f"{product.product_name} added to your wishlist!")
    return JsonResponse({'status': 'added'})