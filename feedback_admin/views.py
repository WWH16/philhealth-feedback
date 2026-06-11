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