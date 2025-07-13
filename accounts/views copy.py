from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from accounts.models import CustomUser, Role
import bcrypt   
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = CustomUser.objects.get(username=username)

            # ✅ Check password
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                # ✅ Store session details properly
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                request.session['user_email'] = user.email
                request.session['role_id'] = user.role_id_fk.id if user.role_id_fk else None
                request.session['role_name'] = user.role_id_fk.role_name if user.role_id_fk else "No Role"
                request.session['is_authenticated'] = True 
                role_name = user.role_id_fk.role_name.lower() if user.role_id_fk else ""

                # ✅ Redirect based on role
                # if role_name == "admin":
                #     return redirect('home')
                # elif role_name == "doctor":
                #     return redirect('doctor-dashboard')
                # else:
                #     return redirect('patient-dashboard')
                return redirect('home')
            else:
                messages.error(request, "Invalid password")
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found")

    return render(request, 'accounts/login.html')

def logout_view(request):
    request.session.flush() 
    return redirect('login')

previous one like this but i work perfectly fine 

def register_user(request):
    role_name = request.session.get('role_name', '')  
    if not role_name:
        messages.error(request, "You must be logged in to register a user.")
        return redirect('login')


    if role_name.lower() in ["admin"]:
        if request.method == "POST":
            name = request.POST['name']
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password'].encode('utf-8')  
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')  
            role_id = request.POST.get('role') 
            status = 1  
            created_by = request.session.get('user_id')  

            errors = []
            if CustomUser.objects.filter(email=email).exists():
                errors.append("Email already exists.")
            if CustomUser.objects.filter(username=username).exists():
                errors.append("Username already exists.")

            if errors:
                return JsonResponse({"status": "error", "message": " ".join(errors)})

            try:
                role_instance = Role.objects.get(id=role_id) if role_id else None  

                new_user = CustomUser(
                    name=name,
                    username=username,
                    email=email,
                    password=hashed_password,
                    role_id_fk=role_instance,  
                    status=status,
                    created_by=created_by
                )
                new_user.save()
                return JsonResponse({"status": "success", "message": "User registered successfully"})
            except Role.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Invalid role selected"})
            except IntegrityError:
                return JsonResponse({"status": "error", "message": "Failed to register user"})
        
        return render(request, 'accounts/register.html')


    elif role_name.lower() == "doctor":
        if request.method == "POST":
            name = request.POST['name']
            username = request.POST['username']
            email = request.POST['email']  
            mrno = request.POST['mrno']  
            role_id = 3  
            status = 1  
            created_by = request.session.get('user_id')  

            errors = []
            if CustomUser.objects.filter(email=email).exists():
                errors.append("Email already exists.")
            if CustomUser.objects.filter(username=username).exists():
                errors.append("Username already exists.")

            if errors:
                return JsonResponse({"status": "error", "message": " ".join(errors)})

            try:
                role_instance = Role.objects.get(id=role_id)  

                new_user = CustomUser(
                    name=name,
                    username=username,
                    email=email,
                    role_id_fk=role_instance,
                    mrno=mrno,  
                    status=status,
                    created_by=created_by
                )
                new_user.save()
                return JsonResponse({"status": "success", "message": "Patient registered successfully"})
            except Role.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Invalid role selected"})
            except IntegrityError:
                return JsonResponse({"status": "error", "message": "Failed to register patient"})
        
        return render(request, 'accounts/register_Patient.html')

    messages.error(request, "You do not have permission to register a user.")
    return redirect('home')
