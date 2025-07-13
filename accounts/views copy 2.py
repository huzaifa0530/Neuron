from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from accounts.models import CustomUser, Role
import bcrypt
import uuid
from accounts.decorators import token_required

@api_view(['POST'])
def api_login_view(request):
    
    
    username = request.data.get('username')
    password = request.data.get('password')

    try:
        if parameter equal to  adminOrdoctor search according to 
        user = CustomUser.objects.get(username=username ,where role_id_fk == 2 or 1 )
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8') ,where role_id_fk == 2 or 1 ):
            token = str(uuid.uuid4())  
            user.api_token = token
            user.save()
            request.session['user_id'] = user.id
            request.session['role_name'] = user.role_id_fk.role_name if user.role_id_fk else ''
            return Response({
                "status": "success",
                "message": "User authenticated successfully",
                "token": token
            })
            else if   parameter equal to  patient search according to 
              user = CustomUser.objects.get(username=username ,where role_id_fk ==3 )
        else:
            return Response({"status": "error", "message": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
    except CustomUser.DoesNotExist:
        return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)



def template_login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = CustomUser.objects.get(username=username)

            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                request.session['user_email'] = user.email
                request.session['role_id'] = user.role_id_fk.id if user.role_id_fk else None
                request.session['role_name'] = user.role_id_fk.role_name if user.role_id_fk else "No Role"
                request.session['is_authenticated'] = True 
                return redirect('home')
            else:
                messages.error(request, "Invalid password")
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found")

        return render(request, 'accounts/login.html')

    # ✅ Add this line for GET request
    return render(request, 'accounts/login.html')



def template_register_view(request):
    role_name = request.session.get('role_name', '')  
    if role_name.lower() != "admin":
        messages.error(request, "You must be logged in to register a user.")
        return redirect('login')
    roles = Role.objects.all()
    return render(request, 'accounts/register.html', {'roles': roles})



@api_view(['POST'])
@token_required
def register_user(request):


  
    user = request.user  

    if user.role_id_fk.role_name.lower() != 'admin':
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
        print(f"❗Validation Errors: {errors}")
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
    if role_name.lower() != "doctor":
        messages.error(request, "You must be logged in to register a user.")
        return redirect('login')


    return render(request, 'accounts/register_Patient.html')


    
@api_view(['POST'])
@token_required
def api_register_patient(request):
    user = request.user  
    if user.role_id_fk.role_name.lower() != 'doctor':
        return Response({"status": "error", "message": "You do not have permission."}, status=status.HTTP_403_FORBIDDEN)

    name = request.data.get('name')
    username = request.data.get('username')
    email = request.data.get('email')
    mrno = request.data.get('mrno') 
    role_id = 3  
    user_status= 1  
    created_by = request.session.get('user_id') 
    print(f"📦 Received: name={name}, username={username}, email={email},role_id={role_id}")

    # Validation checks
    errors = []
    if CustomUser.objects.filter(email=email).exists():
        errors.append("Email already exists.")
    if CustomUser.objects.filter(username=username).exists():
        errors.append("Username already exists.")

    if errors:
        print(f"❗Validation Errors: {errors}")
        return Response({"status": "error", "message": " ".join(errors)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        role_instance = Role.objects.get(id=role_id) if role_id else None

        new_user = CustomUser(
              name=name,
                    username=username,
                    email=email,
                    role_id_fk=role_instance,
                    mrno=mrno,  
                    status=user_status,
                    created_by=created_by
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
        return redirect('template_register_patient_view')


