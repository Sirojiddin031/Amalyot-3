from django.urls import path
from .views import *

app_name = "app_name"

urlpatterns = [
    path('api/news/', NewsListView.as_view(), name='news-list'),
    path('api/news/statistics/', NewsStatisticsView.as_view(), name='news-statistics'),
    path('news/', NewsListCreateAPIView.as_view(), name='news-list-create'),
    path('news/category/<int:category_id>/', CategoryNewsView.as_view(), name='category-news'),

    path("api/test/", my_api_view, name="my_api_view"),
]
