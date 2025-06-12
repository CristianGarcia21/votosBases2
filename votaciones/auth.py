from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from django.contrib import messages

User = get_user_model()

class BlockedUserBackend(ModelBackend):
    """Backend de autenticación que verifica si un usuario está bloqueado"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Primero usamos el backend estándar para verificar credenciales
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        # Si las credenciales son válidas, verificamos si el usuario está bloqueado
        if user:
            with connection.cursor() as cursor:
                # Verificar el estado de bloqueo directamente en la DB
                cursor.execute(
                    "SELECT BLOQUEADO_HASTA FROM AUTH_USER WHERE ID = %s", 
                    [user.id]
                )
                row = cursor.fetchone()
                
                if row and row[0]:
                    bloqueado_hasta = row[0]
                    now = timezone.now()
                    
                    if bloqueado_hasta > now:
                        # Usuario está bloqueado actualmente
                        if request:
                            tiempo_restante = bloqueado_hasta - now
                            horas = int(tiempo_restante.total_seconds() // 3600)
                            minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
                            
                            mensaje = f"Tu cuenta está bloqueada por intentar votar múltiples veces. "
                            mensaje += f"Podrás acceder nuevamente en {horas}h {minutos}m."
                            
                            messages.error(request, mensaje)
                        
                        # No permitir acceso
                        return None
                    else:
                        # El bloqueo expiró, limpiamos el campo
                        cursor.execute(
                            "UPDATE AUTH_USER SET BLOQUEADO_HASTA = NULL WHERE ID = %s",
                            [user.id]
                        )
                        if request:
                            messages.info(request, "Tu período de bloqueo ha expirado. Ya puedes acceder normalmente.")
        
        return user