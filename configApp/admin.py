from django.contrib import admin
from .models import *


class UserAdmin(admin.ModelAdmin):
    ordering = ['id']
    list_display = (
        ['id', 'phone', 'full_name']
    )

admin.site.register(User, UserAdmin)
admin.site.register(Course)
admin.site.register(Worker)
admin.site.register(Departments)
admin.site.register(Day)
admin.site.register(Rooms)
admin.site.register(Group)
# admin.site.register(Student)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'age', 'start_date', 'end_date', 'is_studying', 'is_graduated', 'is_accepted')
    search_fields = ('full_name', 'email')
    list_filter = ('is_studying', 'is_graduated', 'is_accepted')
    
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'updated')  
    search_fields = ('user__phone', 'descriptions')
    filter_horizontal = ('departments', 'course') 

@admin.register(AttendanceLevel)
class AttendanceLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'level', 'title', 'created_at')  
    search_fields = ('level',)  
    ordering = ('-created_at',) 

@admin.register(Parents)
class ParentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number', 'created_at')
    search_fields = ('full_name', 'phone_number')
    ordering = ('-created_at',)
