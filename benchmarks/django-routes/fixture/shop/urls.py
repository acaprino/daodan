from django.urls import path

from shop.views import pages, products

app_name = "shop"
urlpatterns = [
    path("", pages.home, name="home"),
    path("products/", products.ProductList.as_view(), name="products"),
    path("products/<int:pk>/", products.ProductDetail.as_view(), name="product"),
    path("generic/", products.ProductGeneric.as_view(), name="generic"),
    path("decorated/", products.DecoratedGeneric.as_view(), name="decorated"),
    path("mixed/", products.Mixed.as_view(), name="mixed"),
    path("own-head/", products.OwnHead.as_view(), name="own-head"),
    path("cart/", pages.cart, name="cart"),
    path("lambda/", lambda request: None),
]
