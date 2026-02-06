from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Arroz, Sopa, Bebida, Extra, Porcion, Catalogo

def boton_editar(obj):
    # Genera la URL de edición automática según el modelo
    url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
    return format_html(
        '<a class="button" href="{}" style="background:#28a745; color:white; padding:5px 12px; border-radius:5px; text-decoration:none; font-weight:bold; font-size:11px;">'
        '<i class="fas fa-edit me-1"></i>EDITAR</a>', 
        url
    )
boton_editar.short_description = "ACCIONES"

# --- FUNCIÓN PARA MOSTRAR FOTO ---
def imagen_visual(obj):
    from django.utils.html import format_html
    if obj.imagen:
        return format_html('<img src="{}" width="40" height="40" style="border-radius:5px; border:1px solid #555;" />', obj.imagen.url)
    return "-"
imagen_visual.short_description = "FOTO"

# =========================================================
# SIN STOCK + DESCRIPCIÓN (Arroces, Sopas, Porciones)
# =========================================================

# He quitado el campo 'stock' de fields para que no aparezca al editar
@admin.register(Arroz)
class ArrozAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', imagen_visual, boton_editar)
    search_fields = ['nombre']
    fields = ('nombre', 'precio', 'descripcion', 'imagen') # Agregamos descripción

@admin.register(Sopa)
class SopaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', imagen_visual, boton_editar)
    search_fields = ['nombre']
    fields = ('nombre', 'precio', 'descripcion', 'imagen') # Agregamos descripción

@admin.register(Porcion)
class PorcionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', imagen_visual, boton_editar)
    search_fields = ['nombre']
    fields = ('nombre', 'precio', 'descripcion', 'imagen') # Agregamos descripción

# =========================================================
# CON STOCK (Bebidas, Extras)
# =========================================================
@admin.register(Bebida)
class BebidaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', imagen_visual, boton_editar)
    list_editable = ('stock',)
    search_fields = ['nombre']
    # En bebidas si dejamos el stock
    fields = ('nombre', 'precio', 'stock', 'descripcion', 'imagen')

@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', imagen_visual, boton_editar)
    list_editable = ('stock',) 
    search_fields = ['nombre']
    fields = ('nombre', 'precio', 'stock', 'descripcion', 'imagen')

@admin.register(Catalogo)
class CatalogoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'categoria', 'stock', imagen_visual, boton_editar)
    list_filter = ('categoria',)
    search_fields = ['nombre']