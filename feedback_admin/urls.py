from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────
    path('login/',  views.admin_login,  name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # ── Dashboard & pages ─────────────────────────────────────────────
    path('',                            views.dashboard,          name='dashboard'),
    path('responses/',                  views.responses,          name='responses'),
    path('sentiment_analysis/',         views.sentiment_analysis, name='sentiment_analysis'),
    path('reports/',                    views.reports,            name='reports'),

    # ── User management ───────────────────────────────────────────────
    path('users/',                       views.users,              name='users'),
    path('users/add/',                   views.user_add,           name='user_add'),
    path('users/<int:user_id>/edit/',    views.user_edit,          name='user_edit'),
    path('users/<int:user_id>/delete/',  views.user_delete,        name='user_delete'),
    path('users/<int:user_id>/toggle/',  views.user_toggle_active, name='user_toggle_active'),

    # ── Group management ──────────────────────────────────────────────
    path('groups/add/',                   views.group_add,    name='group_add'),
    path('groups/<int:group_id>/edit/',   views.group_edit,   name='group_edit'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group_delete'),

    # ── Management ──────────────────────────────────────────────
    path('feedback/', views.feedback_detail, name='feedback_detail'),
    path('settings/', views.settings_page, name='settings_page'),
]