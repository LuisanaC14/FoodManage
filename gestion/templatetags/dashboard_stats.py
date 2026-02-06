# gestion/templatetags/dashboard_stats.py
from django import template
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.admin.models import LogEntry
from gestion.models import Pedido, DetallePedido, Reserva

register = template.Library()

@register.simple_tag
def get_kpi_stats():
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=6)

    # 1. VENTAS DE HOY
    ventas_raw = Pedido.objects.filter(
        fecha_pedido__date=hoy
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # FORMATO EN PYTHON 
    ventas_hoy = "{:.2f}".format(float(ventas_raw))

    # 2. PEDIDOS HOY
    pedidos_hoy = Pedido.objects.filter(fecha_pedido__date=hoy).count()

    # 3. PLATO MÁS VENDIDO
    top_plato = DetallePedido.objects.values('producto__nombre').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido').first()
    
    nombre_top = top_plato['producto__nombre'] if top_plato else "N/A"
    cantidad_top = top_plato['total_vendido'] if top_plato else 0

    # 4. DATOS PARA LA GRÁFICA
    fechas = []
    totales = []
    
    for i in range(7):
        fecha = hace_7_dias + timedelta(days=i)
        ventas_dia = Pedido.objects.filter(
            fecha_pedido__date=fecha
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        fechas.append(fecha.strftime("%d/%m")) 
        totales.append(float(ventas_dia))

    return {
        'ventas_hoy': ventas_hoy,   
        'pedidos_hoy': pedidos_hoy,
        'top_plato': nombre_top,
        'top_cantidad': cantidad_top,
        'chart_labels': fechas,
        'chart_data': totales,
        'fecha_actual': hoy,
    }

@register.simple_tag
def get_proximas_reservas():
    """Trae las reservas de hoy en adelante, ordenadas por fecha y hora"""
    hoy = timezone.now().date()
    # Filtramos reservas desde hoy, que no estén canceladas
    return Reserva.objects.filter(
        fecha__gte=hoy
    ).exclude(estado='Cancelada').order_by('fecha', 'hora')[:6]

@register.simple_tag
def get_pedidos_web_pendientes():
    """Busca pedidos que inicien con la palabra 'WEB' en observaciones"""
    # Filtramos por observaciones y excluimos los que ya están listos o pagados
    return Pedido.objects.filter(
        observaciones__startswith='WEB', 
        estado__in=['Pendiente', 'En preparación']
    ).order_by('-fecha_pedido')

@register.simple_tag
def check_caja_abierta():
    """Verifica si existe una sesión de caja abierta actualmente"""
    from gestion.models import SesionCaja
    return SesionCaja.objects.filter(estado='Abierta').exists()

@register.simple_tag
def check_hora_cierre():
    """Devuelve True si es tarde (después de las 18:00) y la caja sigue abierta"""
    from django.utils import timezone
    from gestion.models import SesionCaja
    
    ahora = timezone.localtime(timezone.now())
    
    # 1. Verificamos si la caja está abierta
    caja_abierta = SesionCaja.objects.filter(estado='Abierta').exists()
    
    # 2. Verificamos si son las 6 PM (18:00) o más
    es_tarde = ahora.hour >= 18  # Formato 24 horas
    
    # Solo mostramos la alerta si AMBAS cosas son verdad
    return caja_abierta and es_tarde