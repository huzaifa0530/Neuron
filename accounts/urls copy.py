from django.urls import path
from . import views

urlpatterns = [
    path('api/login/', views.api_login_view, name='api-login'),
    path('login/', views.template_login_view, name='login'),
   path('register/', register_user, name='register_user'),
    path('logout/', views.logout_view, name='logout'),
    path('logout/', views.register_user, name='register'),
    # path('register_Patient/', register_Patient, name='register_Patient'),
]
