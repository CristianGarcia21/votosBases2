# votaciones/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('panel/', views.panel_votaciones, name='panel_votaciones'),
    path('votar/<int:opcion_id>/', views.votar, name='votar'),
]