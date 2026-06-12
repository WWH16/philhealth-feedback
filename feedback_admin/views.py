from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.hashers import make_password
from django.db.models import Count
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required  # uncomment when ready

# When backend is integrated, import your Feedback model here, e.g.:
# from feedback.models import FeedbackEntry


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
    username = request.POST.get('username', '').strip()
    if not username:
        messages.error(request, 'Username is required.')
        return redirect('users')

    if User.objects.filter(username=username).exists():
        messages.error(request, f'Username "{username}" is already taken.')
        return redirect('users')

    pw1 = request.POST.get('password1', '')
    pw2 = request.POST.get('password2', '')
    if pw1 != pw2:
        messages.error(request, 'Passwords do not match.')
        return redirect('users')
    if len(pw1) < 8:
        messages.error(request, 'Password must be at least 8 characters.')
        return redirect('users')

    user = User.objects.create(
        username=username,
        email=request.POST.get('email', '').strip(),
        first_name=request.POST.get('first_name', '').strip(),
        last_name=request.POST.get('last_name', '').strip(),
        password=make_password(pw1),
        is_active='is_active' in request.POST,
        is_staff='is_staff' in request.POST,
        is_superuser='is_superuser' in request.POST,
    )

    group_ids = request.POST.getlist('groups')
    if group_ids:
        user.groups.set(Group.objects.filter(id__in=group_ids))

    perm_ids = request.POST.getlist('user_permissions')
    if perm_ids:
        user.user_permissions.set(Permission.objects.filter(id__in=perm_ids))

    messages.success(request, f'User "{username}" created successfully.')
    return redirect('users')


@login_required
@require_POST
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    username = request.POST.get('username', '').strip()
    if not username:
        messages.error(request, 'Username is required.')
        return redirect('users')

    if User.objects.filter(username=username).exclude(pk=user_id).exists():
        messages.error(request, f'Username "{username}" is already taken.')
        return redirect('users')

    user.username = username
    user.email = request.POST.get('email', '').strip()
    user.first_name = request.POST.get('first_name', '').strip()
    user.last_name = request.POST.get('last_name', '').strip()

    # Prevent self-deactivation: if editing self, force is_active to True
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
            messages.error(request, 'Passwords do not match.')
            return redirect('users')
        if len(pw1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('users')
        user.password = make_password(pw1)

    user.save()

    user.groups.set(Group.objects.filter(id__in=request.POST.getlist('groups')))
    user.user_permissions.set(Permission.objects.filter(id__in=request.POST.getlist('user_permissions')))

    messages.success(request, f'User "{user.username}" updated successfully.')
    return redirect('users')


@login_required
@require_POST
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('users')
    username = user.username
    user.delete()
    messages.success(request, f'User "{username}" deleted.')
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
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Group name is required.')
        return redirect('users')

    if Group.objects.filter(name=name).exists():
        messages.error(request, f'Group "{name}" already exists.')
        return redirect('users')

    group = Group.objects.create(name=name)
    perm_ids = request.POST.getlist('permissions')
    if perm_ids:
        group.permissions.set(Permission.objects.filter(id__in=perm_ids))

    messages.success(request, f'Group "{name}" created.')
    return redirect('users')


@login_required
@require_POST
def group_edit(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Group name is required.')
        return redirect('users')

    if Group.objects.filter(name=name).exclude(pk=group_id).exists():
        messages.error(request, f'Group "{name}" already exists.')
        return redirect('users')

    group.name = name
    group.save()
    group.permissions.set(Permission.objects.filter(id__in=request.POST.getlist('permissions')))

    messages.success(request, f'Group "{name}" updated.')
    return redirect('users')


@login_required
@require_POST
def group_delete(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    name = group.name
    group.delete()
    messages.success(request, f'Group "{name}" deleted.')
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