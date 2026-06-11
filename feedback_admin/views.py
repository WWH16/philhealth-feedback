from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# When backend is integrated, import your Feedback model here, e.g.:
# from feedback.models import FeedbackEntry


# @login_required
def dashboard(request):
    """
    Admin dashboard view.

    Replace the dummy context below with real queryset aggregations once
    the Feedback model is in place:

        from django.db.models import Count
        from feedback.models import FeedbackEntry

        qs = FeedbackEntry.objects.all()
        context = {
            'total': qs.count(),
            'very_satisfactory': qs.filter(rating='pos').count(),
            'satisfactory': qs.filter(rating='neu').count(),
            'unsatisfactory': qs.filter(rating='neg').count(),
        }
    """
    context = {
        'total': 248,
        'very_satisfactory': 149,
        'satisfactory': 64,
        'unsatisfactory': 35,
    }
    return render(request, 'feedback_admin/dashboard.html', context)


# @login_required
def responses(request):
    """
    Full responses list view.

    Replace the dummy context below with a real queryset once the
    Feedback model is in place:

        from feedback.models import FeedbackEntry

        entries = FeedbackEntry.objects.order_by('-created_at')
        context = {
            'total': entries.count(),
            'very_satisfactory': entries.filter(rating='pos').count(),
            'satisfactory':      entries.filter(rating='neu').count(),
            'unsatisfactory':    entries.filter(rating='neg').count(),
            'entries': entries,   # passed to template for server-side rendering
        }
    """
    context = {
        'total': 248,
        'very_satisfactory': 149,
        'satisfactory': 64,
        'unsatisfactory': 35,
    }
    return render(request, 'feedback_admin/responses.html', context)

def sentiment_analysis(request):
    """
    Sentiment analysis view.

    Replace the dummy context below with real sentiment analysis results once
    the Feedback model is in place and you have implemented your sentiment
    analysis logic:

        from feedback.models import FeedbackEntry

        entries = FeedbackEntry.objects.all()
        # Implement your sentiment analysis logic here, e.g.:
        # pos_count = entries.filter(sentiment='positive').count()
        # neu_count = entries.filter(sentiment='neutral').count()
        # neg_count = entries.filter(sentiment='negative').count()

        context = {
            'total': entries.count(),
            'positive': pos_count,
            'neutral': neu_count,
            'negative': neg_count,
            # Add any additional context needed for charts or tables
        }
    """
    context = {
        'total': 248,
        'positive': 149,
        'neutral': 64,
        'negative': 35,
    }
    return render(request, 'feedback_admin/sentiment_analysis.html', context)

def reports(request):
    """
    Reports view with multiple report types.

    Replace the dummy context below with real data once the Feedback model is in place:

        from feedback.models import FeedbackEntry
        from django.db.models import Count, Avg
        from datetime import timedelta
        from django.utils import timezone

        entries = FeedbackEntry.objects.all()
        today = timezone.now().date()

        # Daily report
        daily_entries = entries.filter(created_at__date=today)

        context = {
            'daily_total': daily_entries.count(),
            'weekly_total': entries.filter(created_at__gte=today - timedelta(days=7)).count(),
            'monthly_total': entries.filter(created_at__gte=today - timedelta(days=30)).count(),
            'quarterly_total': entries.filter(created_at__gte=today - timedelta(days=90)).count(),
            'annual_total': entries.filter(created_at__year=today.year).count(),
            # Add satisfaction rates, suggestions, etc.
        }
    """
    context = {
        'daily_total': 18,
        'daily_vsat': 11,
        'daily_sat': 5,
        'daily_neg': 2,
        'daily_satisfaction': 83,

        'weekly_total': 84,
        'weekly_vsat': 52,
        'weekly_sat': 22,
        'weekly_neg': 10,
        'weekly_satisfaction': 81,

        'monthly_total': 248,
        'monthly_vsat': 149,
        'monthly_sat': 64,
        'monthly_neg': 35,
        'monthly_satisfaction': 82,

        'quarterly_total': 756,
        'quarterly_vsat': 453,
        'quarterly_sat': 204,
        'quarterly_neg': 99,
        'quarterly_satisfaction': 79,

        'annual_total': 3021,
        'annual_vsat': 1813,
        'annual_sat': 809,
        'annual_neg': 399,
        'annual_satisfaction': 77,
    }
    return render(request, 'feedback_admin/reports.html', context)