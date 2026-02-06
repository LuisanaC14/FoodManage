# gestion/templatetags/stock_alerts.py
from django import template
from gestion.models import Producto

register = template.Library()

@register.simple_tag
def get_low_stock_products():
    # Buscamos Bebidas y Extras con menos de 10 unidades
    # Usamos __in para buscar en las categorias que usan stock
    categorias_con_stock = ['Bebidas', 'Bebida', 'Extras', 'Extra']
    
    return Producto.objects.filter(
        categoria__in=categorias_con_stock, 
        stock__lt=10
    ).order_by('stock')