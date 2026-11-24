import functools

from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path, register_converter
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView, TemplateView

from shop import converters
from shop.views import pages, products

register_converter(converters.FourDigits, "yyyy")
register_converter(converters.Pair, "pair")


def without_wraps(view):
    def wrapper(request, *args, **kwargs):
        return view(request, *args, **kwargs)

    return wrapper


urlpatterns = [
    path("admin/", admin.site.urls),
    path("shop/", include("shop.urls")),
    path("api/", include(("shop.api_urls", "api"))),
    path("about/", TemplateView.as_view(template_name="about.html")),
    path("go/", RedirectView.as_view(url="/shop/")),
    path("blog/<int:year>/<slug:slug>/", pages.post),
    path("files/<path:rest>", pages.serve_file),
    path("assets/<path:name>", products.Assets.as_view()),
    re_path(r"^regex-class/$", products.ProductList.as_view()),
    path("year/<yyyy:year>/", pages.by_year),
    path("pair/<pair:p>/", pages.pair),
    path("token/<uuid:token>/", pages.token),
    path("<str:tenant>/dash/", include("shop.dash_urls")),
    re_path(r"^legacy/(?P<year>[0-9]{4})/$", pages.archive),
    re_path(r"^optional/(?:(?P<n>[0-9]+)/)?$", pages.optional),
    re_path(r"^(alpha|beta)/$", pages.alt),
    path("partial/", functools.partial(pages.generic, kind="x")),
    path("plain-wrapper/", without_wraps(pages.home)),
    path("lambda/", lambda request: None),
    path("async/", pages.fast),
    path("private/", pages.private),
]
urlpatterns += i18n_patterns(
    path("localized/", pages.home),
    path(_("products-i18n/"), products.ProductList.as_view()),
)
urlpatterns += i18n_patterns(path("noprefix/", pages.home), prefix_default_language=False)
urlpatterns += static("media/", document_root="/tmp")
