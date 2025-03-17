from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminUserOrReadOnly(BasePermission):
    """
    Admin foydalanuvchilar o'zgartirish va o'chirish huquqiga ega,
    boshqa foydalanuvchilar faqat o'qish huquqiga ega.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsAuthenticatedAndActive(BasePermission):
    """
    Foydalanuvchi autentifikatsiyadan o'tgan va faol bo'lishi kerak.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active
    
class AllowAllUsers(BasePermission):
    """
    Har qanday foydalanuvchiga API dan foydalanishga ruxsat beradi.
    """
    def has_permission(self, request, view):
        return True