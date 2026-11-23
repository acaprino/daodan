from django.urls import include, path, re_path

from shop.views import pages

urlpatterns = [
    path("shop/", include("shop.urls")),
    re_path(r"^legacy/(?P<year>[0-9]{4})/$", pages.archive),
]
