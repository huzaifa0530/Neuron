# serializers.py
from rest_framework import serializers
from .models import Game
from accounts.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'username', 'email']

class GameSerializer(serializers.ModelSerializer):
    patient = CustomUserSerializer(source='patient_id_fk', read_only=True)

    class Meta:
        model = Game
        fields = ['id', 'name', 'result', 'remarks', 'status', 'created_at', 'updated_at', 'patient_id_fk', 'patient']
