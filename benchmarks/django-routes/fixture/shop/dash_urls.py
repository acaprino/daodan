from django.urls import path

from shop.views import pages

urlpatterns = [
    path("", pages.home),
    path("report/<int:n>/", pages.report),
]
