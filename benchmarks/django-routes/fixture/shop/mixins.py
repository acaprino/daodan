from django.http import HttpResponse


class AuditMixin:
    def get(self, request, *args, **kwargs):
        return HttpResponse("audit")
