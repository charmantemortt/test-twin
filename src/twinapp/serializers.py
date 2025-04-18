from rest_framework import serializers
from .models import CallRequest


class CallRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallRequest
        fields = ['name', 'phone', 'color']
