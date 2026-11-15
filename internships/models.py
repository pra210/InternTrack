from django.core.validators import MinValueValidator
from django.db import models


class Internship(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'
        FILLED = 'FILLED', 'Filled'

    company = models.ForeignKey(
        'companies.CompanyProfile',
        on_delete=models.PROTECT,
        related_name='internships',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.ManyToManyField(
        'students.Skill',
        related_name='internships',
        blank=True,
    )
    location = models.CharField(max_length=200)
    stipend = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    duration = models.CharField(max_length=100)
    deadline = models.DateField(db_index=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline', '-created_at']
        indexes = [
            models.Index(
                fields=['status', 'deadline'],
                name='intern_status_deadline_idx',
            ),
            models.Index(
                fields=['company', 'status'],
                name='intern_company_status_idx',
            ),
        ]

    def __str__(self):
        return self.title
