from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),
    path('users/', views.view_users, name='View_Users'),
    path('api/get_users/', views.get_users_data, name='get_users_data'),
    path('api/get_user_details/<int:user_id>/', views.get_user_details, name='get_user_details'),
    path('api/edit_user/', views.edit_user, name='edit_user'),
    path('api/delete_user/', views.delete_user, name='delete_user'),
    path('second_doctor_dashboard/', views.second_dashboard, name='second_dashboard'),
    path('api/get_top3_patient/', views.get_top3_patient, name='get_top3_patient'),
    path('patient_profile/', views.patient_profile, name='patient_profile'),
    path('Report/', views.view_games, name='view_games'),
    path('games/details/<int:game_id>/', views.game_details, name='game_details'),
    
    
    
    path('api/games/', views.get_all_games, name='get_all_games'),
    path('api/games/<int:game_id>/', views.get_game_by_id, name='get_game_by_id'),
    path('api/games/create/', views.create_game, name='create_game'),
    path('api/games/update/<int:game_id>/', views.update_game, name='update_game'),
    path('api/games/delete/<int:game_id>/',  views.delete_game, name='delete_game'),
    path('api/get-games-by-name-and-patient/', views.get_games_by_name_and_patient, name='get_games_by_name_and_patient'),
    path('api/get-game-results/<int:user_id>/<int:game_id>/', views.get_game_results_by_user, name='get_game_results_by_user'),
    path('api/user-games/<int:user_id>/', views.get_user_games , name='get_user_games'),
    path('api/get_games_name/<int:user_id>/', views.get_games_name, name='get_games_name'),
    path('api/toggle_game_access/',  views.toggle_game_access, name='toggle_game_access'),
    path('api/user-games-by-date/<int:user_id>/', views.get_user_games_by_date, name='get_user_games_by_date'),
    path('api/setting/', views.setting_time, name='setting_time'),
    path('setting/', views.setting_form, name='setting_formuser-games-by-date'),
    
    path('api/feedback/create/', views.create_feedback, name='create_feedback'),
    path('api/feedback/', views.list_feedback, name='list_feedback'),
    path("feedback/form/", views.feedback_form, name="feedback_form"), 
    path("feedback/show/", views.feedback_show, name="feedback_show"), 
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)