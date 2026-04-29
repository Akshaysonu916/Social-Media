from django.utils.timezone import now
from django.conf import settings
from .models import UserActivity

class TrackUserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Skip media and static files
            path = request.path
            if not path.startswith(settings.MEDIA_URL) and not path.startswith(settings.STATIC_URL):
                # Throttle updates: only update once per minute
                last_update = request.session.get('last_activity_update')
                current_time = now().timestamp()
                
                if not last_update or current_time - last_update > 60:
                    UserActivity.objects.update_or_create(
                        user=request.user,
                        defaults={'last_active': now()}
                    )
                    request.session['last_activity_update'] = current_time

        return self.get_response(request)