
from django.contrib.auth.hashers import make_password
from .models import *
from typing import Any, Dict, Optional, Type, TypeVar
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, update_last_login
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()
class ParentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parents
        fields = "__all__"
        

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"

class UserAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone','password', "full_name", 'is_active', 'is_staff', "is_teacher",'is_admin', 'is_student')
        extra_kwargs = {'password': {'write_only': True}}
        
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    # def create(self, validated_data):
    #     validated_data['password'] = make_password(validated_data['password'])
    #     return super().create(validated_data)
    
class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}} 

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)  
        return user


class TokenSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        phone = data.get("phone")
        password = data.get("password")
        user = User.objects.filter(phone=phone).first()
        
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        raise serializers.ValidationError("Noto‘g‘ri telefon raqam yoki parol")
        
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'title', 'descriptions']

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'status', 'date_joined']

class TeacherSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Teacher
        fields = '__all__'


class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    re_new_password = serializers.CharField(required=True, write_only=True)

    def update(self, instance, validated_data):
        instance.password = validated_data.get('password', instance.password)

        if not validated_data['new_password']:
            raise serializers.ValidationError({'new_password': 'not found'})

        if not validated_data['old_password']:
            raise serializers.ValidationError({'old_password': 'not found'})

        if not instance.check_password(validated_data['old_password']):
            raise serializers.ValidationError({'old_password': 'wrong password'})

        if validated_data['new_password'] != validated_data['re_new_password']:
            raise serializers.ValidationError({'passwords': 'passwords do not match'})

        if validated_data['new_password'] == validated_data['re_new_password'] and instance.check_password(
                validated_data['old_password']):
            instance.set_password(validated_data['new_password'])
            instance.save()
            return instance

    class Meta:
        model = User
        fields = ['old_password', 'new_password', 're_new_password']

class HomeWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeWork
        fields = ['id', 'groupHomeWork', 'price', 'student','link', 'is_active', 'descriptions']

class DepartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ['id', 'title', 'is_active', 'descriptions']

class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ["id", 'user', 'departments', 'course', 'descriptions']

class TopicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topics
        fields = ['id', 'title', 'course', 'descriptions']
        
class SMSSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

class VerifySMSSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    verification_code = serializers.CharField()

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rooms
        fields = ['id', 'title', 'descriptions']


class GroupSerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True)  # 
    class Meta:
        model = Group
        fields = "__all__"

class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = ['id', 'title', 'descriptions']

class TableTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableType
        fields = ['id', 'title', 'descriptions']

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'start_time', 'end_time', 'room','type', 'descriptions']

class GroupHomeWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupHomeWork
        fields = ['id', 'group', 'topic','is_active', 'descriptions']

class AttendanceLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceLevel
        fields = ['id', 'level', 'title', 'created_at']


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

class AttendanceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceStatus
        fields = '__all__'

class DepartamentAddWorker(serializers.Serializer):
    worker_id = serializers.IntegerField()

class UserAndTeacherSerializer(serializers.Serializer):
    user = UserSerializer()
    teacher = TeacherSerializer()

class UserAndStudentSerializer(serializers.Serializer):
    user = UserSerializer()
    student = StudentSerializer()



class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("style", {})
        kwargs["style"]["input_type"] = "password"
        kwargs["write_only"] = True
        super().__init__(*args, **kwargs)

class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("No active account found with the given credentials")
        
        if not user.check_password(password):
            raise serializers.ValidationError("No active account found with the given credentials")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive")

        # Agar autentifikatsiya muvaffaqiyatli bo‘lsa, standart validate funksiyasini chaqiramiz
        data = super().validate({
            "username": user.username,  # username maydoni orqali token olish jarayonini davom ettiramiz
            "password": password
        })
        data["phone"] = phone
        return data