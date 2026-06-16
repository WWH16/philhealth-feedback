import json

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import FeedbackEntry


@ensure_csrf_cookie
def index(request):
    return render(request, 'feedback/index.html')


@require_POST
def submit_feedback(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid request.'}, status=400)

    rating = payload.get('rating')
    comment = (payload.get('comment') or '').strip()

    valid_ratings = {choice[0] for choice in FeedbackEntry.RATING_CHOICES}
    if rating not in valid_ratings:
        return JsonResponse({'ok': False, 'error': 'Please select your experience.'}, status=400)
    if len(comment) > 500:
        return JsonResponse({'ok': False, 'error': 'Concern must be 500 characters or fewer.'}, status=400)

    entry = FeedbackEntry.objects.create(rating=rating, comment=comment)

    return JsonResponse({
        'ok': True,
        'tracking_code': entry.tracking_code,
        'rating': entry.get_rating_display(),
        'status': entry.get_status_display(),
        'created_at': entry.created_at.strftime('%b %d, %Y %I:%M %p'),
        'track_url': reverse('feedback-track', args=[entry.tracking_code]),
    }, status=201)


@require_GET
def track_feedback(request, tracking_code):
    entry = FeedbackEntry.objects.filter(tracking_code=tracking_code.strip().upper()).first()
    if not entry:
        return JsonResponse({'ok': False, 'error': 'Tracking code not found.'}, status=404)
    return JsonResponse({
        'ok': True,
        'tracking_code': entry.tracking_code,
        'rating': entry.get_rating_display(),
        'status': entry.get_status_display(),
        'created_at': entry.created_at.strftime('%b %d, %Y %I:%M %p'),
        'updated_at': entry.updated_at.strftime('%b %d, %Y %I:%M %p'),
    })