from django.http import HttpResponse
from django.urls import include, path


def own(request):
    return HttpResponse("own")


urlpatterns = [path("own/", own), path("shared/", include("sharedlib.urls"))]
