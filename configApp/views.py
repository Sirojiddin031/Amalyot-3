import random
from configApp.pagination import StudentPagination
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.generics import ListAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.module_loading import import_string
from rest_framework.request import Request
from rest_framework.serializers import Serializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.hashers import make_password
from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets
from django.db.models import Count
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, action
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework.decorators import api_view, permission_classes
from django.utils.dateparse import parse_date


class Pagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    
#User
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    pagination_class = Pagination
    permission_classes = [IsAuthenticated]

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]    

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer

class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]

class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Barcha foydalanuvchilarni olish",
        responses={200: UserSerializer(many=True)},
    )
    def list(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Foydalanuvchi ID bo‘yicha olish",
        responses={200: UserSerializer()},
    )
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Yangi foydalanuvchi yaratish",
        request_body=UserSerializer,
        responses={201: "Foydalanuvchi yaratildi"},
    )
    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Foydalanuvchini yangilash",
        request_body=UserSerializer,
        responses={200: "Foydalanuvchi yangilandi"},
    )
    def update(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Foydalanuvchini o‘chirish",
        responses={204: "Foydalanuvchi o‘chirildi"},
    )
    def destroy(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

User = get_user_model()


class CreateUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        # Foydalanuvchi yaratish lojiqasi
        user = User.objects.create_user(
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password"),
            # Qo'shimcha maydonlar: is_superuser, is_staff, phone, full_name va hokazo
        )
        return Response({"detail": "User created successfully"}, status=201)

class PhoneSendOTP(APIView):
    @swagger_auto_schema(request_body=SMSSerializer)
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        print(phone_number)
        if phone_number:
            phone = str(phone_number)
            user = User.objects.filter(phone__iexact=phone)
            if user.exists():
                return Response({
                    'status': False,
                    'detail': 'phone number already exist'
                })
            else:
                key = send_otp(phone)

                if key:
                    cache.set(phone_number, key, 600)

                    return Response({"message": "SMS sent successfully"}, status=status.HTTP_200_OK)

                return Response({"message": "Failed to send SMS"}, status=status.HTTP_400_BAD_REQUEST)

def send_otp(phone):
    if phone:
        key = 1212
        print(key)
        return key
    else:
        return False

class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer

class StatisticsView(APIView):
    """
    Ushbu API date1 va date2 oralig‘idagi statistikani chiqaradi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date1 = request.GET.get('date1')
        date2 = request.GET.get('date2')

        if not date1 or not date2:
            return Response({"error": "date1 va date2 parametrlari kerak"}, status=400)

        date1 = parse_date(date1)
        date2 = parse_date(date2)

        if not date1 or not date2:
            return Response({"error": "Noto‘g‘ri sana formati"}, status=400)

        stats = {}
        for course in Course.objects.all():
            stats[course.name] = {
                "registered": Enrollment.objects.filter(course=course, status='registered', date_joined__range=[date1, date2]).count(),
                "studying": Enrollment.objects.filter(course=course, status='studying', date_joined__range=[date1, date2]).count(),
                "graduated": Enrollment.objects.filter(course=course, status='graduated', date_joined__range=[date1, date2]).count()
            }

        return Response(stats)

class EnrollmentUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
# -----------------------------
# CRUD API
# -----------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_student(request):
    serializer = StudentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_students(request):
    students = Student.objects.all()
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_student(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = StudentSerializer(student, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_student(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    student.delete()
    return Response({'message': 'Student deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

# -----------------------------
# Sana oralig‘i bo‘yicha filtrlangan API
# -----------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def studying_students(request):
    start = request.data.get('start')
    end = request.data.get('end')
    if not start or not end:
        return Response({'error': 'Please provide start and end dates'}, status=status.HTTP_400_BAD_REQUEST)
    start_date = parse_date(start)
    end_date = parse_date(end)
    students = Student.objects.filter(start_date__lte=end_date, is_studying=True)
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def graduated_students(request):
    start = request.data.get('start')
    end = request.data.get('end')
    if not start or not end:
        return Response({'error': 'Please provide start and end dates'}, status=status.HTTP_400_BAD_REQUEST)
    start_date = parse_date(start)
    end_date = parse_date(end)
    students = Student.objects.filter(end_date__range=[start_date, end_date], is_graduated=True)
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accepted_students(request):
    start = request.data.get('start')
    end = request.data.get('end')
    if not start or not end:
        return Response({'error': 'Please provide start and end dates'}, status=status.HTTP_400_BAD_REQUEST)
    start_date = parse_date(start)
    end_date = parse_date(end)
    students = Student.objects.filter(start_date__range=[start_date, end_date], is_accepted=True)
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
   

class StudentListByIdsAPIView(APIView):
    permission_classes = [BasePermission]  

    def post(self, request, *args, **kwargs):
        student_ids = request.data.get("student_ids", [])
        students = Student.objects.filter(id__in=student_ids)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentListView(ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    pagination_class = StudentPagination
    

class StudentPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
def student_list_api(request):
    students = Student.objects.all().order_by('id')  
    paginator = StudentPagination()
    result_page = paginator.paginate_queryset(students, request)
    serializer = StudentSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


class StudentUpdateView(UpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]

class StudentRetrieveAPIView(RetrieveAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]

class StudentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=UserAndStudentSerializer)
    def post(self, request):
        user_data = request.data.get('user', {})
        user_serializer = UserSerializer(data=user_data)

        if user_serializer.is_valid():
            user = user_serializer.save(is_student=True)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student_data = request.data.get('student', {})
        student_serializer = StudentSerializer(data=student_data)

        if student_serializer.is_valid():
            phone = user_data.get('phone')
            user_s = User.objects.get(phone=phone)
            student_serializer.validated_data['user'] = user_s
            student = student_serializer.save()
        else:
            user.delete()
            return Response(student_serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class StudentGroupsAPIView(APIView):
    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
        except Teacher.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        groups = Group.objects.filter(g_student=student)
        serializer = GroupSerializer(groups, many=True)

        return Response(serializer.data, status=200)
    
class StudentGroupListView(APIView):
    def post(self, request, *args, **kwargs):
        student_ids = request.data.get("student_ids", [])
        group_ids = request.data.get("group_ids", [])

        students = Student.objects.filter(id__in=student_ids)
        groups = Group.objects.filter(id__in=group_ids)

        student_data = StudentSerializer(students, many=True).data
        group_data = GroupSerializer(groups, many=True).data

        return Response(
            {"students": student_data, "groups": group_data}, 
            status=status.HTTP_200_OK
        )
        
class TeacherCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=UserAndTeacherSerializer)
    def post(self, request):
        user_data = request.data.get('user', {})
        user_serializer = UserSerializer(data=user_data)

        if user_serializer.is_valid():
            user = user_serializer.save(is_teacher=True)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        teacher_data = request.data.get('teacher', {})
        teacher_serializer = TeacherSerializer(data=teacher_data)

        if teacher_serializer.is_valid():
            phone = user_data.get('phone')
            user_t = User.objects.get(phone=phone)
            teacher_serializer.validated_data['user'] = user_t
            teacher_serializer.save()
            return Response(teacher_serializer.data, status=status.HTTP_201_CREATED)

        else:
            user.delete()
            return Response(teacher_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    
class TeacherListView(ListAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    pagination_class = Pagination
    permission_classes = [IsAuthenticated]


class VerifySms(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=VerifySMSSerializer)
    def post(self, request):
        serializer = VerifySMSSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            verification_code = serializer.validated_data['verification_code']
            cached_code = str(cache.get(phone_number))
            if verification_code == str(cached_code):
                return Response({
                    'status': True,
                    'detail': 'OTP matched. please proceed for registration'
                })
            else:
                return Response({
                    'status': False,
                    'detail': 'otp INCOORECT'
                })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserApi(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            password = serializer.validated_data.get('password')
            serializer.validated_data['password'] = make_password(password)
            serializer.save()
            return Response({
                'status': True,
                'datail': 'Account create'
            })

    def get(self, request):
        users = User.objects.all().order_by('-id')
        serializer = UserSerializer(users, many=True)
        return Response(data=serializer.data)

class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def patch(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(instance=self.request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DepartmentsApiView(ModelViewSet):
    queryset = Departments.objects.all().order_by('-id')
    serializer_class = DepartmentsSerializer
    pagination_class = PageNumberPagination

class DepartmentsViewSet(viewsets.ViewSet):
    permission_classes = [PageNumberPagination]

    def list(self, request):
        departments = Departments.objects.all()
        paginator = Pagination()
        result_page = paginator.paginate_queryset(departments, request)
        serializer = DepartmentsSerializer(result_page, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        serializer = DepartmentsSerializer(department)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='create/department')
    @swagger_auto_schema(request_body=DepartmentsSerializer)
    def create_department(self, request):
        serializer = DepartmentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='update/department')
    def update_department(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        serializer = DepartmentsSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete/department')
    def delete_department(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        department.delete()
        return Response({'status':True,'detail': 'Department deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='add-worker')
    @swagger_auto_schema(request_body=DepartamentAddWorker)
    def add_worker(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        serializer = DepartamentAddWorker(data=request.data)

        if serializer.is_valid():
            worker_id = serializer.validated_data['worker_id']
            worker = get_object_or_404(Worker, pk=worker_id)
            worker.department = department
            worker.save()

            return Response({'status':True,'detail': f'Worker {worker.user.phone} added to department {department.title}'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseApiView(ModelViewSet):
    queryset = Course.objects.all().order_by('-id')
    serializer_class = CourseSerializer
    pagination_class = PageNumberPagination


class CourseStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Sanalar oralig‘ida kurslar statistikasi",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["start_date", "end_date"],
            properties={
                "start_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Boshlanish sanasi"),
                "end_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Tugash sanasi"),
            },
        ),
        responses={200: "Statistika qaytarildi"},
    )
    def post(self, request):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if not start_date or not end_date:
            return Response({"error": "start_date va end_date talab qilinadi"}, status=400)

        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date or not end_date:
            return Response({"error": "Noto‘g‘ri sana formati"}, status=400)

        stats = Course.objects.filter(created_at__range=[start_date, end_date]).count()

        return Response({"total_courses": stats})

    @swagger_auto_schema(
        operation_description="Yangi kurs yaratish",
        request_body=CourseSerializer,
        responses={201: "Kurs yaratildi"},
    )
    def create(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=WorkerSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = str(serializer.validated_data.get('user'))
            try:
                user = User.objects.get(phone=user_id)
                user.is_teacher = True
                user.save()
                serializer.save()

            except Exception as e:
                print(e)
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        teacher = Worker.objects.filter(user__is_teacher=True).order_by('-id')
        serializer = WorkerSerializer(instance=teacher, many=True)
        return Response(data=serializer.data)

class TeacherListView(ListAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    pagination_class = Pagination

class TeacherListCreateView(generics.ListCreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

# Bitta Teacher ni olish
class TeacherDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

# Comment yaratish
class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

class TeacherUpdateView(UpdateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    lookup_field = 'id'

class TeacherRetrieveAPIView(RetrieveAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    lookup_field = 'id'

class TeacherCreateAPIView(APIView):

    @swagger_auto_schema(request_body=UserAndTeacherSerializer)
    def post(self, request):
        user_data = request.data.get('user', {})
        user_serializer = UserSerializer(data=user_data)

        if user_serializer.is_valid():
            user = user_serializer.save(is_worker=True)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        teacher_data = request.data.get('teacher', {})   
        teacher_serializer = TeacherSerializer(data=teacher_data)

        if teacher_serializer.is_valid():
            teacher = teacher_serializer.save(user=user)
            return Response(TeacherSerializer(teacher).data, status=status.HTTP_201_CREATED)
        else:
            user.delete()
            return Response(teacher_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherGroupsAPIView(APIView):
    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found"}, status=404)

        groups = teacher.groups.all()
        serializer = GroupSerializer(groups, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class WorkerApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')

            user = User.objects.get(phone=f"{user_id}")
            user.is_staff = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        worker = Worker.objects.filter(user__is_staff=True).order_by('-id')
        serializer = WorkerSerializer(worker, many=True)
        return Response(data=serializer.data)

class WorkerApiViewId(APIView):
    def get(self, request, pk):
        try:
            worker = Worker.objects.get(pk=pk)
            serializer = WorkerSerializer(worker)
            return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def put(self, request, pk):
        try:
            teacher = Worker.objects.get(id=pk)
            serializer = WorkerSerializer(teacher, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def patch(self, request, pk):
        try:
            teacher = Worker.objects.get(pk=pk)
            serializer = WorkerSerializer(teacher, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

class WorkerApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=WorkerSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')
            user = User.objects.get(phone=user_id)
            user.is_staff = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        worker = Worker.objects.filter(user__is_staff=True).order_by('-id')
        serializer = WorkerSerializer(worker, many=True)
        return Response(data=serializer.data)

class RoomAPIView(ModelViewSet):
    queryset = Rooms.objects.all().order_by('-id')
    serializer_class = RoomSerializer
    pagination_class = PageNumberPagination

class DayAPIView(ModelViewSet):
    queryset = Day.objects.all().order_by('-id')
    serializer_class = DaySerializer
    pagination_class = PageNumberPagination

class WorkerApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=WorkerSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')
            user = User.objects.get(phone=user_id)
            user.is_staff = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        worker = Worker.objects.filter(user__is_staff=True).order_by('-id')
        serializer = WorkerSerializer(worker, many=True)
        return Response(data=serializer.data)


class StudentApiView(APIView):
    pagination_class = PageNumberPagination
    @swagger_auto_schema(request_body=StudentSerializer)
    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')
            user = User.objects.get(phone=user_id)
            user.is_student = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        student = Student.objects.filter(user__is_student=True).order_by('-id')
        group = Group.objects.all().order_by('-id')
        course = Course.objects.all().order_by('-id')
        serializer_student = StudentSerializer(student, many=True)
        serializer_group = GroupSerializer(group, many=True)
        serializer_course = CourseSerializer(course, many=True)
        data = {
            "students": serializer_student.data,
            "groups": serializer_group.data,
            "courses": serializer_course.data
        }
        return Response(data=data)

class StudentApiViewId(APIView):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
            serializer = StudentSerializer(student)
            return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def put(self, request, pk):
        try:
            student = Student.objects.get(id=pk)
            serializer = StudentSerializer(student, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def patch(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
            serializer = StudentSerializer(student, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})
        

class GroupListCreateView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class GroupRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class GroupApiView(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = Group.objects.all().order_by('-id')
    serializer_class = GroupSerializer

class GroupApi(APIView):
    pagination_class = PageNumberPagination
    def get(self, request):
        teachers = Worker.objects.filter(user__is_teacher=True).order_by('-id')
        courses = Course.objects.all().order_by('-id')
        tables = Table.objects.all().order_by('-id')
        serializer_teachers = WorkerSerializer(teachers, many=True)
        serializer_courses = CourseSerializer(courses, many=True)
        serializer_table = TableSerializer(tables, many=True)

        datas = {
            "teachers": serializer_teachers.data,
            "courses": serializer_courses.data,
            "tables": serializer_table.data
        }
        return Response(data=datas)

class GroupListByIdsAPIView(APIView):
    def post(self, request, *args, **kwargs):
        group_ids = request.data.get("group_ids", []) 
        groups = Group.objects.filter(id__in=group_ids)  
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GroupStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Sanalar oralig‘ida guruhlar statistikasi",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["start_date", "end_date"],
            properties={
                "start_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Boshlanish sanasi"),
                "end_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Tugash sanasi"),
            },
        ),
        responses={200: "Statistika qaytarildi"},
    )
    def post(self, request):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if not start_date or not end_date:
            return Response({"error": "start_date va end_date talab qilinadi"}, status=400)

        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date or not end_date:
            return Response({"error": "Noto‘g‘ri sana formati"}, status=400)

        stats = Group.objects.filter(created_at__range=[start_date, end_date]).count()

        return Response({"total_groups": stats})

    @swagger_auto_schema(
        operation_description="Yangi guruh yaratish",
        request_body=GroupSerializer,
        responses={201: "Guruh yaratildi"},
    )
    def create(self, request):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TableTypeApi(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = TableType.objects.all().order_by('-id')
    serializer_class = TableTypeSerializer

class TableApi(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = Table.objects.all().order_by('-id')
    serializer_class = TableSerializer

class TopicsApi(ModelViewSet):
    queryset = Topics.objects.all().order_by('-id')
    serializer_class = TopicsSerializer
    pagination_class = PageNumberPagination

class AttendanceLevelApi(ModelViewSet):
    queryset = AttendanceLevel.objects.all().order_by('-id')
    serializer_class = AttendanceLevelSerializer
    pagination_class = PageNumberPagination

class AttendanceStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Sanalar oralig‘ida davomat statistikasi",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["start_date", "end_date"],
            properties={
                "start_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Boshlanish sanasi"),
                "end_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Tugash sanasi"),
            },
        ),
        responses={200: "Statistika qaytarildi"},
    )
    def post(self, request):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if not start_date or not end_date:
            return Response({"error": "start_date va end_date talab qilinadi"}, status=400)

        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date or not end_date:
            return Response({"error": "Noto‘g‘ri sana formati"}, status=400)

        stats = Attendance.objects.filter(date__range=[start_date, end_date]).values("status").annotate(count=Count("id"))
        return Response(stats)
    
    def create(self, request):
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AttendanceStatusViewSet(viewsets.ModelViewSet):
    queryset = AttendanceStatus.objects.all().order_by('-created_at')
    serializer_class = AttendanceStatusSerializer
    permission_classes = [IsAuthenticated]

    
class AttendanceLevelView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AttendanceLevelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        attendance_levels = AttendanceLevel.objects.all()
        serializer = AttendanceLevelSerializer(attendance_levels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TokenObtainView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
     
class GroupHomeWorkApi(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = GroupHomeWork.objects.all().order_by('-id')
    serializer_class = GroupHomeWorkSerializer

class HomeWorkApi(ModelViewSet):
    queryset = HomeWork.objects.all().order_by('-id')
    serializer_class = HomeWorkSerializer
    pagination_class = PageNumberPagination


class ParentsViewSet(viewsets.ViewSet):
    """
    Ota-onalar uchun CRUD API.
    """
    queryset = Parents.objects.all()
    serializer_class = ParentsSerializer
    permission_classes = [BasePermission]

    def list(self, request):
        """
        Barcha ota-onalarni ro‘yxatini qaytaradi.
        """
        parents = Parents.objects.all()
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(parents, request)
        serializer = ParentsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Bitta ota-onaning ma'lumotlarini olish.
        """
        parent = get_object_or_404(Parents, pk=pk)
        serializer = ParentsSerializer(parent)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='create/parent')
    def create_parent(self, request):
        """
        Ota-onani yaratish uchun API.
        """
        serializer = ParentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='update/parent')
    def update_parent(self, request, pk=None):
        """
        Ota-onaning ma'lumotlarini yangilash.
        """
        parent = get_object_or_404(Parents, pk=pk)
        serializer = ParentsSerializer(parent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete/parent')
    def delete_parent(self, request, pk=None):
        """
        Ota-onani o‘chirish.
        """
        parent = get_object_or_404(Parents, pk=pk)
        parent.delete()
        return Response({'status': True, 'detail': 'Parent muvaffaqiyatli o‘chirildi'}, status=status.HTTP_204_NO_CONTENT)


User = get_user_model()

class RegisterView(APIView):
    """
    Telefon raqam orqali foydalanuvchini ro'yxatdan o'tkazish va OTP yuborish
    """

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response({"error": "Telefon raqami talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 4 xonali tasodifiy OTP yaratish
        otp_code = random.randint(1000, 9999)
        
        # OTP ni vaqtinchalik saqlash (30 daqiqa)
        cache.set(phone, otp_code, timeout=1800)

        return Response({"message": "OTP kod yuborildi", "otp": otp_code}, status=status.HTTP_201_CREATED)

class VerifyOTPView(APIView):
    """
    OTP orqali foydalanuvchini tasdiqlash va akkaunt yaratish
    """

    def post(self, request):
        phone = request.data.get("phone")
        otp_code = request.data.get("otp")

        if not phone or not otp_code:
            return Response({"error": "Telefon raqam va OTP kod talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = cache.get(phone)

        if not stored_otp or str(stored_otp) != str(otp_code):
            return Response({"error": "Noto‘g‘ri yoki eskirgan OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # OTP to‘g‘ri bo‘lsa, foydalanuvchini ro‘yxatdan o‘tkazamiz
        user, created = User.objects.get_or_create(phone=phone)
        
        if created:
            user.set_password(str(otp_code)) 
            user.save()

        # OTP ni cache dan o‘chirish
        cache.delete(phone)

        return Response({"message": "Ro'yxatdan o‘tish muvaffaqiyatli yakunlandi"}, status=status.HTTP_200_OK)
