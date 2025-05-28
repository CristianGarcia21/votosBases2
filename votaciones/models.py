# votaciones/models.py
from django.db import models
from django.contrib.auth.models import User

class Votacion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    def __str__(self):
        return self.nombre

class OpcionVoto(models.Model):
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='opciones/')

    def __str__(self):
        return f"{self.nombre} ({self.votacion.nombre})"

class Voto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    opcion = models.ForeignKey(OpcionVoto, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    valido = models.BooleanField(default=True)

    def __str__(self):
        return f"Voto de {self.usuario.username} en {self.opcion.nombre}"

class AuditoriaVoto(models.Model):
    voto = models.ForeignKey(Voto, on_delete=models.CASCADE)
    accion = models.CharField(max_length=50)  # creado, intento_duplicado, etc.
    fecha = models.DateTimeField(auto_now_add=True)
    datos_antes = models.TextField(null=True, blank=True)
    datos_despues = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Auditoría {self.accion} - {self.voto.id}"