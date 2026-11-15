from django.http import HttpResponse
from django.template.loader import get_template


def _error_response(template_name, status):
    return HttpResponse(
        get_template(template_name).render(),
        status=status,
        content_type='text/html; charset=utf-8',
    )


def permission_denied(request, exception=None):
    return _error_response('errors/403.html', 403)


def page_not_found(request, exception=None):
    return _error_response('errors/404.html', 404)


def server_error(request):
    return _error_response('errors/500.html', 500)
