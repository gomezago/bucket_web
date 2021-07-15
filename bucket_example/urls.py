from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('login/', views.bucket_login, name='login'),
    path('auth/', views.auth, name='auth'),
    path('thing/', views.create_thing, name='thing'),
    path('prop/', views.create_property, name='prop'),
    path('update/', views.update_property, name='update'),
    path('read/', views.read_property, name='update'),
    path('logout/', views.bucket_logout, name='logout'),
]