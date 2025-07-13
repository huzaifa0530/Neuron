import traceback
from datetime import datetime
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from accounts.models import CustomUser ,Role
from django.http import JsonResponse
from rest_framework.decorators import api_view
from accounts.decorators import token_required
from accounts.models import CustomUser
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from .models import Game
from .serializers import GameSerializer
from django.utils.dateparse import parse_date

@api_view(['GET'])
def get_game_results(request, user_id, game_id):
    """
    Return results for a specific user and game.
    """
    game_results = Game.objects.filter(patient_id_fk=user_id, name=game_id)
    results = [{
        'shape': r.shape,
        'color': r.color,
        'action': r.action,
        'display_time': r.display_time,
        'tap_time': r.tap_time
    } for r in game_results]

    return Response({'results': results})

@api_view(['GET'])
@token_required
def get_game_results_by_user(request, user_id, game_id):
    try:
        games = Game.objects.filter(patient_id_fk=user_id, id=game_id)
        print(f"Found games: {games}")  # 🛠 print what you found

        results = []
        for game in games:
            print(f"Game result: {game.result}")  # 🛠 print each game's result
            if isinstance(game.result, list):
                results.extend(game.result)

        return JsonResponse({'results': results}, safe=False)

    except Game.DoesNotExist:
        return JsonResponse({'results': [], 'error': 'Game not found'}, status=404)

@api_view(['GET'])
@token_required
def get_user_games(request, user_id):
    """
    Returns a list of all games played by the user (including duplicates), including creation date.
    """
    games = Game.objects.filter(patient_id_fk=user_id).order_by('id')

    result = []

    for game in games:
        result.append({
            'id': game.id,  # Keep the real id
            'name': str(game.name).strip(),  # Add name separately
            'date': game.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return Response(result)

@api_view(['GET'])
@token_required
def get_user_games_by_date(request, user_id):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Date parameter is required.'}, status=400)

    try:
        date_obj = parse_date(date_str)
        if not date_obj:
            raise ValueError("Invalid date format.")

        games = Game.objects.filter(
            patient_id_fk=user_id,
            created_at__date=date_obj
        ).values('id', 'name', 'created_at')

        # Format date nicely for frontend
        game_list = []
        for game in games:
            game_list.append({
        'id': game['id'],
        'name': game['name'],  # you need a type field!
        'date': game['created_at'].strftime('%Y-%m-%d') if game['created_at'] else ''
            })


        return JsonResponse(game_list, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def home(request):
    role_name = request.session.get('role_name', '').lower()  

    if role_name == 'admin':

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role_id_fk = 1")
            total_admins = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role_id_fk = 2")
            total_doctors = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role_id_fk = 3")
            total_patients = cursor.fetchone()[0]

        context = {
            'total_users': total_users,
            'total_admins': total_admins,
            'total_doctors': total_doctors,
            'total_patients': total_patients,
        }
        
        return render(request, 'myapp/home.html', context)

    elif role_name == 'doctor':

        created_by = request.session.get('user_id') 
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role_id_fk = 3 AND created_by = %s", [created_by])
            total_patients = cursor.fetchone()[0]
        patients = CustomUser.objects.filter(role_id_fk=3, created_by=created_by, status__gt=-1)

        if not patients.exists():
            print("No patients found for doctor id", created_by)

        patients_list = [{'id': p.id, 'name': p.name,'mrno':p.mrno} for p in patients]

    
        return render(request, 'myapp/doctor_dashboard.html', {
            'total_patients': total_patients,
            'patients': patients_list,
        })

    else:
        return redirect('login') 



    




def second_dashboard(request):
    role_name = request.session.get('role_name', '').lower()

    if role_name == 'doctor':
        created_by = request.session.get('user_id')  
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role_id_fk = 3 AND created_by = %s", [created_by])
            total_patients = cursor.fetchone()[0]
        patients = CustomUser.objects.filter(role_id_fk=3, created_by=created_by, status__gt=-1)

        if not patients.exists():
            print("No patients found for doctor id", created_by)

        patients_list = [{'id': p.id, 'name': p.name,'mrno':p.mrno} for p in patients]

        return render(request, 'myapp/second_dashboard.html', {'total_patients': total_patients,
            'patients': patients_list,
        })

    else:
        return redirect('login') 

def view_users(request):
    """ Fetch all users from the database and pass them to the template """

    role_name = request.session.get('role_name', '').lower()  
    user_id = request.session.get('user_id')  

    if role_name == "doctor":
        users = CustomUser.objects.filter(role_id_fk__id=3, created_by=user_id, status__gt=-1)
        return render(request, 'myapp/patient_list.html', {'users': users})
    else:
        users = CustomUser.objects.all()
        return render(request, 'myapp/users_list.html', {'users': users})



@api_view(['GET'])
@token_required
def get_users_data(request):
    """ Fetch users' data for DataTables with token protection """

    user = request.user
    role_name = user.role_id_fk.role_name.lower() if user.role_id_fk else ''
    user_id = user.id


    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()


    if role_name == "doctor":
        users = CustomUser.objects.filter(role_id_fk=3, created_by=user_id, status__gt=-1)
    else:
        users = CustomUser.objects.all()


    if search_value:
        users = users.filter(
            Q(name__icontains=search_value) |
            Q(username__icontains=search_value) |
            Q(email__icontains=search_value)
        )

    total_records = users.count()
    filtered_records = users.count()

    users = users[start:start+length]
    is_doctor = request.session.get('role_name', '').lower() == 'doctor'

    data = [
        {
            'id': user.id,
            'name': f"<span class='patientNameLink ' style='cursor:pointer;' data-id='{user.id}'>{user.name}</span>" if is_doctor else user.name,
            'username': user.username,
            'email': user.email,
            'mobile': user.mobile,
            'address': user.address,
            'age': user.age,
            'mrno': user.mrno,
            'user_image': user.user_image.url if user.user_image else '',            
            'role': user.role_id_fk.role_name if user.role_id_fk else "N/A",
            'status': "Active" if user.status == 1 else "Inactive",
            'created_at': user.created_at.strftime('%Y-%m-%d'),
         'actions': f"""
    <button class='editBtn btn btn-sm btn-warning' data-id='{user.id}'><i class="fa fa-edit"></i></button>
    <button class='deleteBtn btn btn-sm btn-danger' data-id='{user.id}'><i class="fa fa-trash"></i></button>
   
""",
         'games': f"""
    {f"<button class='viewGamesBtn btn btn-sm btn-info' data-userid='{user.id}'><i class='fa fa-gamepad'></i> See Games</button>" if is_doctor else ""}
"""
        }
        for user in users
    ]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })


#               <button class='viewResultsBtn btn btn-sm btn-info' data-userid='{user.id}'>
#     <i class="fa fa-gamepad"></i> See Games
# </button>


@api_view(['GET'])
@token_required
def get_user_details(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        roles = Role.objects.all()

        roles_options = [
            {"id": role.id, "role_name": role.role_name} for role in roles
        ]

        data = {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "role_id": user.role_id_fk.id if user.role_id_fk else None,
            "role_name": user.role_id_fk.role_name if user.role_id_fk else "Unknown",
            "status": "Active" if user.status else "Inactive",
            "rolesOptions": roles_options
        }

        return Response(data)

    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required
def edit_user(request):
    try:
        data = request.data

        user_id = data.get("id")
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        status_val = data.get("status")
        role_id = data.get("role")

        user = get_object_or_404(CustomUser, id=user_id)

        if CustomUser.objects.filter(email=email).exclude(id=user_id).exists():
            return Response({"error": "Email already exists!"}, status=status.HTTP_400_BAD_REQUEST)

        user.name = name
        user.email = email
        user.status = int(status_val)
        user.role_id_fk = get_object_or_404(Role, id=role_id)

        if password:
            user.set_password(password)

        user.save()

        return Response({"success": "User updated successfully!"})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@token_required
def delete_user(request):
    try:
        user_id = request.data.get("id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.get(id=user_id)
        user.delete()

        return Response({"success": "User deleted successfully."})

    except CustomUser.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
from rest_framework import serializers

# game table crud apis
# serializers.py
# @api_view(['POST'])
# @token_required
# def get_games_by_name_and_patient(request):
#     game_name = request.data.get('name')
#     patient_id = request.data.get('patient_id_fk')

#     if not game_name or not patient_id:
#         return Response({"error": "Both 'name' and 'patient_id_fk' are required."}, status=status.HTTP_400_BAD_REQUEST)

#     games = Game.objects.filter(name=game_name, patient_id_fk=patient_id).order_by('-created_at')

#     if not games.exists():
#         return Response({"message": "No games found for the given name and patient."}, status=status.HTTP_404_NOT_FOUND)

#     serializer = GameSerializer(games, many=True)
#     return Response({
#         "status": "success",
#         "count": games.count(),
#         "data": serializer.data
#     }, status=status.HTTP_200_OK)

@api_view(['POST'])
@token_required
def get_games_by_name_and_patient(request):
    try:
        game_name = request.data.get('name')
        patient_id = request.data.get('patient_id_fk')

        if not game_name or not patient_id:
            return Response({
                "success": False,
                "error": "Both 'name' and 'patient_id_fk' are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        latest_game = Game.objects.filter(
            name=game_name,
            patient_id_fk=patient_id
        ).order_by('-created_at').first()

        if not latest_game:
            return Response({
                "success": False,
                "message": "No game found for the given name and patient."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if latest_game was played today
        created_date = latest_game.created_at.date()
        current_date = now().date()

        if created_date == current_date:
            return Response({
                "success": False,
                "message": "You've already played today. Please wait until tomorrow to play again."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = GameSerializer(latest_game)
        return Response({
            "success": True,
                "message": "Ready To Play",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@token_required
def get_all_games(request):
    games = Game.objects.select_related('patient_id_fk').all().order_by('-created_at')
    serializer = GameSerializer(games, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@token_required
def get_game_by_id(request, game_id):
    try:
        game = Game.objects.select_related('patient_id_fk').get(id=game_id)
        serializer = GameSerializer(game)
        return Response(serializer.data)
    except Game.DoesNotExist:
        return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required
def create_game(request):
    data = request.data
    serializer = GameSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({"success": "Game created successfully", "game": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@token_required
def update_game(request, game_id):
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = GameSerializer(game, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"success": "Game updated successfully", "game": serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@token_required
def delete_game(request, game_id):
    try:
        game = Game.objects.get(id=game_id)
        game.delete()
        return Response({"success": "Game deleted successfully"})
    except Game.DoesNotExist:
        return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # toglle game acces api@api_view(['POST'])
@api_view(['POST'])
@token_required
def toggle_game_access(request):
    user_id = request.data.get('user_id')
    game_id = int(request.data.get('game_id'))

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)

    # Map game_id to field name
    game_field_map = {
        1: 'game1',
        2: 'game2',
        3: 'game3',
    }

    game_field = game_field_map.get(game_id)
    if not game_field:
        return JsonResponse({'error': 'Invalid game ID.'}, status=400)

    current_value = getattr(user, game_field, 0) or 0
    new_value = 0 if current_value == 1 else 1
    setattr(user, game_field, new_value)
    user.save()

    return JsonResponse({
        'success': True,
        'message': f"{game_field} updated to {new_value}",
        'new_value': new_value
    })




@api_view(['GET'])
@token_required
def get_games_name(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({
        'game1': user.game1 or 0,
        'game2': user.game2 or 0,
        'game3': user.game3 or 0
    })


def setting_form(request):
    user_id = request.session.get('user_id')
    
    # Get any one user (for example, the first one)
    user = CustomUser.objects.filter(created_by=user_id).first()

    context = {
        'user': user,  # not 'users'
    }

    return render(request, 'myapp/setting_form.html', context)




@api_view(['POST'])
@token_required
def setting_time(request):
    data = request.data
    print("Received Data:", data)

    user_id = request.session.get('user_id')

    users = CustomUser.objects.filter(created_by=user_id)

    if not users.exists():
        return Response(
            {"error": "No users found for this creator."},
            status=status.HTTP_404_NOT_FOUND
        )

    game_time = data.get('gametime')
    demo_time = data.get('demotime')
    game_time_interval = data.get('gametimeinterval')
    demo_time_interval = data.get('demotimeinterval')
    if not game_time or not demo_time:
        return Response(
            {"error": "Missing 'gametime' or 'demotime' in request data."},
            status=status.HTTP_400_BAD_REQUEST
        )

    users.update(
        game_time=game_time,
        demo_time=demo_time,
        game_time_interval=game_time_interval,
        demo_time_interval=demo_time_interval
    )

    return Response(
        {
            "success": "Users' game time updated successfully",
            "updated_count": users.count(),
        },
        status=status.HTTP_200_OK
    )
