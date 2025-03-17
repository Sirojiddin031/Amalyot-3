from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__' 

# class NewsSerializer(serializers.ModelSerializer):
#     is_expired = serializers.SerializerMethodField()

#     class Meta:
#         model = News
#         fields = '__all__'

#     def get_is_expired(self, obj):
#         return obj.is_expired()

