from django.utils.deprecation import MiddlewareMixin
from accounts.models import CustomUser

class CustomAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_id = request.session.get('user_id')  # Get user ID from session
        if user_id:
            try:
                request.user = CustomUser.objects.get(id=user_id)  # Attach user to request
            except CustomUser.DoesNotExist:
                request.user = None
        else:
            request.user = None

        if not hasattr(request.user, 'is_authenticated'):
            request.user.is_authenticated = True  # Ensure `is_authenticated` exists
