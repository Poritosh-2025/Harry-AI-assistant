"""
Serializers for dashboard.
"""
from rest_framework import serializers


class AdminInfoSerializer(serializers.Serializer):
    """Serializer for admin info in dashboard responses."""
    full_name = serializers.CharField()
    role = serializers.CharField()
    profile_picture = serializers.ImageField(allow_null=True)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    total_chat_users = serializers.IntegerField()
    todays_chat_users = serializers.IntegerField()
    admin_info = AdminInfoSerializer()


class MonthlyGrowthSerializer(serializers.Serializer):
    """Serializer for monthly growth data."""
    month = serializers.IntegerField()
    month_name = serializers.CharField()
    new_chat_users = serializers.IntegerField()
    cumulative_users = serializers.IntegerField()


class GrowthSummarySerializer(serializers.Serializer):
    """Serializer for growth summary."""
    highest_growth_month = MonthlyGrowthSerializer()
    lowest_growth_month = MonthlyGrowthSerializer()
    average_monthly_growth = serializers.FloatField()
    growth_rate_percentage = serializers.FloatField()


class YearlyGrowthSerializer(serializers.Serializer):
    """Serializer for yearly growth data."""
    year = serializers.IntegerField()
    new_chat_users = serializers.IntegerField()
    cumulative_users = serializers.IntegerField()
    growth_rate_percentage = serializers.FloatField()
    monthly_average = serializers.FloatField()
    is_current_year = serializers.BooleanField(required=False)
    months_elapsed = serializers.IntegerField(required=False)
