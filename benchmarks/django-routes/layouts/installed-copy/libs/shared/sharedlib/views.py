from django.http import HttpResponse


def shared_view(request):
    return HttpResponse("shared")
