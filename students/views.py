import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import StudentProfileForm
from .models import StudentProfile

logger = logging.getLogger(__name__)


@login_required
def profile_view(request):
    if request.user.role != request.user.Role.STUDENT:
        messages.error(request, 'Only student profiles can be edited here.')
        return redirect('home')

    profile, _ = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.get_full_name() or request.user.username},
    )

    if request.method == 'POST':
        form = StudentProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )
        if form.is_valid():
            try:
                form.save()
            except OSError:
                logger.exception(
                    'Student profile file storage failed for user_id=%s',
                    request.user.pk,
                )
                messages.error(
                    request,
                    'We could not save your uploaded file. Please try again.',
                )
            else:
                messages.success(
                    request,
                    'Your profile was updated successfully.',
                )
                return redirect('students:profile')
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'students/profile.html', {'form': form, 'profile': profile})
