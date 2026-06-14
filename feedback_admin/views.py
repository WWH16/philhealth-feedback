from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.hashers import make_password
from django.db.models import Count
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm

# When backend is integrated, import your Feedback model here, e.g.:
# from feedback.models import FeedbackEntry


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@login_required
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


@login_required
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

@login_required
def sentiment_analysis(request):
    """
    Sentiment analysis view.

    Replace the dummy context below once the Feedback model is in place:

        from feedback.models import FeedbackEntry
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        entries = FeedbackEntry.objects.all()
        total = entries.count()
        positive = entries.filter(sentiment='positive').count()
        neutral  = entries.filter(sentiment='neutral').count()
        negative = entries.filter(sentiment='negative').count()

        trend_qs = (entries
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(
                positive=Count('id', filter=Q(sentiment='positive')),
                neutral=Count('id', filter=Q(sentiment='neutral')),
                negative=Count('id', filter=Q(sentiment='negative')),
            )
            .order_by('day'))

        trend_labels = [d['day'].strftime('%b %d') for d in trend_qs]
        trend_positive = [d['positive'] for d in trend_qs]
        trend_neutral  = [d['neutral'] for d in trend_qs]
        trend_negative = [d['negative'] for d in trend_qs]
    """
    total = 248
    positive = 149
    neutral = 64
    negative = 35

    def pct(n):
        return round((n / total) * 100) if total else 0

    context = {
        'total': total,
        'positive': positive,
        'neutral': neutral,
        'negative': negative,
        'positive_pct': pct(positive),
        'neutral_pct': pct(neutral),
        'negative_pct': pct(negative),

        'trend_labels': ['Jun 1','Jun 2','Jun 3','Jun 4','Jun 5','Jun 6','Jun 7','Jun 8','Jun 9','Jun 10','Jun 11'],
        'trend_positive': [12, 18, 14, 22, 16, 20, 25, 18, 23, 19, 16],
        'trend_neutral':  [5, 7, 6, 8, 5, 7, 9, 6, 8, 7, 6],
        'trend_negative': [3, 2, 4, 1, 3, 2, 3, 2, 4, 2, 3],
    }
    return render(request, 'feedback_admin/sentiment_analysis.html', context)

@login_required
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


# ── user management ───────────────────────────────────────────────────

@login_required
def users(request):
    all_users = User.objects.all().order_by('-date_joined').prefetch_related('groups', 'user_permissions')
    all_groups = Group.objects.annotate(member_count=Count('user')).prefetch_related('permissions')
    all_perms = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')

    context = {
        'users': all_users,
        'groups': all_groups,
        'permissions': all_perms,
        'total_users': all_users.count(),
        'active_users': all_users.filter(is_active=True).count(),
        'staff_users': all_users.filter(is_staff=True).count(),
        'total_groups': all_groups.count(),
    }
    return render(request, 'feedback_admin/users.html', context)


@login_required
@require_POST
def user_add(request):
    def err(msg):
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'error': msg})
        messages.error(request, msg)
        return redirect('users')

    username = request.POST.get('username', '').strip()
    if not username:
        return err('Username is required.')
    if User.objects.filter(username=username).exists():
        return err(f'Username "{username}" is already taken.')

    pw1 = request.POST.get('password1', '')
    pw2 = request.POST.get('password2', '')
    if pw1 != pw2:
        return err('Passwords do not match.')

    # Build a temporary user object so similarity validator can compare
    tmp_user = User(
        username=username,
        email=request.POST.get('email', '').strip(),
        first_name=request.POST.get('first_name', '').strip(),
        last_name=request.POST.get('last_name', '').strip(),
    )
    try:
        validate_password(pw1, user=tmp_user)
    except ValidationError as e:
        return err(' '.join(e.messages))

    has_usable_password = request.POST.get('has_usable_password', 'on') == 'on'

    user = User.objects.create(
        username=username,
        email=tmp_user.email,
        first_name=tmp_user.first_name,
        last_name=tmp_user.last_name,
        is_active='is_active' in request.POST,
        is_staff='is_staff' in request.POST,
        is_superuser='is_superuser' in request.POST,
    )
    if has_usable_password:
        user.set_password(pw1)
    else:
        user.set_unusable_password()
    user.save()

    group_ids = request.POST.getlist('groups')
    if group_ids:
        user.groups.set(Group.objects.filter(id__in=group_ids))
    perm_ids = request.POST.getlist('user_permissions')
    if perm_ids:
        user.user_permissions.set(Permission.objects.filter(id__in=perm_ids))

    msg = f'User "{username}" created successfully.'
    messages.success(request, msg)

    if _is_ajax(request):
        return JsonResponse({'ok': True, 'message': msg})
    return redirect('users')


@login_required
@require_POST
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    def err(msg):
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'error': msg})
        messages.error(request, msg)
        return redirect('users')

    username = request.POST.get('username', '').strip()
    if not username:
        return err('Username is required.')
    if User.objects.filter(username=username).exclude(pk=user_id).exists():
        return err(f'Username "{username}" is already taken.')

    user.username = username
    user.email = request.POST.get('email', '').strip()
    user.first_name = request.POST.get('first_name', '').strip()
    user.last_name = request.POST.get('last_name', '').strip()

    if user == request.user:
        user.is_active = True
    else:
        user.is_active = 'is_active' in request.POST

    user.is_staff = 'is_staff' in request.POST
    user.is_superuser = 'is_superuser' in request.POST

    pw1 = request.POST.get('password1', '')
    pw2 = request.POST.get('password2', '')
    if pw1:
        if pw1 != pw2:
            return err('Passwords do not match.')
        try:
            validate_password(pw1, user=user)
        except ValidationError as e:
            return err(' '.join(e.messages))
        user.set_password(pw1)

    # Password-based auth toggle (only meaningful when not setting a new password)
    has_usable_password = request.POST.get('has_usable_password', 'on') == 'on'
    if not pw1:
        if has_usable_password and not user.has_usable_password():
            # Can't re-enable without a new password
            pass
        elif not has_usable_password:
            user.set_unusable_password()

    user.save()
    user.groups.set(Group.objects.filter(id__in=request.POST.getlist('groups')))
    user.user_permissions.set(Permission.objects.filter(id__in=request.POST.getlist('user_permissions')))

    msg = f'User "{user.username}" updated successfully.'
    messages.success(request, msg)

    if _is_ajax(request):
        return JsonResponse({'ok': True, 'message': msg})
    return redirect('users')


@login_required
@require_POST
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'error': 'You cannot delete your own account.'})
        messages.error(request, "You cannot delete your own account.")
        return redirect('users')
    username = user.username
    user.delete()
    
    msg = f'User "{username}" deleted.'
    messages.success(request, msg)

    if _is_ajax(request):
        return JsonResponse({'ok': True, 'message': msg})
    return redirect('users')


@login_required
@require_POST
def user_toggle_active(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('users')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    state = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User "{user.username}" {state}.')
    return redirect('users')


@login_required
@require_POST
def group_add(request):
    def err(msg):
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'error': msg})
        messages.error(request, msg)
        return redirect('users')

    name = request.POST.get('name', '').strip()
    if not name:
        return err('Group name is required.')
    if Group.objects.filter(name=name).exists():
        return err(f'Group "{name}" already exists.')

    group = Group.objects.create(name=name)
    perm_ids = request.POST.getlist('permissions')
    if perm_ids:
        group.permissions.set(Permission.objects.filter(id__in=perm_ids))

    msg = f'Group "{name}" created.'
    messages.success(request, msg)

    if _is_ajax(request):
        return JsonResponse({'ok': True, 'message': msg})
    return redirect('users')


@login_required
@require_POST
def group_edit(request, group_id):
    group = get_object_or_404(Group, pk=group_id)

    def err(msg):
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'error': msg})
        messages.error(request, msg)
        return redirect('users')

    name = request.POST.get('name', '').strip()
    if not name:
        return err('Group name is required.')
    if Group.objects.filter(name=name).exclude(pk=group_id).exists():
        return err(f'Group "{name}" already exists.')

    group.name = name
    group.save()
    group.permissions.set(Permission.objects.filter(id__in=request.POST.getlist('permissions')))

    msg = f'Group "{name}" updated.'
    messages.success(request, msg)

    if _is_ajax(request):
        return JsonResponse({'ok': True, 'message': msg})
    return redirect('users')


@login_required
@require_POST
def group_delete(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    name = group.name
    group.delete()

    msg = f'Group "{name}" deleted.'
    messages.success(request, msg)

    if _is_ajax(request):
        return JsonResponse({'ok': True, 'message': msg})
    return redirect('users')


# ── LOGIN ─────────────────────────────────────────────────────────────
def admin_login(request):
    """
    Custom login view for the feedback admin panel.
    GET  → render login form.
    POST → validate credentials, redirect to dashboard on success.
    """
    # Already logged in? Go straight to dashboard.
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        # Form errors render automatically via {{ form.errors }} in the template.

    return render(request, 'feedback_admin/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


# ── LOGOUT ────────────────────────────────────────────────────────────
@require_POST
def admin_logout(request):
    """
    POST-only logout to prevent CSRF-free logouts via GET.
    Redirects to the login page after clearing the session.
    """
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('admin_login')

@login_required
def feedback_detail(request):
    """
    Feedback detail view.

    Replace the dummy context below with a real queryset once the
    Feedback model is in place:

        from feedback.models import FeedbackEntry

        entry = get_object_or_404(FeedbackEntry, pk=entry_id)
        context = {
            'entry': entry,
            # Add any additional context needed for the detail view
        }
    """
    context = {
        'entry': {
            'id': 123,
            'rating': 'pos',
            'comment': 'Great service!',
            'created_at': '2024-01-01 12:34:56',
            # Add any additional fields needed for the template
        }
    }
    return render(request, 'feedback_admin/feedback.html', context)

@login_required
def settings_page(request):
    """
    Settings page view.

    Replace the dummy context below with real settings data once you have
    defined what settings are needed for your application:

        # Example: load settings from a model or config file
        from .models import AdminSetting

        settings = AdminSetting.objects.first()
        context = {
            'setting1': settings.setting1,
            'setting2': settings.setting2,
            # Add any additional settings needed for the template
        }
    """
    context = {
        'users': User.objects.all().order_by('-date_joined'),
    }
    return render(request, 'feedback_admin/settings.html', context)

@login_required
@require_POST
def change_password(request):
    current_password = request.POST.get('current_password', '')
    new_password1    = request.POST.get('new_password1', '')
    new_password2    = request.POST.get('new_password2', '')

    if not request.user.check_password(current_password):
        messages.error(request, 'current_password|Current password is incorrect.', extra_tags='pw_field')
        return redirect('settings_page')
    if new_password1 != new_password2:
        messages.error(request, 'new_password2|New passwords do not match.', extra_tags='pw_field')
        return redirect('settings_page')

    try:
        validate_password(new_password1, user=request.user)
    except ValidationError as e:
        messages.error(request, 'new_password1|' + ' '.join(e.messages), extra_tags='pw_field')
        return redirect('settings_page')

    request.user.set_password(new_password1)
    request.user.save()
    update_session_auth_hash(request, request.user)
    messages.success(request, 'Password updated successfully.', extra_tags='pw_field')
    return redirect('settings_page')