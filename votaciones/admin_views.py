# Al principio del archivo
import plotly.express as px
import pandas as pd
from plotly.offline import plot
from django.utils.safestring import mark_safe
import plotly.graph_objects as go
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db import connection
from votaciones.models import Votacion, OpcionVoto, Voto

def ejecutar_procedimiento_reporte():
    """Ejecuta el procedimiento almacenado que genera el reporte de votaciones"""
    print("Ejecutando procedimiento SP_GENERAR_REPORTE_VOTACIONES...")
    with connection.cursor() as cursor:
        try:
            cursor.callproc('SP_GENERAR_REPORTE_VOTACIONES')
            print("✓ Procedimiento ejecutado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error al ejecutar el procedimiento: {str(e)}")
            return False

def obtener_datos_reporte():
    """Obtiene los datos del reporte de votaciones"""
    print("Consultando datos de REPORTE_VOTACIONES...")
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT VOTACION_ID, VOTACION_NOMBRE, OPCION_ID, OPCION_NOMBRE, 
                       TOTAL_VOTOS, PORCENTAJE
                FROM REPORTE_VOTACIONES
                ORDER BY VOTACION_ID, PORCENTAJE DESC
            """)
            columns = [col[0].lower() for col in cursor.description]
            datos = [dict(zip(columns, row)) for row in cursor.fetchall()]
            print(f"✓ Datos obtenidos: {len(datos)} registros")
            return datos
        except Exception as e:
            print(f"❌ Error al consultar los datos: {str(e)}")
            return []

@staff_member_required
def datos_votacion(request, votacion_id=None):
    """API para obtener datos de una votación específica o todas"""
    # Ejecuta el procedimiento para asegurar datos actualizados
    ejecutar_procedimiento_reporte()
    
    # Obtiene los datos del reporte
    datos_reporte = obtener_datos_reporte()
    
    if votacion_id:
        # Filtra para una votación específica
        datos_votacion = [d for d in datos_reporte if d['votacion_id'] == votacion_id]
        if not datos_votacion:
            return JsonResponse({'error': 'Votación no encontrada'}, status=404)
            
        labels = [d['opcion_nombre'] for d in datos_votacion]
        datos = [d['total_votos'] for d in datos_votacion]
        porcentajes = [d['porcentaje'] for d in datos_votacion]
        
        return JsonResponse({
            'labels': labels,
            'datos': datos,
            'porcentajes': porcentajes,
            'titulo': datos_votacion[0]['votacion_nombre'] if datos_votacion else ''
        })
    else:
        # Datos para todas las votaciones
        resultados = {}
        # Agrupamos los resultados por votación_id
        votaciones_ids = set(d['votacion_id'] for d in datos_reporte)
        
        for v_id in votaciones_ids:
            datos_votacion = [d for d in datos_reporte if d['votacion_id'] == v_id]
            if datos_votacion:
                resultados[str(v_id)] = {
                    'labels': [d['opcion_nombre'] for d in datos_votacion],
                    'datos': [d['total_votos'] for d in datos_votacion],
                    'porcentajes': [d['porcentaje'] for d in datos_votacion],
                    'titulo': datos_votacion[0]['votacion_nombre']
                }
                
        return JsonResponse(resultados)

@staff_member_required
def dashboard_votaciones(request):
    """Dashboard con estadísticas y gráficos de votaciones"""
    print("=== Iniciando función dashboard_votaciones ===")
    
    # Ejecutar el procedimiento almacenado para actualizar los datos
    ejecutar_procedimiento_reporte()
    
    # Obtener los datos del reporte
    datos_reporte = obtener_datos_reporte()
    
    # Obtener lista de votaciones para mantener el resto de la funcionalidad
    votaciones = Votacion.objects.all()
    total_votaciones = votaciones.count()
    
    # Calcular total de votos desde el reporte
    total_votos = sum(d['total_votos'] for d in datos_reporte)
    print(f"Total votaciones: {total_votaciones}")
    print(f"Total votos: {total_votos}")
    
    # Añadir totales a cada votación desde el reporte
    for votacion in votaciones:
        votos_votacion = sum(d['total_votos'] for d in datos_reporte if d['votacion_id'] == votacion.id)
        votacion.total_votos = votos_votacion
        print(f"Votación ID {votacion.id}: {votacion.nombre} - {votacion.total_votos} votos")
    
    # Generar gráficos con los datos del reporte
    graficos = {}
    
    try:
        # Agrupar datos por votación
        votaciones_ids = set(d['votacion_id'] for d in datos_reporte)
        
        for votacion_id in votaciones_ids:
            print(f"\nProcesando votación ID {votacion_id}")
            
            # Filtrar datos para esta votación
            datos_votacion = [d for d in datos_reporte if d['votacion_id'] == votacion_id]
            
            if datos_votacion:
                nombre_votacion = datos_votacion[0]['votacion_nombre']
                print(f"  - Votación: {nombre_votacion}")
                print(f"  - Opciones con votos encontradas: {len(datos_votacion)}")
                
                print(f"  - Detalle de opciones:")
                for d in datos_votacion:
                    print(f"    • {d['opcion_nombre']}: {d['total_votos']} votos ({d['porcentaje']}%)")
                
                try:
                    # Crear DataFrame para el gráfico
                    df = pd.DataFrame(datos_votacion)
                    df_grafico = pd.DataFrame({
                        'Opción': df['opcion_nombre'],
                        'Votos': df['total_votos'],
                        'Porcentaje': df['porcentaje']
                    })
                    print(f"  ✓ DataFrame creado correctamente")
                    
                    # Añadir el porcentaje al nombre de la opción para el gráfico
                    df_grafico['Etiqueta'] = df_grafico.apply(
                        lambda x: f"{x['Opción']} ({x['Porcentaje']}%)", axis=1
                    )
                    
                    # Crear gráfico circular
                    fig = px.pie(
                        df_grafico, 
                        values='Votos',
                        names='Etiqueta',
                        title=nombre_votacion,
                        hole=0.4
                    )
                    print(f"  ✓ Figura de gráfico creada correctamente")
                    
                    # Configurar layout
                    fig.update_layout(
                        autosize=True,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                    )
                    print(f"  ✓ Layout de gráfico actualizado")
                    
                    # Convertir a HTML
                    grafico_html = plot(fig, output_type='div', include_plotlyjs=True)
                    graficos[votacion_id] = mark_safe(grafico_html)
                    print(f"  ✓ Gráfico convertido a HTML y guardado para votación {votacion_id}")
                    
                except Exception as e:
                    print(f"  ❌ Error al crear gráfico: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ❌ No hay datos para esta votación")
                
        # Generar gráfico de barras para comparar todas las votaciones
        try:
            # Agrupar por votación para el gráfico general
            datos_resumen = []
            for votacion_id in votaciones_ids:
                datos_votacion = [d for d in datos_reporte if d['votacion_id'] == votacion_id]
                if datos_votacion:
                    total = sum(d['total_votos'] for d in datos_votacion)
                    datos_resumen.append({
                        'Votación': datos_votacion[0]['votacion_nombre'],
                        'Total Votos': total
                    })
            
            if datos_resumen:
                df_resumen = pd.DataFrame(datos_resumen)
                fig_general = px.bar(
                    df_resumen,
                    x='Votación',
                    y='Total Votos',
                    title='Comparativa de participación por votación',
                    color='Total Votos',
                    text='Total Votos'
                )
                
                fig_general.update_traces(texttemplate='%{text}', textposition='outside')
                
                grafico_general = plot(fig_general, output_type='div', include_plotlyjs=False)
                grafico_general = mark_safe(grafico_general)
            else:
                grafico_general = None
        except Exception as e:
            print(f"❌ Error al crear gráfico general: {str(e)}")
            grafico_general = None
                
    except Exception as e:
        print(f"❌ Error general en la generación de gráficos: {str(e)}")
        import traceback
        traceback.print_exc()
        grafico_general = None
    
    print(f"\nTotal de gráficos generados: {len(graficos)}")
    print(f"IDs de votaciones con gráficos: {list(graficos.keys())}")
    
    votaciones_dict = {votacion.id: votacion for votacion in votaciones}
    
    context = {
        'votaciones': votaciones_dict,  # Ahora es un diccionario
        'total_votaciones': total_votaciones,
        'total_votos': total_votos,
        'graficos': graficos,
        'grafico_general': grafico_general,
        'titulo': 'Dashboard de Votaciones',
    }
    
    return render(request, 'admin/dashboard_votaciones.html', context)

@staff_member_required
def grafico_modal(request, votacion_id):
    """API que devuelve los datos del gráfico para un modal específico"""
    print(f"Ejecutando grafico_modal para votación {votacion_id}")
    ejecutar_procedimiento_reporte()
    
    # Obtener los datos del reporte
    datos_reporte = obtener_datos_reporte()
    
    # Filtrar datos para esta votación
    datos_votacion = [d for d in datos_reporte if d['votacion_id'] == votacion_id]
    
    if not datos_votacion:
        return JsonResponse({'error': 'No hay datos para esta votación'}, status=404)
        
    try:
        # Preparar datos en formato adecuado para el gráfico
        opciones = [d['opcion_nombre'] for d in datos_votacion]
        votos = [d['total_votos'] for d in datos_votacion]
        porcentajes = [d['porcentaje'] for d in datos_votacion]
        etiquetas = [f"{op} ({pct}%)" for op, pct in zip(opciones, porcentajes)]
        
        return JsonResponse({
            'titulo': datos_votacion[0]['votacion_nombre'],
            'datos': {
                'labels': etiquetas,
                'values': votos
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)