from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView
from .serializers import NewsSerializer
from rest_framework.filters import OrderingFilter
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from .models import News
from rest_framework.generics import ListAPIView
from .models import News
from .serializers import NewsSerializer

class CategoryNewsView(ListAPIView):
    serializer_class = NewsSerializer

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return News.objects.filter(category_id=category_id)

class NewsListCreateAPIView(generics.ListCreateAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    
class NewsListView(ListAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_ed'] 
    
class NewsStatisticsView(APIView):
    def get(self, request):
        expired_count = News.objects.filter(deadline__lt=now()).count()  
        not_expired_count = News.objects.filter(deadline__gte=now()).count()
        return Response({
            "expired_count": expired_count,
            "not_expired_count": not_expired_count
        })


class CategoryNewsView(APIView):
    def get(self, request, category_id):
        news = News.objects.filter(category_id=category_id)

        if not news.exists():
            return Response({"detail": "Bu kategoriya bo‘yicha yangiliklar topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = NewsSerializer(news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt 
def my_api_view(request):
    response = JsonResponse({"message": "Success"})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# Create your views here.
