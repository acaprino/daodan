from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods


def home(request):
    return HttpResponse("home")


@require_http_methods(["GET", "POST"])
def cart(request):
    return HttpResponse("cart")


def archive(request, year):
    return HttpResponse(year)


def post(request, year, slug):
    return HttpResponse(slug)


def serve_file(request, rest):
    return HttpResponse(rest)


def by_year(request, year):
    return HttpResponse(year)


def pair(request, p):
    return HttpResponse(p)


def token(request, token):
    return HttpResponse(token)


def optional(request, n=None):
    return HttpResponse(n)


def alt(request, which):
    return HttpResponse(which)


def generic(request, kind):
    return HttpResponse(kind)


def report(request, tenant, n):
    return HttpResponse(n)


@require_GET
async def fast(request):
    return HttpResponse("fast")


@csrf_exempt
@login_required
def private(request):
    return HttpResponse("private")
