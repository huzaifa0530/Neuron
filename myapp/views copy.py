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
        games = Game.objects.filter(patient_id_fk=user_id, name=game_id)
        results = []
        for game in games:
            if isinstance(game.result, list):
                results.extend(game.result)
        return JsonResponse({'results': results}, safe=False)
    except Game.DoesNotExist:
        return JsonResponse({'results': [], 'error': 'Game not found'}, status=404)

@api_view(['GET'])
@token_required
def get_user_games(request, user_id):
    """
    Returns a list of distinct games played by the user.
    """
    games = Game.objects.filter(patient_id_fk=user_id).order_by('id')

    unique_ids = set()
    result = []

    for game in games:
        game_id = str(game.name).strip()
  # assuming 'name' holds values like '1', '2', etc.
        if game_id not in unique_ids:
            unique_ids.add(game_id)
            result.append({
                'id': game_id  # keep as string to match JS mapping keys
            })

    return Response(result)
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

        return render(request, 'myapp/doctor_dashboard.html', {'total_patients': total_patients})

    else:
        return redirect('login') 



def second_dashboard(request):
    role_name = request.session.get('role_name', '').lower()

    if role_name == 'doctor':
        created_by = request.session.get('user_id')  
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role_id_fk = 3 AND created_by = %s", [created_by])
            total_patients = cursor.fetchone()[0]

        return render(request, 'myapp/second_dashboard.html', {'total_patients': total_patients})

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
            'name': user.name,
            'username': user.username,
            'email': user.email,
            'role': user.role_id_fk.role_name if user.role_id_fk else "N/A",
            'status': "Active" if user.status == 1 else "Inactive",
            'created_at': user.created_at.strftime('%Y-%m-%d'),
         'actions': f"""
    <button class='editBtn btn btn-sm btn-warning' data-id='{user.id}'><i class="fa fa-edit"></i></button>
    <button class='deleteBtn btn btn-sm btn-danger' data-id='{user.id}'><i class="fa fa-trash"></i></button>
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
@api_view(['POST'])
@token_required
def get_games_by_name_and_patient(request):
    game_name = request.data.get('name')
    patient_id = request.data.get('patient_id_fk')

    if not game_name or not patient_id:
        return Response({"error": "Both 'name' and 'patient_id_fk' are required."}, status=status.HTTP_400_BAD_REQUEST)

    games = Game.objects.filter(name=game_name, patient_id_fk=patient_id).order_by('-created_at')

    if not games.exists():
        return Response({"message": "No games found for the given name and patient."}, status=status.HTTP_404_NOT_FOUND)

    serializer = GameSerializer(games, many=True)
    return Response({
        "status": "success",
        "count": games.count(),
        "data": serializer.data
    }, status=status.HTTP_200_OK)


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