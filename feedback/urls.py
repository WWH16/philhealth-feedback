from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='feedback-index'),
    path('submit/', views.submit_feedback, name='feedback-submit'),
    path('track/<str:tracking_code>/', views.track_feedback, name='feedback-track'),
]