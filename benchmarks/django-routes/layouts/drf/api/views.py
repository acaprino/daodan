from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Item
from api.serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def list(self, request):
        return Response([])

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        return Response("published")


class ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class Ping(APIView):
    def get(self, request):
        return Response("pong")

    def post(self, request):
        return Response("posted")


class Listed(ListCreateAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


@api_view(["GET", "POST"])
def status(request):
    return Response("ok")
