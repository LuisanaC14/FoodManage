from django import template
from django.contrib.admin.models import LogEntry
from gestion.models import Pedido

register = template.Library()

@register.simple_tag
def get_historial_acciones():
    """Trae las últimas 10 acciones del sistema (LogEntry)"""
    return LogEntry.objects.select_related('content_type', 'user').order_by('-action_time')[:10]

@register.simple_tag
def get_pedidos_pendientes():
    """Trae los pedidos activos (No pagados ni entregados)"""
    return Pedido.objects.filter(
        estado__in=['Pendiente', 'En preparación', 'Listo']
    ).order_by('fecha_pedido')[:10]