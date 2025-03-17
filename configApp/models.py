from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# ---------------------------
# Custom User va Manager
# ---------------------------
class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('The Phone number must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')
        return self.create_user(phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,14}$',
        message="Phone number must be entered in the format: '998900404001'. Up to 14 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    full_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(unique=False, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    password = models.CharField(max_length=255)
    
    username = None
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

# ---------------------------
# Teacher model
# ---------------------------
class Teacher(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    experience = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departments = models.ManyToManyField('Departments', related_name='teachers')
    course = models.ManyToManyField('Course', related_name="teachers")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    descriptions = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.user.phone

    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'

# ---------------------------
# Course model
# ---------------------------
class Course(models.Model):
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=50)
    descriptions = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.title

# ---------------------------
# Enrollment model
# ---------------------------
class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('registered', 'Registered'),
        ('studying', 'Studying'),
        ('graduated', 'Graduated'),
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    date_joined = models.DateField()

    def __str__(self):
        return f"{self.student} - {self.course} ({self.status})"

# ---------------------------
# Worker model
# ---------------------------
class Worker(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departments = models.ManyToManyField('Departments', related_name='workers')
    course = models.ManyToManyField(Course, related_name='workers')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.user.phone

# ---------------------------
# Comment model
# ---------------------------
class Comment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.teacher.name}"

# ---------------------------
# Departments model
# ---------------------------
class Departments(models.Model):
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    descriptions = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

# ---------------------------
# Student model
# ---------------------------
class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    age = models.IntegerField()
    # Bir student bir nechta guruhga tegishli bo'lishi mumkin
    groups = models.ManyToManyField('Group', related_name='student_groups', blank=True)
    course = models.ManyToManyField(Course, related_name='student_courses', blank=True)
    is_line = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    descriptions = models.CharField(max_length=500, blank=True, null=True)
    # Qo'shimcha maydonlar – filtrlar uchun
    start_date = models.DateField(null=True, blank=True)   # Qabul qilingan sana
    end_date = models.DateField(null=True, blank=True)     # Bitirgan sana
    is_studying = models.BooleanField(default=False)       # Hozir o'qiyotgan
    is_graduated = models.BooleanField(default=False)      # Bitirgan
    is_accepted = models.BooleanField(default=False)       # Qabul qilingan

    def __str__(self):
        return self.user.phone

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['id']

# ---------------------------
# Parents model
# ---------------------------
class Parents(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    descriptions = models.CharField(max_length=500, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

# ---------------------------
# Day model
# ---------------------------
class Day(models.Model):
    title = models.CharField(max_length=50)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

# ---------------------------
# Rooms model
# ---------------------------
class Rooms(models.Model):
    title = models.CharField(max_length=50)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

# ---------------------------
# TableType model
# ---------------------------
class TableType(models.Model):
    title = models.CharField(max_length=50)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

# ---------------------------
# Table model
# ---------------------------
class Table(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Rooms, on_delete=models.RESTRICT)
    type = models.ForeignKey(TableType, on_delete=models.RESTRICT)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

# ---------------------------
# Group model
# ---------------------------
class Group(models.Model):
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=50, unique=True)
    course = models.ForeignKey(Course, on_delete=models.RESTRICT)
    teacher = models.ManyToManyField(Worker, related_name='teacher_groups')
    table = models.ForeignKey(Table, on_delete=models.RESTRICT)
    created = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    start_date = models.DateField()
    start_time = models.TimeField()
    schedule = models.TimeField()
    end_date = models.DateField()
    price = models.CharField(max_length=15, blank=True, null=True)
    descriptions = models.CharField(max_length=500, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.schedule.strftime('%H:%M')})"

# ---------------------------
# Topics model
# ---------------------------
class Topics(models.Model):
    title = models.CharField(max_length=50)
    course = models.ForeignKey(Course, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

# ---------------------------
# GroupHomeWork model
# ---------------------------
class GroupHomeWork(models.Model):
    group = models.ForeignKey(Group, on_delete=models.RESTRICT)
    topic = models.ForeignKey(Topics, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

# ---------------------------
# HomeWork model
# ---------------------------
class HomeWork(models.Model):
    groupHomeWork = models.ForeignKey(GroupHomeWork, on_delete=models.RESTRICT)
    price = models.CharField(max_length=5, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.RESTRICT)
    link = models.URLField()
    is_active = models.BooleanField(default=False)
    descriptions = models.CharField(max_length=500, blank=True, null=True)

# ---------------------------
# AttendanceLevel model
# ---------------------------
class AttendanceLevel(models.Model):
    level = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.level

# ---------------------------
# AttendanceStatus model
# ---------------------------
class AttendanceStatus(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# ---------------------------
# Attendance model
# ---------------------------
class Attendance(models.Model):
    level = models.ForeignKey(AttendanceLevel, on_delete=models.RESTRICT)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    student = models.ForeignKey(Student, on_delete=models.RESTRICT)
    group = models.ForeignKey(Group, on_delete=models.RESTRICT)

    def __str__(self):
        return str(self.level)
