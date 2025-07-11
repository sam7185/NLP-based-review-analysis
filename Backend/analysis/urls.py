from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('loading/', views.loading, name='loading'),
    path('result/<str:hotel_name>/', views.result, name='result'),
]

