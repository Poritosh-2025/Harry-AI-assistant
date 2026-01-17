"""
URL configuration for dashboard app.
"""
from django.urls import path
from .views import DashboardStatsView, MonthlyGrowthView, YearlyGrowthView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('chat-growth/monthly/', MonthlyGrowthView.as_view(), name='monthly-growth'),
    path('chat-growth/yearly/', YearlyGrowthView.as_view(), name='yearly-growth'),
]
