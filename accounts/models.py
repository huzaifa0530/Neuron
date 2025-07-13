from django.db import models
from django.utils import timezone
class Role(models.Model):
    class Meta:
        db_table = "roles"  # Match MySQL table name

    id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.role_name

class CustomUser(models.Model):
    class Meta:
        db_table = "users"  

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50,null=True, blank=True)
    username = models.CharField(max_length=50, unique=True)
    role_id_fk = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, db_column="role_id_fk")  # Keep column name!
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=256, null=True, blank=True)
    mrno = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    api_token = models.CharField(max_length=256, null=True, blank=True)
    game1 = models.IntegerField(max_length=256, null=True, blank=True)
    game2 = models.IntegerField(max_length=256, null=True, blank=True)
    game3 = models.IntegerField(max_length=256, null=True, blank=True)
    user_image = models.ImageField(upload_to='profile_image/', max_length=500, null=True, blank=True)
    mobile = models.CharField(max_length=256, null=True, blank=True)
    age = models.CharField(max_length=256, null=True, blank=True)
    address = models.CharField(max_length=256, null=True, blank=True)
    game_time = models.CharField(max_length=256, null=True, blank=True)
    demo_time = models.CharField(max_length=256, null=True, blank=True)    
    game_time_interval = models.CharField(max_length=256, null=True, blank=True)
    demo_time_interval = models.CharField(max_length=256, null=True, blank=True)    
                            
    def __str__(self):
        return self.username
    
    



