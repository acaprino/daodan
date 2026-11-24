from django.http import HttpResponse
from django.urls import path


def view_b(request):
    return HttpResponse("view_b")


urlpatterns = [path("view_b/", view_b)]
