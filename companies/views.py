import logging
import mimetypes
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import Notification, User
from applications.models import (
    Application,
    ApplicationStatusHistory,
    Interview,
)
from internships.models import Internship

from .decorators import company_required
from .forms import (
    ApplicationStatusForm,
    CompanyProfileForm,
    CompanyRegistrationForm,
    InterviewForm,
    InternshipForm,
)
from .models import CompanyProfile

logger = logging.getLogger(__name__)


def _authenticated_redirect(user):
    if user.role == User.Role.COMPANY:
        return redirect('companies:dashboard')
    if user.role == User.Role.STUDENT:
        return redirect('dashboard:student_dashboard')
    return redirect('home')


def company_register(request):
    if request.user.is_authenticated:
        return _authenticated_redirect(request.user)

    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(
                request,
                user,
                backend='django.contrib.auth.backends.ModelBackend',
            )
            messages.success(
                request,
                'Your company account has been created successfully.',
            )
            return redirect('companies:dashboard')
    else:
        form = CompanyRegistrationForm()

    return render(request, 'companies/register.html', {'form': form})


def company_login(request):
    if request.user.is_authenticated:
        return _authenticated_redirect(request.user)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role != User.Role.COMPANY:
                form.add_error(
                    None,
                    'This login page is for company accounts only.',
                )
            elif not CompanyProfile.objects.filter(user=user).exists():
                form.add_error(
                    None,
                    'This company account does not have a company profile.',
                )
            else:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('companies:dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'companies/login.html', {'form': form})


@company_required
@require_POST
def company_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out of your company account.')
    return redirect('home')


@company_required
def company_dashboard(request):
    company = request.company_profile
    applications = Application.objects.filter(internship__company=company)

    return render(
        request,
        'companies/dashboard.html',
        {
            'company': company,
            'total_internships': company.internships.count(),
            'active_internships': company.internships.filter(
                status=Internship.Status.OPEN,
            ).count(),
            'total_applicants': applications.values('student_id').distinct().count(),
            'pending_applications': applications.filter(
                status=Application.Status.PENDING,
            ).count(),
            'shortlisted_candidates': applications.filter(
                status=Application.Status.SHORTLISTED,
            ).values('student_id').distinct().count(),
            'recent_internships': company.internships.annotate(
                applicant_count=Count('applications'),
            ).order_by('-created_at')[:5],
            'recent_applicants': applications.select_related(
                'student__user',
                'internship',
            )[:5],
            'upcoming_interviews': Interview.objects.filter(
                application__internship__company=company,
                scheduled_at__gte=timezone.now(),
            )
            .select_related(
                'application__student__user',
                'application__internship',
            )
            .order_by('scheduled_at')[:10],
        },
    )


@company_required
def company_profile(request):
    return render(
        request,
        'companies/profile.html',
        {'company': request.company_profile},
    )


@company_required
def company_logo(request):
    logo = request.company_profile.logo
    if not logo:
        return redirect('companies:profile')
    try:
        if not logo.storage.exists(logo.name):
            messages.error(request, 'The company logo file is unavailable.')
            return redirect('companies:profile')
        logo_file = logo.open('rb')
    except OSError:
        logger.exception(
            'Company logo storage failed for company_id=%s',
            request.company_profile.pk,
        )
        messages.error(request, 'The company logo file is unavailable.')
        return redirect('companies:profile')
    return FileResponse(
        logo_file,
        content_type=mimetypes.guess_type(Path(logo.name).name)[0]
        or 'application/octet-stream',
    )


@company_required
def company_profile_edit(request):
    if request.method == 'POST':
        form = CompanyProfileForm(
            request.POST,
            request.FILES,
            instance=request.company_profile,
        )
        if form.is_valid():
            try:
                form.save()
            except OSError:
                logger.exception(
                    'Company profile file storage failed for company_id=%s',
                    request.company_profile.pk,
                )
                messages.error(
                    request,
                    'We could not save the uploaded company image. Please try again.',
                )
            else:
                messages.success(
                    request,
                    'Your company profile has been updated.',
                )
                return redirect('companies:profile')
    else:
        form = CompanyProfileForm(instance=request.company_profile)

    return render(
        request,
        'companies/profile_form.html',
        {'company': request.company_profile, 'form': form},
    )


@company_required
def internship_list(request):
    internships = request.company_profile.internships.annotate(
        applicant_count=Count('applications'),
    )
    return render(
        request,
        'companies/internship_list.html',
        {'company': request.company_profile, 'internships': internships},
    )


@company_required
def internship_create(request):
    if request.method == 'POST':
        form = InternshipForm(request.POST)
        if form.is_valid():
            internship = form.save(commit=False)
            internship.company = request.company_profile
            internship.save()
            form.save_m2m()
            messages.success(request, 'Your internship posting has been created.')
            return redirect('companies:internship_list')
    else:
        form = InternshipForm()

    return render(
        request,
        'companies/internship_form.html',
        {
            'company': request.company_profile,
            'form': form,
            'page_title': 'Create internship',
        },
    )


@company_required
def internship_edit(request, pk):
    internship = get_object_or_404(
        Internship,
        pk=pk,
        company=request.company_profile,
    )
    if request.method == 'POST':
        form = InternshipForm(request.POST, instance=internship)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your internship posting has been updated.')
            return redirect('companies:internship_list')
    else:
        form = InternshipForm(instance=internship)

    return render(
        request,
        'companies/internship_form.html',
        {
            'company': request.company_profile,
            'form': form,
            'internship': internship,
            'page_title': 'Edit internship',
        },
    )


@company_required
@require_http_methods(['GET', 'POST'])
def internship_delete(request, pk):
    internship = get_object_or_404(
        Internship,
        pk=pk,
        company=request.company_profile,
    )
    if request.method == 'POST':
        if internship.applications.exists():
            messages.error(
                request,
                'This internship has applications and cannot be deleted. Close it instead.',
            )
            return redirect('companies:internship_list')
        internship.delete()
        messages.success(request, 'The internship posting has been deleted.')
        return redirect('companies:internship_list')

    return render(
        request,
        'companies/internship_confirm_delete.html',
        {'company': request.company_profile, 'internship': internship},
    )


@company_required
def internship_applicants(request, pk):
    internship = get_object_or_404(
        Internship,
        pk=pk,
        company=request.company_profile,
    )
    applications = internship.applications.select_related(
        'student__user',
    ).prefetch_related('student__skills')
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    if query:
        applications = applications.filter(
            Q(student__full_name__icontains=query)
            | Q(student__user__email__icontains=query)
            | Q(student__user__username__icontains=query)
        )
    if status_filter in {status.value for status in Application.Status}:
        applications = applications.filter(status=status_filter)
    page = Paginator(applications, 25).get_page(request.GET.get('page'))
    return render(
        request,
        'companies/applicants.html',
        {
            'company': request.company_profile,
            'internship': internship,
            'applications': page,
            'page': page,
            'query': query,
            'status_filter': status_filter,
            'status_choices': Application.Status.choices,
        },
    )


@company_required
def application_detail(request, pk):
    application = get_object_or_404(
        Application.objects.select_related(
            'student__user',
            'internship__company',
        ).prefetch_related('student__skills', 'status_history'),
        pk=pk,
        internship__company=request.company_profile,
    )
    form = ApplicationStatusForm(instance=application)
    interview = Interview.objects.filter(application=application).first()
    interview_form = InterviewForm(instance=interview)
    return render(
        request,
        'companies/application_detail.html',
        {
            'company': request.company_profile,
            'application': application,
            'student': application.student,
            'form': form,
            'status_history': application.status_history.all(),
            'interview': interview,
            'interview_form': interview_form,
        },
    )


@company_required
@require_POST
def application_status_update(request, pk):
    application = get_object_or_404(
        Application.objects.select_related(
            'student__user',
            'internship__company',
        ),
        pk=pk,
        internship__company=request.company_profile,
    )
    previous_status = application.status
    form = ApplicationStatusForm(request.POST, instance=application)
    if form.is_valid():
        updated_application = form.save(commit=False)
        if updated_application.status != previous_status:
            with transaction.atomic():
                updated_application.save()
                ApplicationStatusHistory.objects.create(
                    application=application,
                    status=application.status,
                    changed_by=request.user,
                )
                Notification.objects.create(
                    user=application.student.user,
                    message=(
                        f'Your application for {application.internship.title} at '
                        f'{application.internship.company.company_name} is now '
                        f'{application.get_status_display()}.'
                    ),
                )
        messages.success(request, 'The application status has been updated.')
    else:
        messages.error(request, 'Choose a valid application status.')
    return redirect('companies:application_detail', pk=application.pk)


@company_required
@require_POST
def interview_schedule(request, pk):
    application = get_object_or_404(
        Application.objects.select_related(
            'student__user',
            'internship__company',
        ),
        pk=pk,
        internship__company=request.company_profile,
    )
    if application.status not in {
        Application.Status.SHORTLISTED,
        Application.Status.REVIEWING,
        Application.Status.INTERVIEWING,
    }:
        messages.error(
            request,
            'Only shortlisted or interviewing candidates can be scheduled.',
        )
        return redirect('companies:application_detail', pk=application.pk)

    interview = Interview.objects.filter(application=application).first()
    form = InterviewForm(request.POST, instance=interview)
    if form.is_valid():
        is_new = interview is None
        with transaction.atomic():
            interview = form.save(commit=False)
            interview.application = application
            interview.save()

            if application.status == Application.Status.SHORTLISTED:
                application.status = Application.Status.INTERVIEWING
                application.save(update_fields=['status'])
                ApplicationStatusHistory.objects.create(
                    application=application,
                    status=application.status,
                    changed_by=request.user,
                )
                Notification.objects.create(
                    user=application.student.user,
                    message=(
                        f'Your application for {application.internship.title} '
                        'has moved to Interviewing.'
                    ),
                )

            scheduled_time = timezone.localtime(interview.scheduled_at)
            action = 'scheduled' if is_new else 'updated'
            Notification.objects.create(
                user=application.student.user,
                message=(
                    f'An interview for {application.internship.title} at '
                    f'{application.internship.company.company_name} was '
                    f'{action} for {scheduled_time:%b %d, %Y at %I:%M %p} '
                    f'({interview.get_mode_display()}).'
                ),
            )

        messages.success(
            request,
            'The interview has been scheduled.'
            if is_new
            else 'The interview schedule has been updated.',
        )
        return redirect('companies:application_detail', pk=application.pk)

    return render(
        request,
        'companies/application_detail.html',
        {
            'company': request.company_profile,
            'application': application,
            'student': application.student,
            'form': ApplicationStatusForm(instance=application),
            'status_history': application.status_history.all(),
            'interview': interview,
            'interview_form': form,
        },
    )


@company_required
def application_resume(request, pk):
    application = get_object_or_404(
        Application.objects.select_related('student'),
        pk=pk,
        internship__company=request.company_profile,
    )
    resume = application.student.resume
    if not resume:
        messages.error(request, 'This student has not uploaded a resume.')
        return redirect('companies:application_detail', pk=application.pk)
    try:
        if not resume.storage.exists(resume.name):
            messages.error(request, 'The uploaded resume file is unavailable.')
            return redirect('companies:application_detail', pk=application.pk)
        resume_file = resume.open('rb')
    except OSError:
        logger.exception(
            'Resume storage failed for application_id=%s',
            application.pk,
        )
        messages.error(request, 'The uploaded resume file is unavailable.')
        return redirect('companies:application_detail', pk=application.pk)

    return FileResponse(
        resume_file,
        as_attachment=True,
        filename='resume.pdf',
        content_type='application/pdf',
    )
