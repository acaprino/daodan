from django.http import HttpResponse
from django.urls import path


def view_a(request):
    return HttpResponse("view_a")


urlpatterns = [path("view_a/", view_a)]
