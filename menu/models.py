from django.db import models
from gestion.models import Producto 

# ==========================================
# 1. DEFINIMOS LOS FILTROS (MANAGERS)
# ==========================================

class BebidaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(categoria__in=['Bebidas', 'Bebida', 'bebidas', 'bebida'])

class ArrozManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(categoria__in=['Arroces', 'Arroz', 'arroces', 'arroz'])

class SopaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(categoria__in=['Sopas', 'Sopa', 'sopas', 'sopa'])

class ExtraManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(categoria__in=['Extras', 'Extra', 'extras', 'extra'])

class PorcionManager(models.Manager):  # <--- NUEVO MANAGER
    def get_queryset(self):
        return super().get_queryset().filter(categoria__in=['Porciones', 'Porcion', 'porciones', 'porcion'])

# ==========================================
# 2. MODELOS PROXY
# ==========================================

class Catalogo(Producto):
    class Meta:
        proxy = True
        verbose_name = "Ver Menú Completo"
        verbose_name_plural = "Ver Menú Completo"

class Bebida(Producto):
    objects = BebidaManager()
    class Meta:
        proxy = True
        verbose_name = "Bebidas"
        verbose_name_plural = "Bebidas"

class Arroz(Producto):
    objects = ArrozManager()
    class Meta:
        proxy = True
        verbose_name = "Arroces"
        verbose_name_plural = "Arroces"

class Sopa(Producto):
    objects = SopaManager()
    class Meta:
        proxy = True
        verbose_name = "Sopas"
        verbose_name_plural = "Sopas"

class Extra(Producto):
    objects = ExtraManager()
    class Meta:
        proxy = True
        verbose_name = "Extras"
        verbose_name_plural = "Extras"

class Porcion(Producto): # <--- NUEVO MODELO
    objects = PorcionManager()
    class Meta:
        proxy = True
        verbose_name = "Porciones"
        verbose_name_plural = "Porciones"