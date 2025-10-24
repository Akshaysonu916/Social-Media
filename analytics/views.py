from django.shortcuts import render
from django.db.models import Count, Max
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
    weekly_active_users = CustomUser.objects.filter(last_login__gte=today - timedelta(days=7), last_login__isnull=False).count()
    monthly_active_users = CustomUser.objects.filter(last_login__gte=today - timedelta(days=30), last_login__isnull=False).count()

    # Signups Per Day
    signups = CustomUser.objects.annotate(day=TruncDay('date_joined')) \
        .values('day').annotate(count=Count('id')).order_by('day')
    max_count = signups.aggregate(max_count=Max('count'))['max_count'] or 1
    total_signups = sum(item['count'] for item in signups)

    # Top Posts
    top_liked = Post.objects.annotate(like_count=Count('like_entries')).order_by('-like_count')[:5]  # use your related_name
    top_commented = Post.objects.annotate(comment_count=Count('comments')).order_by('-comment_count')[:5]  # use your related_name

    # Top Users by Post Count
    top_users = CustomUser.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:5]  # use your related_name

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
        'max_count': max_count,
        'total_signups': total_signups,
        'top_liked': top_liked,
        'top_commented': top_commented,
        'top_users': top_users,
        'hourly_activity': list(hourly_activity),
    }
    return render(request, 'admin_dashboard.html', context)