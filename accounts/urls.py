from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
urlpatterns = [
    path('api/login/', views.api_login_view, name='api-login'),
    path('login/', views.template_login_view, name='login'),
    path('api/register/', views.register_user, name='register_user'),  # changed URL here
    path('register/', views.template_register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/register-patient/', views.api_register_patient, name='api_register_patient'),  # changed URL here
    path('register-patient/', views.template_register_patient_view, name='register_patient'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)