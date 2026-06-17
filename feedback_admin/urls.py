from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────
    path('login/',  views.admin_login,  name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # ── Dashboard & pages ─────────────────────────────────────────────
    path('',                            views.dashboard,          name='dashboard'),
    path('responses/',                  views.responses,          name='responses'),
    path('responses/<int:entry_id>/status/', views.response_status_update, name='response_status_update'),
    path('responses/<int:entry_id>/category/', views.response_category_update, name='response_category_update'),
    path('responses/<int:entry_id>/notes/add/', views.response_note_add, name='response_note_add'),
    path('sentiment_analysis/',         views.sentiment_analysis, name='sentiment_analysis'),
    path('reports/',                    views.reports,            name='reports'),
    path('activity-log/',               views.activity_log,       name='activity_log'),

    # ── User management ───────────────────────────────────────────────
    path('users/',                       views.users,              name='users'),
    path('users/add/',                   views.user_add,           name='user_add'),
    path('users/<int:user_id>/edit/',    views.user_edit,          name='user_edit'),
    path('users/<int:user_id>/delete/',  views.user_delete,        name='user_delete'),
    path('users/<int:user_id>/toggle/',  views.user_toggle_active, name='user_toggle_active'),
    path('settings/password/', views.change_password, name='change_password'),

    # ── Group management ──────────────────────────────────────────────
    path('groups/add/',                   views.group_add,    name='group_add'),
    path('groups/<int:group_id>/edit/',   views.group_edit,   name='group_edit'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group_delete'),

    # ── Management ──────────────────────────────────────────────
    path('feedback/', views.feedback_detail, name='feedback_detail'),
    path('settings/', views.settings_page, name='settings_page'),
]