from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import User
from applications.models import Application, ApplicationStatusHistory, Interview
from companies.models import CompanyProfile
from internships.models import Internship
from students.models import StudentProfile


def platform_admin_required(*permissions):
    def decorator(view):
        @wraps(view)
        @login_required(login_url='platform_admin:login')
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_active or not request.user.is_staff:
                raise PermissionDenied
            if permissions and not request.user.has_perms(permissions):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped_view

    return decorator


def platform_admin_login(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('platform_admin:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active or not user.is_staff:
                form.add_error(
                    None,
                    'This login page is for platform administrators only.',
                )
            else:
                login(request, user)
                messages.success(request, 'Welcome to platform management.')
                if url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect('platform_admin:dashboard')
    else:
        form = AuthenticationForm()

    return render(
        request,
        'platform_admin/login.html',
        {'form': form, 'next': next_url},
    )


@platform_admin_required()
@require_POST
def platform_admin_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out of platform management.')
    return redirect('platform_admin:login')


def _activity_feed():
    activities = []
    for application in (
        Application.objects.select_related(
            'student__user',
            'internship__company',
        )
        .order_by('-applied_date')[:8]
    ):
        activities.append(
            {
                'created_at': application.applied_date,
                'title': 'New application',
                'description': (
                    f'{application.student.full_name} applied for '
                    f'{application.internship.title} at '
                    f'{application.internship.company.company_name}.'
                ),
            },
        )

    for event in (
        ApplicationStatusHistory.objects.select_related(
            'application__student',
            'application__internship__company',
            'changed_by',
        )
        .exclude(changed_by__isnull=True)
        .order_by('-created_at')[:8]
    ):
        activities.append(
            {
                'created_at': event.created_at,
                'title': f'Application {event.get_status_display().lower()}',
                'description': (
                    f'{event.application.student.full_name} · '
                    f'{event.application.internship.title} · updated by '
                    f'{event.changed_by.get_full_name() or event.changed_by.username}.'
                ),
            },
        )

    for internship in (
        Internship.objects.select_related('company')
        .order_by('-created_at')[:8]
    ):
        activities.append(
            {
                'created_at': internship.created_at,
                'title': 'Internship posted',
                'description': (
                    f'{internship.company.company_name} posted '
                    f'{internship.title}.'
                ),
            },
        )

    for interview in (
        Interview.objects.select_related(
            'application__student',
            'application__internship',
        )
        .order_by('-updated_at')[:8]
    ):
        activities.append(
            {
                'created_at': interview.updated_at,
                'title': 'Interview scheduled or updated',
                'description': (
                    f'{interview.application.student.full_name} · '
                    f'{interview.application.internship.title} · '
                    f'{interview.scheduled_at:%b %d, %Y %I:%M %p}.'
                ),
            },
        )

    return sorted(
        activities,
        key=lambda activity: activity['created_at'],
        reverse=True,
    )[:12]


@platform_admin_required(
    'accounts.view_user',
    'students.view_studentprofile',
    'companies.view_companyprofile',
    'internships.view_internship',
    'applications.view_application',
)
def platform_dashboard(request):
    return render(
        request,
        'platform_admin/dashboard.html',
        {
            'total_students': User.objects.filter(
                role=User.Role.STUDENT,
                is_staff=False,
            ).count(),
            'total_companies': CompanyProfile.objects.count(),
            'total_internships': Internship.objects.count(),
            'total_applications': Application.objects.count(),
            'pending_applications': Application.objects.filter(
                status=Application.Status.PENDING,
            ).count(),
            'recent_activities': _activity_feed(),
        },
    )


@platform_admin_required('students.view_studentprofile', 'accounts.view_user')
def student_management(request):
    query = request.GET.get('q', '').strip()
    active_filter = request.GET.get('active', '')
    students = User.objects.filter(
        role=User.Role.STUDENT,
        is_staff=False,
    ).select_related('student_profile')
    if query:
        students = students.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(student_profile__full_name__icontains=query)
            | Q(student_profile__college__icontains=query)
            | Q(student_profile__department__icontains=query)
        )
    if active_filter in {'active', 'inactive'}:
        students = students.filter(is_active=active_filter == 'active')

    page = Paginator(students.order_by('-date_joined'), 20).get_page(
        request.GET.get('page'),
    )
    return render(
        request,
        'platform_admin/management_list.html',
        {
            'page': page,
            'query': query,
            'active_filter': active_filter,
            'list_type': 'students',
            'page_title': 'Student management',
            'page_description': 'Search student accounts and review their profiles.',
        },
    )


@platform_admin_required('companies.view_companyprofile', 'accounts.view_user')
def company_management(request):
    query = request.GET.get('q', '').strip()
    active_filter = request.GET.get('active', '')
    companies = CompanyProfile.objects.select_related('user')
    if query:
        companies = companies.filter(
            Q(company_name__icontains=query)
            | Q(contact_person__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
            | Q(location__icontains=query)
        )
    if active_filter in {'active', 'inactive'}:
        companies = companies.filter(
            user__is_active=active_filter == 'active',
        )

    page = Paginator(companies.order_by('company_name'), 20).get_page(
        request.GET.get('page'),
    )
    return render(
        request,
        'platform_admin/management_list.html',
        {
            'page': page,
            'query': query,
            'active_filter': active_filter,
            'list_type': 'companies',
            'page_title': 'Company management',
            'page_description': 'Search company accounts and review recruiter profiles.',
        },
    )


@platform_admin_required('internships.view_internship')
def internship_management(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    internships = Internship.objects.select_related('company').annotate(
        application_count=Count('applications'),
    )
    if query:
        internships = internships.filter(
            Q(title__icontains=query)
            | Q(company__company_name__icontains=query)
            | Q(location__icontains=query)
        )
    valid_statuses = {status.value for status in Internship.Status}
    if status_filter in valid_statuses:
        internships = internships.filter(status=status_filter)

    page = Paginator(internships.order_by('-created_at'), 20).get_page(
        request.GET.get('page'),
    )
    return render(
        request,
        'platform_admin/management_list.html',
        {
            'page': page,
            'query': query,
            'status_filter': status_filter,
            'status_choices': Internship.Status.choices,
            'list_type': 'internships',
            'page_title': 'Internship management',
            'page_description': 'Review and manage platform internship postings.',
        },
    )


@platform_admin_required('internships.change_internship')
@require_POST
def internship_status_update(request, pk, action):
    internship = get_object_or_404(Internship, pk=pk)
    if action == 'activate':
        internship.status = Internship.Status.OPEN
        message = f'{internship.title} is now active.'
    elif action == 'deactivate':
        internship.status = Internship.Status.CLOSED
        message = f'{internship.title} has been deactivated.'
    else:
        raise PermissionDenied

    internship.save(update_fields=['status', 'updated_at'])
    messages.success(request, message)
    return redirect('platform_admin:internships')


@platform_admin_required('internships.delete_internship')
@require_POST
def internship_delete(request, pk):
    internship = get_object_or_404(Internship, pk=pk)
    title = internship.title
    try:
        internship.delete()
    except ProtectedError:
        messages.error(
            request,
            'This internship has applications and cannot be deleted. Deactivate it instead.',
        )
    else:
        messages.success(request, f'{title} was deleted.')
    return redirect('platform_admin:internships')


@platform_admin_required('applications.view_application')
def application_monitoring(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    applications = Application.objects.select_related(
        'student__user',
        'internship__company',
    )
    if query:
        applications = applications.filter(
            Q(student__full_name__icontains=query)
            | Q(student__user__email__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(internship__title__icontains=query)
            | Q(internship__company__company_name__icontains=query)
        )
    valid_statuses = {status.value for status in Application.Status}
    if status_filter in valid_statuses:
        applications = applications.filter(status=status_filter)

    page = Paginator(applications.order_by('-applied_date'), 20).get_page(
        request.GET.get('page'),
    )
    return render(
        request,
        'platform_admin/management_list.html',
        {
            'page': page,
            'query': query,
            'status_filter': status_filter,
            'status_choices': Application.Status.choices,
            'list_type': 'applications',
            'page_title': 'Application monitoring',
            'page_description': 'Monitor applications across all platform internships.',
        },
    )
