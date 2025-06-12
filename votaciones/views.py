# votaciones/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from .forms import RegistroForm
from .models import OpcionVoto, Voto, AuditoriaVoto, Votacion
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

@login_required
def panel_votaciones(request):
    votaciones = Votacion.objects.all().order_by('id')  # Solo las 2 primeras
    votos_usuario = Voto.objects.filter(usuario=request.user)
    votos_realizados = {voto.opcion.votacion_id for voto in votos_usuario}
    return render(request, 'panel_votaciones.html', {
        'votaciones': votaciones,
        'votos_realizados': votos_realizados
    })

def custom_404(request, exception):
    return redirect('login')

@login_required
def votar(request, opcion_id):
    opcion = get_object_or_404(OpcionVoto, id=opcion_id)
    votacion = opcion.votacion
    usuario = request.user

    # Verifica si ya votó en esta votación
    ya_voto = Voto.objects.filter(usuario=usuario, opcion__votacion=votacion).exists()
    if ya_voto:
        # Opcional: bloquear usuario
        usuario.is_active = False
        usuario.save()
        messages.error(request, "Solo puedes votar una vez. Usuario bloqueado.")
        return redirect('panel_votaciones')

    # Si no ha votado, guarda el voto
    voto = Voto.objects.create(usuario=usuario, opcion=opcion)
    messages.success(request, "¡Voto registrado!")
    return redirect('panel_votaciones')

@require_POST
@login_required
@transaction.atomic  # Esto es importante para asegurar que todos los votos se guardan o ninguno
def confirmar_votos(request):
    usuario = request.user
    votos_procesados = 0
    errores = []
    
    # Verificar si ya votó en alguna de las votaciones
    votaciones_ids = []
    for key in request.POST:
        if key.startswith('opcion_'):
            votacion_id = key.split('_')[1]
            votaciones_ids.append(votacion_id)
    
    ya_voto = Voto.objects.filter(
        usuario=usuario, 
        opcion__votacion__id__in=votaciones_ids
    ).exists()
    
    if ya_voto:
        return JsonResponse({
            'success': False,
            'message': "Ya has votado en al menos una de estas votaciones."
        })
    
    # Procesar los votos
    try:
        for key, opcion_id in request.POST.items():
            if key.startswith('opcion_'):
                votacion_id = key.split('_')[1]
                
                # Obtener la opción
                try:
                    opcion = OpcionVoto.objects.get(id=opcion_id, votacion__id=votacion_id)
                    
                    # Crear el voto
                    Voto.objects.create(usuario=usuario, opcion=opcion)
                    votos_procesados += 1
                    
                except OpcionVoto.DoesNotExist:
                    errores.append(f"Opción inválida para la votación {votacion_id}")
        
        if votos_procesados > 0:
            return JsonResponse({
                'success': True,
                'message': f"¡Tus {votos_procesados} votos han sido registrados correctamente!"
            })
        else:
            return JsonResponse({
                'success': False,
                'message': "No se procesó ningún voto. " + ", ".join(errores)
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f"Error al procesar los votos: {str(e)}"
        })