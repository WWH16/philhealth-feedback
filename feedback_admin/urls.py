from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('responses/', views.responses, name='responses'),
    path('sentiment_analysis/', views.sentiment_analysis, name='sentiment_analysis'),
]