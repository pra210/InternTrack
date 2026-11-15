from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Notification
from accounts.models import User
from internships.models import Internship
from students.models import StudentProfile

from .forms import ApplicationForm
from .models import Application


@login_required(login_url='accounts:login')
def apply_to_internship(request, internship_id):
    internship = get_object_or_404(
        Internship.objects.select_related('company').prefetch_related(
            'required_skills',
        ),
        pk=internship_id,
    )

    if request.user.role != User.Role.STUDENT:
        messages.error(request, 'Only student accounts can apply to internships.')
        return redirect('internships:detail', pk=internship.pk)

    profile, _ = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
        },
    )
    existing_application = Application.objects.filter(
        student=profile,
        internship=internship,
    ).first()
    if existing_application:
        messages.info(request, 'You have already applied to this internship.')
        return redirect('internships:detail', pk=internship.pk)

    if (
        internship.status != Internship.Status.OPEN
        or internship.deadline < timezone.localdate()
    ):
        messages.error(
            request,
            'This internship is no longer accepting applications.',
        )
        return redirect('internships:detail', pk=internship.pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    Application.objects.create(
                        student=profile,
                        internship=internship,
                        cover_letter=form.cleaned_data['cover_letter'],
                    )
                    Notification.objects.create(
                        user=request.user,
                        message=(
                            f'Your application for {internship.title} at '
                            f'{internship.company.company_name} has been submitted.'
                        ),
                    )
            except IntegrityError:
                if Application.objects.filter(
                    student=profile,
                    internship=internship,
                ).exists():
                    messages.info(
                        request,
                        'You have already applied to this internship.',
                    )
                    return redirect('internships:detail', pk=internship.pk)
                raise

            messages.success(
                request,
                'Your application has been submitted successfully.',
            )
            return redirect('dashboard:student_dashboard')
    else:
        form = ApplicationForm()

    return render(
        request,
        'applications/apply.html',
        {
            'form': form,
            'internship': internship,
            'profile': profile,
        },
    )
