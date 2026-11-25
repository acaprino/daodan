from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView

from shop.mixins import AuditMixin
from shop.models import Product


class ProductList(View):
    def get(self, request):
        return HttpResponse("list")

    def post(self, request):
        return HttpResponse("created")


class ProductDetail(View):
    def get(self, request, pk):
        return HttpResponse(pk)


class ProductGeneric(ListView):
    model = Product


class Mixed(AuditMixin, View):
    def post(self, request):
        return HttpResponse("mixed")


class OwnHead(View):
    def get(self, request):
        return HttpResponse("get")

    def head(self, request):
        return HttpResponse("head")

    def options(self, request, *args, **kwargs):
        return HttpResponse("options")


class Assets(View):
    def get(self, request, name):
        return HttpResponse(name)


@method_decorator(csrf_exempt, name="dispatch")
class DecoratedGeneric(ListView):
    model = Product
