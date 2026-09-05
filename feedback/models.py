import secrets

from django.db import models
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone


class FeedbackEntry(models.Model):
    # Experience Ratings (Service Quality Dimensions - SQD)
    STRONGLY_AGREE = 'strongly_agree'
    AGREE = 'agree'
    NEITHER = 'neither'
    DISAGREE = 'disagree'
    STRONGLY_DISAGREE = 'strongly_disagree'
    NOT_APPLICABLE = 'na'

    EXPERIENCE_CHOICES = [
        (STRONGLY_AGREE, 'Strongly Agree'),
        (AGREE, 'Agree'),
        (NEITHER, 'Neither Agree nor Disagree'),
        (DISAGREE, 'Disagree'),
        (STRONGLY_DISAGREE, 'Strongly Disagree'),
        (NOT_APPLICABLE, 'Not Applicable'),
    ]

    # Sentiments (Detected or Manual)
    POSITIVE = 'pos'
    NEUTRAL = 'neu'
    NEGATIVE = 'neg'
    PENDING = 'pending'

    SENTIMENT_CHOICES = [
        (POSITIVE, 'Positive'),
        (NEUTRAL, 'Neutral'),
        (NEGATIVE, 'Negative'),
        (PENDING, 'Pending'),
    ]

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
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
    experience = models.CharField(max_length=25, choices=EXPERIENCE_CHOICES)
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, default=PENDING)
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, blank=True)
    comment = models.TextField(blank=True, max_length=1000)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)

    # CSM Form Specific Fields
    date_time = models.DateTimeField(null=True, blank=True)
    contact_no = models.CharField(max_length=50, blank=True)
    email_address = models.EmailField(max_length=100, blank=True)
    age = models.IntegerField(null=True, blank=True)
    client_type = models.CharField(max_length=100, blank=True)
    sex = models.CharField(max_length=50, blank=True)
    name_of_client = models.CharField(max_length=100, blank=True)
    services_availed = models.JSONField(default=list, blank=True)

    cc1 = models.CharField(max_length=10, blank=True)
    cc2 = models.CharField(max_length=10, blank=True)
    cc3 = models.CharField(max_length=10, blank=True)

    sqd0 = models.IntegerField(null=True, blank=True)
    sqd1 = models.IntegerField(null=True, blank=True)
    sqd2 = models.IntegerField(null=True, blank=True)
    sqd3 = models.IntegerField(null=True, blank=True)
    sqd4 = models.IntegerField(null=True, blank=True)
    sqd5 = models.IntegerField(null=True, blank=True)
    sqd6 = models.IntegerField(null=True, blank=True)
    sqd7 = models.IntegerField(null=True, blank=True)
    sqd8 = models.IntegerField(null=True, blank=True)

    comments_suggestions = models.TextField(blank=True, max_length=1000)
    commendation = models.TextField(blank=True, max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Feedback #{self.pk} - {self.get_experience_display()}'


class FeedbackConfiguration(models.Model):
    auto_analysis_enabled = models.BooleanField(default=True)
    daily_summary_enabled = models.BooleanField(default=False)
    notification_email = models.EmailField(blank=True, default='')
    daily_summary_time = models.CharField(max_length=5, default='16:30')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'feedback configuration'
        verbose_name_plural = 'feedback configuration'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        state = 'enabled' if self.auto_analysis_enabled else 'disabled'
        return f'Feedback configuration ({state})'

    @classmethod
    def get_solo(cls):
        try:
            config, _ = cls.objects.get_or_create(pk=1)
        except (OperationalError, ProgrammingError):
            return cls(
                pk=1,
                auto_analysis_enabled=True,
                daily_summary_enabled=False,
                notification_email='',
                daily_summary_time='16:30'
            )
        return config

    @classmethod
    def auto_analysis_is_enabled(cls):
        return cls.get_solo().auto_analysis_enabled

