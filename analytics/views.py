from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncHour
from django.utils.timezone import now, timedelta

from myapp.models import CustomUser, Post, Like, Comment  # Adjust based on your app structure
from analytics.models import UserActivity  # If UserActivity is in analytics app

def analytics_dashboard(request):
    today = now().date()

    # Total Users
    total_users = CustomUser.objects.count()

    # Verified & Suspended Users
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    suspended_users = CustomUser.objects.filter(is_suspended=True).count()

    # Weekly/Monthly Active Users
    weekly_active_users = CustomUser.objects.filter(last_login__gte=today - timedelta(days=7)).count()
    monthly_active_users = CustomUser.objects.filter(last_login__gte=today - timedelta(days=30)).count()

    # Signups Per Day
    signups = CustomUser.objects.annotate(day=TruncDay('date_joined')) \
        .values('day').annotate(count=Count('id')).order_by('day')

    # Top Posts
    top_liked = Post.objects.annotate(like_count=Count('like')).order_by('-like_count')[:5]
    top_commented = Post.objects.annotate(comment_count=Count('comment')).order_by('-comment_count')[:5]

    # Top Users by Post Count
    top_users = CustomUser.objects.annotate(post_count=Count('post')).order_by('-post_count')[:5]

    # Heatmap Data (Hourly)
    hourly_activity = UserActivity.objects.annotate(hour=TruncHour('last_active')) \
        .values('hour').annotate(count=Count('id')).order_by('hour')

    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'suspended_users': suspended_users,
        'weekly_active_users': weekly_active_users,
        'monthly_active_users': monthly_active_users,
        'signups': list(signups),
        'top_liked': top_liked,
        'top_commented': top_commented,
        'top_users': top_users,
        'hourly_activity': list(hourly_activity),
    }
    return render(request, 'admin_dashboard.html', context)
