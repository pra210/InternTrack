from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from applications.models import Application
from students.models import StudentProfile

from .models import Internship


def internship_detail(request, pk):
    internship = get_object_or_404(
        Internship.objects.select_related('company').prefetch_related(
            'required_skills',
        ),
        pk=pk,
    )
    application = None
    if (
        request.user.is_authenticated
        and request.user.role == request.user.Role.STUDENT
    ):
        application = Application.objects.filter(
            student__user=request.user,
            internship=internship,
        ).first()

    return render(
        request,
        'internships/detail.html',
        {
            'internship': internship,
            'application': application,
            'accepting_applications': (
                internship.status == Internship.Status.OPEN
                and internship.deadline >= timezone.localdate()
            ),
        },
    )
