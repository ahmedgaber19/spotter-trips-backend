"""
API URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('calculate-route/', views.RouteCalculationView.as_view(), name='calculate-route'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]
