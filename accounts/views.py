from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from accounts.models import CustomUser, Role
import bcrypt
import uuid
from accounts.decorators import token_required

from .serializers import CustomUserSerializer
import bcrypt
import uuid
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import CustomUser
from .serializers import CustomUserSerializer
from rest_framework import status

@api_view(['POST'])
def api_login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    role_type = request.data.get('role_type')

    try:
    
        if role_type == "adminOrdoctor":
            user = CustomUser.objects.get(username=username, role_id_fk__in=[1, 2])  # Assuming 1 and 2 are admin or doctor roles
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                # Generate and store the token
                token = str(uuid.uuid4())
                user.api_token = token
                user.save()

                request.session['user_id'] = user.id
                request.session['role_name'] = user.role_id_fk.role_name if user.role_id_fk else ''
                request.session['username'] = user.username
                request.session['email'] = user.email
                # Serialize user data
                serializer = CustomUserSerializer(user)

                # Debug print in terminal
                print("User authenticated successfully:")
                print(serializer.data)

                return Response({
                    "status": "success",
                    "message": "User authenticated successfully",
                    "token": token,
                    "role": user.role_id_fk.role_name if user.role_id_fk else None,
                    "data": serializer.data
                })
            else:
                return Response({"status": "error", "message": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)

  
        elif role_type == "patient":
            user = CustomUser.objects.get(username=username, role_id_fk=3)  # Assuming 3 is the patient role
            mrno = request.data.get('mrno')  
            if user.mrno == mrno:
             
                token = str(uuid.uuid4())
                user.api_token = token
                user.save()

                request.session['user_id'] = user.id
                request.session['role_name'] = user.role_id_fk.role_name if user.role_id_fk else ''
                request.session['username'] = user.username
                request.session['email'] = user.email
   
                serializer = CustomUserSerializer(user)

                print("User authenticated successfully:")
                print(serializer.data)

                return Response({
                    "status": "success",
                    "message": "User authenticated successfully",
                    "token": token,
                    "role": user.role_id_fk.role_name if user.role_id_fk else None,
                    "data": serializer.data
                })
            else:
                return Response({"status": "error", "message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"status": "error", "message": "Invalid role type"}, status=status.HTTP_400_BAD_REQUEST)

    except CustomUser.DoesNotExist:
        return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

def template_login_view(request):
  

        return render(request, 'accounts/login.html')




def template_register_view(request):
    role_name = request.session.get('role_name', '')  
    if role_name.lower() != "admin" :
        messages.error(request, "You must be logged in to register a user.")
        return redirect('login')
    roles = Role.objects.all()
    return render(request, 'accounts/register.html', {'roles': roles})

def Signup(request):

    return render(request, 'accounts/doctor_register.html')



@api_view(['POST'])
@token_required
def register_user(request):


  
    user = request.user  

    if user.role_id_fk.role_name.lower() == 'patient':
        return Response({"status": "error", "message": "You do not have permission."}, status=status.HTTP_403_FORBIDDEN)

    name = request.data.get('name')
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    role_id = request.data.get('role')

    print(f"📦 Received: name={name}, username={username}, email={email}, password={'*' * len(password) if password else None}, role_id={role_id}")

    # Validation checks
    errors = []
    if CustomUser.objects.filter(email=email).exists():
        errors.append("Email already exists.")
    if CustomUser.objects.filter(username=username).exists():
        errors.append("Username already exists.")

    if errors:
        return Response({"status": "error", "message": " ".join(errors)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        role_instance = Role.objects.get(id=role_id) if role_id else None

        new_user = CustomUser(
            name=name,
            username=username,
            email=email,
            password=hashed_password,
            role_id_fk=role_instance,
            status=1,
            created_by=request.session.get('user_id')
        )
        new_user.save()
        
        print("✅ User created successfully.")
        return Response({"status": "success", "message": "User registered successfully"}, status=status.HTTP_201_CREATED)

    except Role.DoesNotExist:
        print("❌ Role ID not found in Role table.")
        return Response({"status": "error", "message": "Invalid role selected"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"🔥 Unexpected Error: {str(e)}")
        return Response({"status": "error", "message": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return redirect('template_register_view')

# 🔐 Logout View
def logout_view(request):
    request.session.flush()
    return redirect('login')





def template_register_patient_view(request):
    role_name = request.session.get('role_name', '')  

    if not role_name or role_name.strip().lower() != "doctor":
        messages.error(request, "You must be logged in to register a user.")
        return redirect('login')

    return render(request, 'accounts/register_Patient.html')

@api_view(['POST'])
@token_required
def api_register_patient(request):
    try:
        user = request.user

        if not user or not hasattr(user, 'role_id_fk'):
            return Response({
                "status": "error",
                "message": "Invalid or unauthorized user."
            }, status=status.HTTP_401_UNAUTHORIZED)

        if user.role_id_fk.role_name.lower() != 'doctor':
            return Response({
                "status": "error",
                "message": "You do not have permission to register a patient."
            }, status=status.HTTP_403_FORBIDDEN)

        name = request.data.get('name')
        username = request.data.get('username')
        email = request.data.get('email')
        mrno = request.data.get('mrno')
        mobile = request.data.get('mobile')  
        age = request.data.get('age')  
        address = request.data.get('address') 
        user_image = request.FILES.get('profile_image') 
        if not all([name, username, email, mrno, mobile, age, address]):
            return Response({
                "status": "error",
                "message": "All fields (name, username, email, mrno, mobile, age, address) are required."
            }, status=status.HTTP_400_BAD_REQUEST)


        role_id = 3  # Role ID for patient
        user_status = 1  # Active status

        # Check for existing records
        errors = []
        if CustomUser.objects.filter(email=email).exists():
            errors.append("Email already exists.")
        if CustomUser.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        if CustomUser.objects.filter(mrno=mrno).exists():
            errors.append("MRNO already exists.")

        if errors:
            return Response({
                "status": "error",
                "message": " ".join(errors)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch role instance
        try:
            role_instance = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Invalid role selected."
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"Creating user with details: {username}, {email}, MRNO: {mrno}, Created by: {user.username}")

        # Create new user
        new_user = CustomUser(
            name=name,
            username=username,
            email=email,
            role_id_fk=role_instance,
            mrno=mrno,
            mobile=mobile,  
            age=age,  
            address=address, 
            game1=1,
            game2=1,
            game3=1,
            game_time=15,
            demo_time=30,
            status=user_status,
            created_by=user.id,
        )
        if user_image:
            new_user.user_image = user_image 

        new_user.save()

        return Response({
            "status": "success",
            "message": "User registered successfully."
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        tb = traceback.format_exc()
        print(f" Exception occurred: {str(e)}\nTraceback:\n{tb}")
        return Response({
            "status": "error",
            "message": f"Unexpected error occurred: {str(e)}",
            "trace": tb
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

