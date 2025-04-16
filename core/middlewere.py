# middleware.py
from django.http import HttpResponseForbidden
from django.conf import settings

class AdminIPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/wakili-secure-admin/'):
            ip = request.META.get('REMOTE_ADDR')
            if ip not in settings.ALLOWED_ADMIN_IPS:
                return HttpResponseForbidden("Admin access restricted to authorized IPs only.")
        return self.get_response(request)