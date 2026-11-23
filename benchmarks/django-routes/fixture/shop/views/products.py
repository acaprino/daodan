from django.http import HttpResponse
from django.views import View


class ProductList(View):
    def get(self, request):
        return HttpResponse("list")

    def post(self, request):
        return HttpResponse("created")


class ProductDetail(View):
    def get(self, request, pk):
        return HttpResponse(pk)
