# votaciones/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('panel/', views.panel_votaciones, name='panel_votaciones'),
    # Añade esta ruta a tus urlpatterns
    path('confirmar-votos/', views.confirmar_votos, name='confirmar_votos'),
]