from django.db import models
from accounts.models import CustomUser

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
