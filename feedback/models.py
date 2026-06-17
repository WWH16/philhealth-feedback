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

    rating = models.CharField(max_length=3, choices=RATING_CHOICES)
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, blank=True)
    comment = models.TextField(blank=True, max_length=500)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'# {self.id} - {self.get_rating_display()}'

    @property
    def sentiment(self):
        return {
            self.VERY_SATISFACTORY: 'Positive',
            self.SATISFACTORY: 'Neutral',
            self.UNSATISFACTORY: 'Negative',
        }.get(self.rating, 'Neutral')