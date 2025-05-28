# votaciones/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import RegistroForm

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
    return render(request, 'panel_votaciones.html')

def custom_404(request, exception):
    return redirect('login')