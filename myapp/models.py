from django.db import models
from accounts.models import CustomUser
from django.utils import timezone


# this is my game table 

# the name colmn represent which game user play
# remomber one thing the name colmn  1,2,3 that represent which game played by patient


# i wante dto show all detail of user who played the game which which date also th result in table format also download optiion
class Game(models.Model):
    name = models.CharField(max_length=255)
    patient_id_fk = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, db_column="patient_id_fk")  
    result = models.JSONField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'game'

    def __str__(self):
        return f"{self.name} ({self.status})"


class Feedback(models.Model):
    class Meta:
        db_table = "feedbacks"   

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="feedbacks")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    msg = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.msg[:30]}"