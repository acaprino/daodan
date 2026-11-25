from django.urls import path

from shop.views import products

urlpatterns = [
    path("items/", products.ProductList.as_view()),
    path("items/<int:pk>/", products.ProductDetail.as_view()),
]
