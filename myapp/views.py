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
from .models import Feedback, Game
from .serializers import GameSerializer,FeedbackSerializer
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
        print(f"Found games: {games}")  

        results = []
        for game in games:
            print(f"Game result: {game.result}")
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
        
        active_patients = CustomUser.objects.filter(role_id_fk=3, created_by=created_by, status=1).count()

    
        inactive_patients = CustomUser.objects.filter(role_id_fk=3, created_by=created_by, status=0).count()

    
        return render(request, 'myapp/doctor_dashboard.html', {
            'total_patients': total_patients,
            'active_patients': active_patients,
            'inactive_patients': inactive_patients,
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

def patient_profile(request):
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

        return render(request, 'myapp/patient_profile.html', {'total_patients': total_patients,
            'patients': patients_list,
        })

    else:
        return redirect('login') 



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

@api_view(['GET'])
@token_required
def get_top3_patient(request):
    """ Fetch top 3 newest users """
    user = request.user
    role_name = user.role_id_fk.role_name.lower() if user.role_id_fk else ''
    user_id = user.id

    if role_name == "doctor":
        users = CustomUser.objects.filter(role_id_fk=3, created_by=user_id, status__gt=-1)
    else:
        users = CustomUser.objects.all()

    users = users.order_by('-created_at')[:3]

    data = [
        {
            'id': u.id,
            'name': u.name,
            'username': u.username,
            'email': u.email,
            'mobile': u.mobile,
            'address': u.address,
            'age': u.age,
            'mrno': u.mrno,
            'user_image': u.user_image.url if u.user_image else '',
            'role': u.role_id_fk.role_name if u.role_id_fk else "N/A",
            'status': "Active" if u.status == 1 else "Inactive",
            'created_at': u.created_at.strftime('%Y-%m-%d'),
        }
        for u in users
    ]

    return JsonResponse(data, safe=False)



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
            "mrno": user.mrno,
            "mobile": user.mobile,
            "address": user.address,
            "age": user.age,
            "created_at": user.created_at,
            "username": user.username,  
            "user_image": user.user_image.url if user.user_image else None, 
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
    patient_id = data.get("patient_id_fk")
    game_name = data.get("name")

    # validate & save game
    serializer = GameSerializer(data=data)
    if serializer.is_valid():
        serializer.save()

        # Update the related CustomUser
        try:
            user = CustomUser.objects.get(id=patient_id)

            if str(game_name) == "1":
                user.game1 = 0
            elif str(game_name) == "2":
                user.game2 = 0
            elif str(game_name) == "3":
                user.game3 = 0

            user.save()

        except CustomUser.DoesNotExist:
            return Response(
                {"error": "CustomUser not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"success": "Game created successfully", "game": serializer.data},
            status=status.HTTP_201_CREATED
        )

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



from django.http import JsonResponse
from django.utils.timezone import localtime

@api_view(['GET'])
@token_required
def get_games_name(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    # ✅ Fetch last played for each game
    last_game1 = Game.objects.filter(patient_id_fk=user, name="1").order_by('-created_at').first()
    last_game2 = Game.objects.filter(patient_id_fk=user, name="2").order_by('-created_at').first()
    last_game3 = Game.objects.filter(patient_id_fk=user, name="3").order_by('-created_at').first()

    response_data = {
        "game1": user.game1 or 0,
        "game1_last_played": localtime(last_game1.created_at).strftime("%Y-%m-%d %H:%M:%S") if last_game1 else None,

        "game2": user.game2 or 0,
        "game2_last_played": localtime(last_game2.created_at).strftime("%Y-%m-%d %H:%M:%S") if last_game2 else None,

        "game3": user.game3 or 0,
        "game3_last_played": localtime(last_game3.created_at).strftime("%Y-%m-%d %H:%M:%S") if last_game3 else None,
    }

    return JsonResponse(response_data)


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


from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# 👇 This view will render your HTML page in browser
def feedback_form(request):
    return render(request, "myapp/create_feedback.html")

def feedback_show(request):
    return render(request, "myapp/Feedback_Show.html")


@api_view(['POST'])
@token_required
def create_feedback(request):
    try:
        user_id = request.data.get("user_id")
        name = request.data.get("name")
        email = request.data.get("email")
        msg = request.data.get("msg")

        # check if user exists
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        feedback = Feedback.objects.create(
            user=user,
            name=name,
            email=email,
            msg=msg
        )
        serializer = FeedbackSerializer(feedback)
        return Response({"success": True, "message": "Feedback submitted successfully!", "data": serializer.data},
                        status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@token_required
def list_feedback(request):
    """Fetch feedbacks according to respective patient -> doctor relationship"""

    user = request.user
    role_name = user.role_id_fk.role_name.lower() if user.role_id_fk else ''
    user_id = user.id

    if role_name == "doctor":
        patients = CustomUser.objects.filter(
            role_id_fk__role_name__iexact="patient",
            created_by=user_id
        ).values_list("id", flat=True)

        feedbacks = Feedback.objects.filter(
        ).order_by('-created_at')

    else:
        feedbacks = Feedback.objects.all().order_by('-created_at')

    serializer = FeedbackSerializer(feedbacks, many=True)
    return Response(serializer.data)




def view_games(request):
    return render(request, 'myapp/game.html')

from .models import Game
import csv
import json
import re
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from .models import Game
import csv
import json
import re
def clean_result(raw_result):
    """
    Convert anything (string/dict/list) into a valid JSON string.
    Fixes cases like:
    - [{shape:'Circle'}]
    - [{ shape: "Circle" }]
    - With None, single quotes, or missing quotes.
    """
    import json, re

    # If already a Python list/dict
    if isinstance(raw_result, (list, dict)):
        return json.dumps(raw_result)

    # If empty or None
    if not raw_result:
        return json.dumps([{"error": "Empty result"}])

    # Force to string
    text = str(raw_result).strip()

    # Decode escaped unicode
    try:
        text = text.encode('utf-8', 'ignore').decode('unicode_escape')
    except Exception:
        pass

    # Replace Python literals with JSON ones
    text = text.replace("None", "null").replace("True", "true").replace("False", "false")

    # Replace single quotes with double quotes carefully
    text = re.sub(r"'", '"', text)

    # ✅ Fix missing quotes around keys: shape: → "shape":
    text = re.sub(r'([{,])\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', text)

    # ✅ Remove any trailing commas
    text = re.sub(r',\s*([\]}])', r'\1', text)

    # Try to validate JSON
    try:
        parsed = json.loads(text)
        return json.dumps(parsed)
    except Exception as e:
        print("⚠️ JSON Cleaning Error:", e, "→", text)
        # Fallback: return safely wrapped string
        return json.dumps([{"error": "Invalid JSON", "raw": text}])
from datetime import datetime

import csv

def game_details(request, game_id):
    GAME_NAMES = {
        '1': 'RS Mode',
        '2': 'CPT Mode',
        '3': 'VST Mode',
    }

    # Base queryset
    games = Game.objects.filter(name=str(game_id)).select_related('patient_id_fk')

    # === ✅ 1. Filter by date range FIRST ===
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            games = games.filter(created_at__range=(start, end))
        except ValueError:
            pass

    # === ✅ 2. Then handle CSV Export ===
    if 'download' in request.GET:
        response = HttpResponse(content_type='text/csv')

        # make filename dynamic
        if start_date and end_date:
            filename = f'game_{game_id}_details_{start_date}_to_{end_date}.csv'
        else:
            filename = f'game_{game_id}_details_all.csv'

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['#', 'Patient Name', 'Email', 'Game', 'Result', 'Remarks', 'Status', 'Played On'])

        for idx, g in enumerate(games, start=1):
            game_label = GAME_NAMES.get(str(g.name), 'Unknown')
            writer.writerow([
                idx,
                getattr(g.patient_id_fk, 'name', 'N/A'),
                getattr(g.patient_id_fk, 'email', 'N/A'),
                game_label,
                clean_result(g.result)[:200],
                g.remarks or 'N/A',
                'Active' if g.status == 1 else 'Inactive',
                g.created_at.strftime("%Y-%m-%d %H:%M:%S") if g.created_at else 'N/A'
            ])
        return response

    # === ✅ 3. Otherwise, render HTML ===
    game_data = []
    for g in games:
        cleaned_json = clean_result(g.result)
        safe_json = mark_safe(cleaned_json)
        game_data.append({
            'username': getattr(g.patient_id_fk, 'name', 'N/A'),
            'email': getattr(g.patient_id_fk, 'email', 'N/A'),
            'game': g.name,
            'id': g.id,
            'patient_id': g.patient_id_fk.id,
            'result': safe_json,
            'remarks': g.remarks or 'N/A',
            'status': 'Active' if g.status == 1 else 'Inactive',
            'played_on': g.created_at.strftime("%Y-%m-%d %H:%M:%S") if g.created_at else 'N/A'
        })

    return render(request, 'myapp/game_details.html', {
        'games': game_data,
        'game_id': int(game_id),
        'start_date': start_date or '',
        'end_date': end_date or '',
    })
