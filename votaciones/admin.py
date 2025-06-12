from django.contrib import admin
from django.urls import path
from . import admin_views
from .models import Votacion, OpcionVoto, Voto, AuditoriaVoto

# Personaliza las clases admin para tus modelos
class OpcionVotoInline(admin.TabularInline):
    """
    Inline admin interface for the OpcionVoto model, allowing editing of related OpcionVoto instances directly within the parent model's admin page.
    Displays two extra empty option forms by default.
    """
    model = OpcionVoto
    extra = 2  # Cuántas opciones vacías mostrar por defecto

class VotacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('fecha_inicio', 'fecha_fin')
    inlines = [OpcionVotoInline]
    
    def get_votos_count(self, obj):
        return Voto.objects.filter(opcion__votacion=obj).count()
    get_votos_count.short_description = 'Total Votos'

class VotoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'opcion', 'fecha', 'ip', 'valido')
    list_filter = ('valido', 'opcion__votacion', 'fecha')
    search_fields = ('usuario__username', 'opcion__nombre')
    readonly_fields = ('fecha',)

class AuditoriaVotoAdmin(admin.ModelAdmin):
    list_display = ('accion', 'fecha', 'voto')
    list_filter = ('accion', 'fecha')
    readonly_fields = ('accion', 'fecha', 'voto', 'datos_antes', 'datos_despues')

# Registra los modelos con sus clases admin personalizadas
admin.site.register(Votacion, VotacionAdmin)
admin.site.register(OpcionVoto)
admin.site.register(Voto, VotoAdmin)
admin.site.register(AuditoriaVoto, AuditoriaVotoAdmin)


class CustomAdminSite(admin.AdminSite):
    site_header = 'Administración de Votaciones'
    site_title = 'Portal de Administración'
    index_title = 'Panel de Control'
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard-votaciones/', self.admin_view(admin_views.dashboard_votaciones), 
                 name='dashboard_votaciones'),
            path('dashboard-votaciones/datos/', self.admin_view(admin_views.datos_votacion), 
                 name='datos_votacion'),
            path('dashboard-votaciones/datos/<int:votacion_id>/', 
                 self.admin_view(admin_views.datos_votacion), 
                 name='datos_votacion_detalle'),
        ]
        return custom_urls + urls

# Aplica la personalización al sitio admin existente
admin_site = admin.site
admin_site.__class__ = CustomAdminSite

# Añadir una plantilla personalizada para el índice del admin si quieres
# admin_site.index_template = 'admin/custom_index.html' 