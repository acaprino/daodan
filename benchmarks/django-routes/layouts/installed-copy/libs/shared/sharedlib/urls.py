from django.urls import path

from sharedlib.views import shared_view

urlpatterns = [path("view/", shared_view)]
