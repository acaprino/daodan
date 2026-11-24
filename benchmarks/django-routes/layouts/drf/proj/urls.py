from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()
router.register("items", views.ItemViewSet, basename="item")
router.register("readonly", views.ReadOnlyViewSet, basename="readonly")

urlpatterns = [
    path("v1/", include(router.urls)),
    path("ping/", views.Ping.as_view()),
    path("listed/", views.Listed.as_view()),
    path("status/", views.status),
]
