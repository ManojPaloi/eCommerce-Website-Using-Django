from django.shortcuts import render
from django.db.models import Q
from store.models import Product
from category.models import Category


def home(request):
    # Get categories that are associated with a store (has_store=True)
    categories_with_store = Category.objects.filter(has_store=True).distinct()

    # Get products, excluding those in categories associated with a store
    products = Product.objects.filter(
        Q(category__in=categories_with_store) & Q(is_available=True)
    ).order_by("-created_date")[:9]

    # Get featured categories (where has_store=False, limit to 4)
    featured_categories = Category.objects.filter(has_store=False)[:4]

    context = {"products": products, "featured_categories": featured_categories}
    return render(request, "index.html", context)
