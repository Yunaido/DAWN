from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and request.path not in ['/login/']:
            return redirect('login')
        response = self.get_response(request)
        return response