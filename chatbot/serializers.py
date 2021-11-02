from rest_framework import serializers
from .models import Welfare


class WelfareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Welfare  # 모델 설정
        fields = ("id", "title", "genre", "year")  # 필드 설정
