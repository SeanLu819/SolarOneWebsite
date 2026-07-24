import user_agents
from django.utils import timezone
from .models import Visitor, DailyStats

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Skip admin, static, media requests
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response
        
        # Only track GET requests
        if request.method != 'GET':
            return response
        
        try:
            ip = self.get_client_ip(request)
            ua_string = request.META.get('HTTP_USER_AGENT', '')
            
            # Parse user agent
            ua = user_agents.parse(ua_string)
            browser_family = ua.browser.family if ua.browser.family else 'Unknown'
            browser_version = ua.browser.version_string if ua.browser.version_string else ''
            os_family = ua.os.family if ua.os.family else 'Unknown'
            
            # Determine device type
            if ua.is_mobile:
                device = 'Mobile'
            elif ua.is_tablet:
                device = 'Tablet'
            else:
                device = 'Desktop'
            
            # Check if unique visit (first from this IP today)
            today = timezone.now().date()
            is_unique = not Visitor.objects.filter(
                ip_address=ip,
                visited_at__date=today
            ).exists()
            
            Visitor.objects.create(
                ip_address=ip,
                path=request.path,
                referrer=request.META.get('HTTP_REFERER', ''),
                user_agent=ua_string[:500],
                browser=browser_family,
                browser_version=browser_version,
                os=os_family,
                device=device,
                session_key=request.session.session_key or '',
                is_unique=is_unique,
            )
            
            # Update daily stats (use F() to avoid race conditions)
            from django.db.models import F
            daily_stats, _ = DailyStats.objects.get_or_create(date=today)
            DailyStats.objects.filter(pk=daily_stats.pk).update(
                total_visits=F('total_visits') + 1,
                unique_visits=F('unique_visits') + (1 if is_unique else 0),
            )
            
        except Exception:
            pass  # Never let tracking break the site
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
