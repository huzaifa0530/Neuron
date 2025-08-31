# serializers.py
from rest_framework import serializers
from .models import Game
from accounts.models import CustomUser
from .models import Feedback

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'username', 'email']

class GameSerializer(serializers.ModelSerializer):
    patient = CustomUserSerializer(source='patient_id_fk', read_only=True)

    class Meta:
        model = Game
        fields = ['id', 'name', 'result', 'remarks', 'status', 'created_at', 'updated_at', 'patient_id_fk', 'patient']


from rest_framework import serializers

class FeedbackSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=False)

    class Meta:
        model = Feedback
        fields = ["id", "user_id", "name", "email", "msg", "created_at"]
