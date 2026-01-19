"""
Views for dashboard.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime
import calendar

from authentication.models import User, UserRole
from chat.models import ChatSession
from authentication.permissions import IsStaffOrSuperAdmin
from authentication.utils import api_response


class DashboardStatsView(APIView):
    """Dashboard statistics."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def get(self, request):
        today = timezone.now().date()
        
        # Total unique chat users
        total_chat_users = ChatSession.objects.values('user').distinct().count()
        
        # Today's unique chat users
        todays_chat_users = ChatSession.objects.filter(
            created_at__date=today
        ).values('user').distinct().count()
        
        # Admin info
        admin_info = {
            'full_name': request.user.full_name,
            'role': request.user.role,
            'profile_picture': request.build_absolute_uri(request.user.profile_picture.url) 
                if request.user.profile_picture else None
        }
        
        return api_response(
            True,
            'Dashboard statistics retrieved successfully',
            data={
                'total_chat_users': total_chat_users,
                'todays_chat_users': todays_chat_users,
                'admin_info': admin_info
            }
        )


class MonthlyGrowthView(APIView):
    """Monthly chat user growth statistics."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def get(self, request):
        year = request.query_params.get('year', timezone.now().year)
        
        try:
            year = int(year)
        except ValueError:
            return api_response(
                False,
                'Invalid year parameter',
                errors={'year': ['Year must be a valid integer.']}
            )
        
        current_year = timezone.now().year
        if year < 2020 or year > current_year:
            return api_response(
                False,
                'Invalid year parameter',
                errors={'year': [f'Year must be between 2020 and {current_year}']}
            )
        
        # Get monthly data
        monthly_data = ChatSession.objects.filter(
            created_at__year=year
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            new_users=Count('user', distinct=True)
        ).order_by('month')
        
        # Build monthly growth array
        monthly_growth = []
        cumulative = 0
        monthly_dict = {data['month'].month: data['new_users'] for data in monthly_data}
        
        for month in range(1, 13):
            new_users = monthly_dict.get(month, 0)
            cumulative += new_users
            monthly_growth.append({
                'month': month,
                'month_name': calendar.month_name[month],
                'new_chat_users': new_users,
                'cumulative_users': cumulative
            })
        
        # Calculate summary
        active_months = [m for m in monthly_growth if m['new_chat_users'] > 0]
        
        growth_summary = None
        if active_months:
            highest = max(active_months, key=lambda x: x['new_chat_users'])
            lowest = min(active_months, key=lambda x: x['new_chat_users'])
            avg_growth = sum(m['new_chat_users'] for m in active_months) / len(active_months)
            
            # Growth rate from first to last active month
            if len(active_months) > 1:
                first_month = active_months[0]['new_chat_users']
                last_month = active_months[-1]['new_chat_users']
                growth_rate = ((last_month - first_month) / first_month * 100) if first_month > 0 else 0
            else:
                growth_rate = 0
            
            growth_summary = {
                'highest_growth_month': {
                    'month': highest['month'],
                    'month_name': highest['month_name'],
                    'new_chat_users': highest['new_chat_users']
                },
                'lowest_growth_month': {
                    'month': lowest['month'],
                    'month_name': lowest['month_name'],
                    'new_chat_users': lowest['new_chat_users']
                },
                'average_monthly_growth': round(avg_growth, 2),
                'growth_rate_percentage': round(growth_rate, 2)
            }
        
        return api_response(
            True,
            'Monthly chat user growth retrieved successfully',
            data={
                'year': year,
                'total_users_this_year': cumulative,
                'monthly_growth': monthly_growth,
                'growth_summary': growth_summary
            }
        )


class YearlyGrowthView(APIView):
    """Yearly chat user growth statistics."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def get(self, request):
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        start_year = request.query_params.get('start_year', 2020)
        end_year = request.query_params.get('end_year', current_year)
        limit = request.query_params.get('limit', 10)
        
        try:
            start_year = int(start_year)
            end_year = int(end_year)
            limit = min(int(limit), 20)
        except ValueError:
            return api_response(
                False,
                'Invalid parameters',
                errors={'detail': ['Year and limit must be valid integers.']}
            )
        
        # Get yearly data
        yearly_data = ChatSession.objects.filter(
            created_at__year__gte=start_year,
            created_at__year__lte=end_year
        ).annotate(
            year=TruncYear('created_at')
        ).values('year').annotate(
            new_users=Count('user', distinct=True)
        ).order_by('year')
        
        yearly_dict = {data['year'].year: data['new_users'] for data in yearly_data}
        
        # Build yearly growth array
        yearly_growth = []
        cumulative = 0
        prev_users = 0
        
        for year in range(start_year, end_year + 1):
            new_users = yearly_dict.get(year, 0)
            cumulative += new_users
            
            # Calculate growth rate
            growth_rate = ((new_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
            
            # Calculate monthly average
            months = current_month if year == current_year else 12
            monthly_avg = new_users / months if months > 0 else 0
            
            year_data = {
                'year': year,
                'new_chat_users': new_users,
                'cumulative_users': cumulative,
                'growth_rate_percentage': round(growth_rate, 2),
                'monthly_average': round(monthly_avg, 2)
            }
            
            if year == current_year:
                year_data['is_current_year'] = True
                year_data['months_elapsed'] = current_month
            
            yearly_growth.append(year_data)
            prev_users = new_users
        
        # Calculate CAGR
        years_count = len(yearly_growth)
        if years_count > 1 and yearly_growth[0]['new_chat_users'] > 0:
            first_year_users = yearly_growth[0]['new_chat_users']
            last_year_users = yearly_growth[-1]['new_chat_users']
            cagr = ((last_year_users / first_year_users) ** (1 / (years_count - 1)) - 1) * 100
        else:
            cagr = 0
        
        # Find best year
        best_year = max(yearly_growth, key=lambda x: x['new_chat_users']) if yearly_growth else None
        
        return api_response(
            True,
            'Yearly chat user growth retrieved successfully',
            data={
                'date_range': {
                    'start_year': start_year,
                    'end_year': end_year,
                    'total_years': years_count
                },
                'yearly_growth': yearly_growth[:limit],
                'overall_summary': {
                    'total_chat_users': cumulative,
                    'years_in_operation': years_count,
                    'average_yearly_growth': round(cumulative / years_count, 2) if years_count > 0 else 0,
                    'best_year': {
                        'year': best_year['year'],
                        'new_chat_users': best_year['new_chat_users']
                    } if best_year else None,
                    'compound_annual_growth_rate': round(cagr, 2)
                }
            }
        )
