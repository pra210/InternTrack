from django.db import models, transaction
from django.utils import timezone


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        REVIEWING = 'REVIEWING', 'Reviewing'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        INTERVIEWING = 'INTERVIEWING', 'Interviewing'
        REJECTED = 'REJECTED', 'Rejected'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    internship = models.ForeignKey(
        'internships.Internship',
        on_delete=models.PROTECT,
        related_name='applications',
    )
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    cover_letter = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_date']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'internship'],
                name='uniq_student_internship_application',
            ),
        ]
        indexes = [
            models.Index(
                fields=['status', 'applied_date'],
                name='application_status_date_idx',
            ),
        ]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new:
                ApplicationStatusHistory.objects.create(
                    application=self,
                    status=self.status,
                )

    def __str__(self):
        return f'{self.student} - {self.internship}'


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='status_history',
    )
    status = models.CharField(max_length=12, choices=Application.Status.choices)
    changed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='application_status_changes',
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['created_at', 'pk']

    def __str__(self):
        return f'{self.application}: {self.get_status_display()}'


class Interview(models.Model):
    class Mode(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        OFFLINE = 'OFFLINE', 'Offline'

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='interview',
    )
    scheduled_at = models.DateTimeField()
    mode = models.CharField(max_length=8, choices=Mode.choices)
    meeting_link = models.URLField(blank=True)
    location = models.CharField(max_length=300, blank=True)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'Interview for {self.application}'
