import json
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.hashers import make_password
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
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
from django.utils import timezone

from feedback.models import FeedbackEntry


# ── Activity log helpers (built on Django's built-in django_admin_log table) ──

def _feedback_content_type():
    return ContentType.objects.get_for_model(FeedbackEntry)


def log_feedback_note(user, entry, body):
    """Records an 'action taken / reply' note as an ADDITION log entry."""
    LogEntry.objects.log_actions(
        user_id=user.id,
        queryset=[entry],
        action_flag=ADDITION,
        change_message=body,
        single_object=True,
    )


def log_feedback_status_change(user, entry, old_status, new_status):
    """Records a status change as a CHANGE log entry."""
    LogEntry.objects.log_actions(
        user_id=user.id,
        queryset=[entry],
        action_flag=CHANGE,
        change_message=f'{old_status}|{new_status}',
        single_object=True,
    )


def get_feedback_activity(entry):
    """Builds (notes, status_history) for an entry from django_admin_log."""
    logs = (LogEntry.objects
            .filter(content_type=_feedback_content_type(), object_id=str(entry.pk))
            .select_related('user')
            .order_by('action_time'))

    status_display = dict(FeedbackEntry.STATUS_CHOICES)
    notes, history = [], []

    for log in logs:
        author = (log.user.get_full_name() or log.user.username) if log.user else 'System'
        at = timezone.localtime(log.action_time).strftime('%b %d, %Y %I:%M %p')

        if log.action_flag == CHANGE and '|' in log.change_message:
            old_raw, _, new_raw = log.change_message.partition('|')
            history.append({
                'old': status_display.get(old_raw, old_raw),
                'new': status_display.get(new_raw, new_raw),
                'by': author,
                'at': at,
            })
        else:
            notes.append({'author': author, 'body': log.change_message, 'created_at': at})

    return notes, history


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@login_required
@require_POST
def response_note_add(request, entry_id):
    entry = get_object_or_404(FeedbackEntry, pk=entry_id)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid request.'}, status=400)

    body = (payload.get('body') or '').strip()
    if not body:
        return JsonResponse({'ok': False, 'error': 'Note body cannot be empty.'}, status=400)

    log_feedback_note(request.user, entry, body)

    return JsonResponse({
        'ok': True,
        'note': {
            'author': request.user.get_full_name() or request.user.username,
            'body': body,
            'created_at': timezone.localtime(timezone.now()).strftime('%b %d, %Y %I:%M %p'),
        }
    })


@login_required
def dashboard(request):
    qs = FeedbackEntry.objects.all()
    now = timezone.localtime(timezone.now())
    today = now.date()
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    recent_entries = qs.order_by('-created_at')[:5]
    context = {
        'total': qs.count(),
        'very_satisfactory': qs.filter(rating=FeedbackEntry.VERY_SATISFACTORY).count(),
        'satisfactory': qs.filter(rating=FeedbackEntry.SATISFACTORY).count(),
        'unsatisfactory': qs.filter(rating=FeedbackEntry.UNSATISFACTORY).count(),
        'recent_entries_data': [_entry_to_row(entry) for entry in recent_entries],
        'filter_data': {
            'today': _rating_counts(qs.filter(created_at__date=today)),
            'week': _rating_counts(qs.filter(created_at__gte=week_start)),
            'month': _rating_counts(qs.filter(created_at__gte=month_start)),
            'all': _rating_counts(qs),
        },
    }
    return render(request, 'feedback_admin/dashboard.html', context)


@login_required
def responses(request):
    entries = FeedbackEntry.objects.order_by('-created_at')
    context = {
        'total': entries.count(),
        'very_satisfactory': entries.filter(rating=FeedbackEntry.VERY_SATISFACTORY).count(),
        'satisfactory': entries.filter(rating=FeedbackEntry.SATISFACTORY).count(),
        'unsatisfactory': entries.filter(rating=FeedbackEntry.UNSATISFACTORY).count(),
        'entries_data': [_entry_to_row(entry) for entry in entries],
    }
    return render(request, 'feedback_admin/responses.html', context)


def _entry_to_row(entry):
    local_created = timezone.localtime(entry.created_at)
    notes, status_history = get_feedback_activity(entry)
    return {
        'id': entry.id,
        'tracking_code': entry.tracking_code,
        'date': local_created.strftime('%Y-%m-%d'),
        'time': local_created.strftime('%H:%M'),
        'rating': entry.get_rating_display(),
        'category': entry.get_category_display(),
        'sentiment': entry.sentiment,
        'status': entry.get_status_display(),
        'status_value': entry.status,
        'comment': entry.comment,
        'notes': notes,
        'status_history': status_history,
    }


def _rating_counts(qs):
    return {
        'total': qs.count(),
        'vsat': qs.filter(rating=FeedbackEntry.VERY_SATISFACTORY).count(),
        'sat': qs.filter(rating=FeedbackEntry.SATISFACTORY).count(),
        'neg': qs.filter(rating=FeedbackEntry.UNSATISFACTORY).count(),
    }


@login_required
@require_POST
def response_status_update(request, entry_id):
    entry = get_object_or_404(FeedbackEntry, pk=entry_id)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid request.'}, status=400)

    status = payload.get('status')
    valid_statuses = {choice[0] for choice in FeedbackEntry.STATUS_CHOICES}
    if status not in valid_statuses:
        return JsonResponse({'ok': False, 'error': 'Invalid status.'}, status=400)

    status_display = dict(FeedbackEntry.STATUS_CHOICES)
    old_status = entry.status
    history_entry = None

    if status != old_status:
        entry.status = status
        entry.save(update_fields=['status', 'updated_at'])
        log_feedback_status_change(request.user, entry, old_status, status)
        history_entry = {
            'old': status_display.get(old_status, old_status),
            'new': status_display.get(status, status),
            'by': request.user.get_full_name() or request.user.username,
            'at': timezone.localtime(timezone.now()).strftime('%b %d, %Y %I:%M %p'),
        }

    return JsonResponse({
        'ok': True,
        'status': entry.get_status_display(),
        'status_value': entry.status,
        'updated_at': timezone.localtime(entry.updated_at).strftime('%b %d, %Y %I:%M %p'),
        'history_entry': history_entry,
    })


@login_required
def sentiment_analysis(request):
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


@login_required
def activity_log(request):
    """
    Government-facing audit trail: every status change and action-taken
    note recorded against a feedback entry, sourced entirely from Django's
    built-in django_admin_log table.
    """
    logs = (LogEntry.objects
            .filter(content_type=_feedback_content_type())
            .select_related('user')
            .order_by('-action_time'))

    status_display = dict(FeedbackEntry.STATUS_CHOICES)
    entry_ids = {int(l.object_id) for l in logs if l.object_id and l.object_id.isdigit()}
    entries_by_id = {e.pk: e for e in FeedbackEntry.objects.filter(pk__in=entry_ids)}

    rows = []
    status_change_count = 0
    note_count = 0

    for log in logs:
        entry = entries_by_id.get(int(log.object_id)) if log.object_id and log.object_id.isdigit() else None
        local_time = timezone.localtime(log.action_time)
        author = (log.user.get_full_name() or log.user.username) if log.user else 'System'

        row = {
            'id': log.pk,
            'date': local_time.strftime('%Y-%m-%d'),
            'time': local_time.strftime('%H:%M'),
            'admin': author,
            'tracking_code': entry.tracking_code if entry else '—',
            'rating': entry.get_rating_display() if entry else '',
            'category': entry.get_category_display() if entry else '',
        }

        if log.action_flag == CHANGE and '|' in log.change_message:
            old_raw, _, new_raw = log.change_message.partition('|')
            row.update({
                'action_type': 'status',
                'old_status': status_display.get(old_raw, old_raw),
                'new_status': status_display.get(new_raw, new_raw),
                'note': '',
            })
            status_change_count += 1
        else:
            row.update({
                'action_type': 'note',
                'old_status': '',
                'new_status': '',
                'note': log.change_message,
            })
            note_count += 1

        rows.append(row)

    context = {
        'logs_data': rows,
        'total_actions': len(rows),
        'total_status_changes': status_change_count,
        'total_notes': note_count,
    }
    return render(request, 'feedback_admin/activity_log.html', context)


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

    has_usable_password = request.POST.get('has_usable_password', 'on') == 'on'
    if not pw1:
        if has_usable_password and not user.has_usable_password():
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
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)

    return render(request, 'feedback_admin/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


# ── LOGOUT ────────────────────────────────────────────────────────────
@require_POST
def admin_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('admin_login')


@login_required
def feedback_detail(request):
    context = {
        'entry': {
            'id': 123,
            'rating': 'pos',
            'comment': 'Great service!',
            'created_at': '2024-01-01 12:34:56',
        }
    }
    return render(request, 'feedback_admin/feedback.html', context)


@login_required
def settings_page(request):
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