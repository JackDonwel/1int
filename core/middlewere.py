# middleware.py
from django.http import HttpResponseForbidden
from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect

class AdminIPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/wakili-secure-admin/'):
            ip = request.META.get('REMOTE_ADDR')
            if ip not in settings.ALLOWED_ADMIN_IPS:
                return HttpResponseForbidden("Admin access restricted to authorized IPs only.")
        return self.get_response(request)
    
    
class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            if request.path == reverse('login'):
                if request.user.is_staff:
                    return redirect('custom_dashboard')
                else:
                    return redirect('/')
        return response
    
