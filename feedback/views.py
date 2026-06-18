import json

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import FeedbackConfiguration, FeedbackEntry
from .services import analyze_comment_sentiment


@ensure_csrf_cookie
def index(request):
    return render(request, 'feedback/index.html')


@require_POST
def submit_feedback(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid request.'}, status=400)

    experience = payload.get('experience')
    comment = (payload.get('comment') or '').strip()

    valid_experiences = {choice[0] for choice in FeedbackEntry.EXPERIENCE_CHOICES}
    if experience not in valid_experiences:
        return JsonResponse({'ok': False, 'error': 'Please select your experience.'}, status=400)

    if len(comment) > 500:
        return JsonResponse({'ok': False, 'error': 'Concern must be 500 characters or fewer.'}, status=400)

    sentiment = (
        analyze_comment_sentiment(comment)
        if FeedbackConfiguration.auto_analysis_is_enabled()
        else FeedbackEntry.PENDING
    )

    entry = FeedbackEntry.objects.create(
        experience=experience,
        comment=comment,
        sentiment=sentiment,
    )

    return JsonResponse({
        'ok': True,
        'tracking_code': entry.tracking_code,
        'experience': entry.get_experience_display(),
        'status': entry.get_status_display(),
        'created_at': entry.created_at.strftime('%b %d, %Y %I:%M %p'),
    }, status=201)
