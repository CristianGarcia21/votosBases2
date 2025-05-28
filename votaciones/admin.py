# votaciones/admin.py
from django.contrib import admin
from .models import Votacion, OpcionVoto, Voto, AuditoriaVoto

admin.site.register(Votacion)
admin.site.register(OpcionVoto)
admin.site.register(Voto)
admin.site.register(AuditoriaVoto)