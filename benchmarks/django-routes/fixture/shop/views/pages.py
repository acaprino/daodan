from django.http import HttpResponse
from django.views.decorators.http import require_http_methods


def home(request):
    return HttpResponse("home")


@require_http_methods(["GET", "POST"])
def cart(request):
    return HttpResponse("cart")


def archive(request, year):
    return HttpResponse(year)
