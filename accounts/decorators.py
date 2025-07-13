from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from accounts.models import CustomUser

def token_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return Response(
                {'message': 'Session expired. Please login again.', 'redirect': True},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = CustomUser.objects.get(api_token=token)
            request.user = user
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'Session expired. Please login again.', 'redirect': True},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return view_func(request, *args, **kwargs)

    return wrapped_view
