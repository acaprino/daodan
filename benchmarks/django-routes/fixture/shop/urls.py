from django.urls import path

from shop.views import pages, products

app_name = "shop"
urlpatterns = [
    path("", pages.home, name="home"),
    path("products/", products.ProductList.as_view(), name="products"),
    path("products/<int:pk>/", products.ProductDetail.as_view(), name="product"),
    path("cart/", pages.cart, name="cart"),
    path("lambda/", lambda request: None),
]
