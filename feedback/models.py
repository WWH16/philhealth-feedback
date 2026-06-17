import secrets

from django.db import models
from django.utils import timezone


class FeedbackEntry(models.Model):
    VERY_SATISFACTORY = 'pos'
    SATISFACTORY = 'neu'
    UNSATISFACTORY = 'neg'

    RATING_CHOICES = [
        (VERY_SATISFACTORY, 'Very Satisfactory'),
        (SATISFACTORY, 'Satisfactory'),
        (UNSATISFACTORY, 'Unsatisfactory'),
    ]

    PENDING = 'pending'
    REVIEWED = 'reviewed'
    RESOLVED = 'resolved'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (REVIEWED, 'Reviewed'),
        (RESOLVED, 'Resolved'),
    ]

    COMPLAINT = 'complaint'
    SUGGESTION = 'suggestion'
    COMPLIMENT = 'compliment'
    CONCERN = 'concern'

    CATEGORY_CHOICES = [
        (COMPLAINT, 'Complaint'),
        (SUGGESTION, 'Suggestion'),
        (COMPLIMENT, 'Compliment'),
        (CONCERN, 'Concern'),
    ]

    tracking_code = models.CharField(max_length=24, unique=True, editable=False)
    rating = models.CharField(max_length=3, choices=RATING_CHOICES)
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, blank=True)
    comment = models.TextField(blank=True, max_length=500)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_code']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.tracking_code} - {self.get_rating_display()}'

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self._generate_tracking_code()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_tracking_code(cls):
        today = timezone.localdate().strftime('%Y%m%d')
        while True:
            code = f'CF-{today}-{secrets.token_hex(3).upper()}'
            if not cls.objects.filter(tracking_code=code).exists():
                return code

    @property
    def sentiment(self):
        return {
            self.VERY_SATISFACTORY: 'Positive',
            self.SATISFACTORY: 'Neutral',
            self.UNSATISFACTORY: 'Negative',
        }.get(self.rating, 'Neutral')