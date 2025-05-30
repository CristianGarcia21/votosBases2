# votaciones/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from .forms import RegistroForm
from .models import OpcionVoto, Voto, AuditoriaVoto, Votacion


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
    votaciones = Votacion.objects.all().order_by('id')[:2]  # Solo las 2 primeras
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
        # Registrar intento en auditoría
        AuditoriaVoto.objects.create(
            voto=None,
            accion='intento_duplicado',
            datos_antes=None,
            datos_despues=None
        )
        # Opcional: bloquear usuario
        usuario.is_active = False
        usuario.save()
        messages.error(request, "Solo puedes votar una vez. Usuario bloqueado.")
        return redirect('panel_votaciones')

    # Si no ha votado, guarda el voto
    voto = Voto.objects.create(usuario=usuario, opcion=opcion)
    AuditoriaVoto.objects.create(
        voto=voto,
        accion='creado',
        datos_antes=None,
        datos_despues=None
    )
    messages.success(request, "¡Voto registrado!")
    return redirect('panel_votaciones')