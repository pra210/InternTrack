from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Notification, User
from applications.models import Application
from companies.models import CompanyProfile
from internships.models import Internship
from students.models import StudentProfile


def health_check(request):
    return JsonResponse({'status': 'ok'})


def home(request):
    query = request.GET.get('q', '').strip()
    search_terms = query.split()
    internships = Internship.objects.filter(
        status=Internship.Status.OPEN,
    ).select_related('company').prefetch_related('required_skills')

    for term in search_terms:
        internships = internships.filter(
            Q(title__icontains=term)
            | Q(description__icontains=term)
            | Q(location__icontains=term)
            | Q(company__company_name__icontains=term)
            | Q(required_skills__name__icontains=term)
        )
    internships = internships.distinct()
    internship_count = internships.count()
    if not search_terms:
        internships = internships[:3]

    return render(
        request,
        'pages/home.html',
        {
            'query': query,
            'internships': internships,
            'search_result_count': internship_count,
            'student_count': User.objects.filter(
                role=User.Role.STUDENT,
                is_active=True,
            ).count(),
            'company_count': CompanyProfile.objects.filter(
                user__is_active=True,
            ).count(),
            'internship_count': Internship.objects.filter(
                status=Internship.Status.OPEN,
            ).count(),
            'application_count': Application.objects.count(),
        },
    )


@login_required
def student_dashboard(request):
    if request.user.role != User.Role.STUDENT:
        messages.error(request, 'Only student accounts can access this dashboard.')
        return redirect('home')

    profile, _ = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.get_full_name() or request.user.username},
    )

    application_list = (
        Application.objects.filter(student=profile)
        .select_related('internship__company', 'interview')
        .prefetch_related(
            'internship__required_skills',
            'status_history',
        )
        .order_by('-applied_date')
    )

    status_counts = {status.value: 0 for status in Application.Status}
    for row in application_list.values('status').annotate(total=Count('pk')):
        status_counts[row['status']] = row['total']
    status_counts['INTERVIEWING'] = application_list.filter(
        status__in=[
            Application.Status.REVIEWING,
            Application.Status.INTERVIEWING,
        ],
    ).count()
    total_applications = application_list.count()
    application_page = Paginator(application_list, 10).get_page(
        request.GET.get('page'),
    )
    applications = application_page.object_list

    tracking_steps = (
        ('Applied', ()),
        ('Pending', (Application.Status.PENDING,)),
        ('Shortlisted', (Application.Status.SHORTLISTED,)),
        (
            'Interviewing',
            (Application.Status.REVIEWING, Application.Status.INTERVIEWING),
        ),
    )
    for application in applications:
        history = list(application.status_history.all())
        statuses_seen = {event.status for event in history}
        if not history:
            statuses_seen.add(application.status)
        application.status_events = history
        steps = [
            {
                'label': label,
                'complete': label == 'Applied'
                or bool(set(statuses) & statuses_seen),
                'current': application.status in statuses
                if statuses
                else False,
            }
            for label, statuses in tracking_steps
        ]
        for terminal_status in (
            Application.Status.ACCEPTED,
            Application.Status.REJECTED,
        ):
            steps.append(
                {
                    'label': terminal_status.label,
                    'complete': application.status == terminal_status,
                    'current': application.status == terminal_status,
                }
            )
        application.tracking_steps = steps

    return render(
        request,
        'dashboard/student_dashboard.html',
        {
            'profile': profile,
            'applications': applications,
            'application_page': application_page,
            'total_applications': total_applications,
            'status_counts': status_counts,
            'notifications': Notification.objects.filter(
                user=request.user,
            )[:20],
            'unread_notification_count': Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count(),
            'open_internships': Internship.objects.filter(
                status=Internship.Status.OPEN,
            )
            .select_related('company')
            .prefetch_related('required_skills')
            .order_by('-created_at')[:3],
        },
    )


@login_required
@require_POST
def mark_notification_read(request, pk):
    if request.user.role != User.Role.STUDENT:
        messages.error(request, 'Only students can manage notifications here.')
        return redirect('home')

    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user,
    )
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return redirect('dashboard:student_dashboard')
