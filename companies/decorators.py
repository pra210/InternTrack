from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from accounts.models import User

from .models import CompanyProfile


def company_required(view_func):
    @wraps(view_func)
    @login_required(login_url='companies:login')
    def wrapped_view(request, *args, **kwargs):
        if request.user.role != User.Role.COMPANY:
            messages.error(request, 'This page is for company accounts only.')
            return redirect('home')
        company = CompanyProfile.objects.filter(user=request.user).first()
        if company is None:
            messages.error(
                request,
                'Your company account does not have a company profile yet.',
            )
            return redirect('home')
        request.company_profile = company
        return view_func(request, *args, **kwargs)

    return wrapped_view
