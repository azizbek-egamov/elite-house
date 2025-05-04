from rest_framework import serializers
from main.models import *

class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = '__all__'
        
    def get_full_name(self, obj):
        return obj.client.full_name
    
    def get_phone(self, obj):
        return obj.client.phone