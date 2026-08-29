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

    # 1. Experience mapping (supports sqd0 or direct experience payload)
    raw_sqd0 = payload.get('sqd0')
    experience = payload.get('experience')

    if not experience and raw_sqd0 is not None:
        try:
            sqd0_val = int(raw_sqd0)
            if sqd0_val in (1, 2):
                experience = FeedbackEntry.UNSATISFACTORY
            elif sqd0_val in (3, 4, 6):
                experience = FeedbackEntry.SATISFACTORY
            elif sqd0_val == 5:
                experience = FeedbackEntry.VERY_SATISFACTORY
        except (ValueError, TypeError):
            pass

    if not experience:
        experience = FeedbackEntry.SATISFACTORY

    valid_experiences = {choice[0] for choice in FeedbackEntry.EXPERIENCE_CHOICES}
    if experience not in valid_experiences:
        return JsonResponse({'ok': False, 'error': 'Please select your experience.'}, status=400)

    # 2. Comment handling (supports comment, comments_suggestions, commendation)
    comment = (payload.get('comment') or '').strip()
    comments_suggestions = (payload.get('comments_suggestions') or '').strip()
    commendation = (payload.get('commendation') or '').strip()

    if not comment:
        parts = []
        if comments_suggestions:
            parts.append(f"Comments: {comments_suggestions}")
        if commendation:
            parts.append(f"Commendation: {commendation}")
        comment = " | ".join(parts)

    if len(comment) > 1000:
        return JsonResponse({'ok': False, 'error': 'Comments must be 1000 characters or fewer.'}, status=400)

    # 3. Sentiment Analysis
    sentiment = (
        analyze_comment_sentiment(comment)
        if (comment and FeedbackConfiguration.auto_analysis_is_enabled())
        else FeedbackEntry.PENDING
    )

    # 4. Helper for date_time parsing
    dt_val = payload.get('date_time')
    parsed_dt = None
    if dt_val:
        try:
            from django.utils.dateparse import parse_datetime
            parsed_dt = parse_datetime(dt_val)
        except Exception:
            parsed_dt = None

    # Helper for int parsing
    def safe_int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    entry = FeedbackEntry.objects.create(
        experience=experience,
        comment=comment,
        sentiment=sentiment,
        date_time=parsed_dt,
        contact_no=(payload.get('contact_no') or '')[:50],
        email_address=(payload.get('email_address') or '')[:100],
        age=safe_int(payload.get('age')),
        client_type=(payload.get('client_type') or '')[:100],
        sex=(payload.get('sex') or '')[:50],
        name_of_client=(payload.get('name_of_client') or '')[:100],
        services_availed=payload.get('services_availed') if isinstance(payload.get('services_availed'), list) else [],
        cc1=str(payload.get('cc1') or '')[:10],
        cc2=str(payload.get('cc2') or '')[:10],
        cc3=str(payload.get('cc3') or '')[:10],
        sqd0=safe_int(payload.get('sqd0')),
        sqd1=safe_int(payload.get('sqd1')),
        sqd2=safe_int(payload.get('sqd2')),
        sqd3=safe_int(payload.get('sqd3')),
        sqd4=safe_int(payload.get('sqd4')),
        sqd5=safe_int(payload.get('sqd5')),
        sqd6=safe_int(payload.get('sqd6')),
        sqd7=safe_int(payload.get('sqd7')),
        sqd8=safe_int(payload.get('sqd8')),
        comments_suggestions=comments_suggestions,
        commendation=commendation,
    )

    return JsonResponse({
        'ok': True,
        'tracking_code': entry.tracking_code,
        'experience': entry.get_experience_display(),
        'status': entry.get_status_display(),
        'created_at': entry.created_at.strftime('%b %d, %Y %I:%M %p'),
    }, status=201)
