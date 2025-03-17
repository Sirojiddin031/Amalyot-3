from django.contrib import admin
from django.utils.timezone import now
from .models import *

class CategoriesAdmin(admin.ModelAdmin):
    pass

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'deadline', 'is_expired_status')

    def is_expired_status(self, obj):
        return "O'tmagan" if obj.deadline and obj.deadline >= now() else "O'tgan"

    is_expired_status.short_description = "Muddat"

admin.site.register(News, NewsAdmin)
admin.site.register(Categories, CategoriesAdmin)

# Register your models here.
