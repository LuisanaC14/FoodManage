from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Max
from datetime import timedelta

# 1. CATEGORÍAS (Se quedan aquí porque Producto las usa)
CATEGORIAS = [
    ('bebida', 'Bebidas'),
    ('arroz', 'Arroces'),
    ('sopa', 'Sopas'),
    ('extra', 'Extras'),
    ('otro', 'Otros'),
]

# 2. MODELO PRINCIPAL (Aquí nace el producto)
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='otro', verbose_name="Categoría")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    descripcion = models.TextField(blank=True, null=True, help_text="Añade una descripción breve del plato.")
    
    def __str__(self):
        return f"{self.nombre} (${self.precio})"

    class Meta:
        verbose_name = "Producto Base"
        verbose_name_plural = "Productos Base"

# 3. OTROS MODELOS OPERATIVOS
class Mesa(models.Model):
    PISOS = [('Piso 1', 'Piso 1'), ('Piso 2', 'Piso 2')]
    
    # Opciones que coinciden con tus clases CSS
    FORMAS = [
        ('mesa-cuadrada', 'Cuadrada (Estándar)'),
        ('mesa-redonda', 'Redonda (Rústica)'),
        ('mesa-larga', 'Rectangular (Larga)'),
    ]

    numero = models.IntegerField(unique=True)
    capacidad = models.IntegerField()
    piso = models.CharField(max_length=10, choices=PISOS, default='Piso 1')
    
    # --- NUEVOS CAMPOS PARA EL MAPA ---
    forma = models.CharField(max_length=20, choices=FORMAS, default='mesa-cuadrada')
    pos_x = models.IntegerField(default=10, verbose_name="Posición X (%)", help_text="Distancia desde la izquierda (0 a 90)")
    pos_y = models.IntegerField(default=10, verbose_name="Posición Y (%)", help_text="Distancia desde arriba (0 a 90)")

    def __str__(self):
        return f"Mesa {self.numero} ({self.piso})"

class Reserva(models.Model):
    # Opciones de estado
    ESTADOS_RESERVA = [
        ('Pendiente', 'Pendiente'),
        ('Confirmada', 'Confirmada'),
        ('Cancelada', 'Cancelada'),
        ('Finalizada', 'Finalizada'),
    ]
    telefono = models.CharField(max_length=15, verbose_name="Teléfono", help_text="Ej: 0991234567", null=True, blank=True)
    numero_personas = models.PositiveIntegerField(default=2, verbose_name="N° Personas")
    cliente = models.CharField(max_length=100)
    fecha = models.DateField()
    hora = models.TimeField()
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, verbose_name="Mesa Seleccionada")
    asistio = models.BooleanField(default=False)
    notas = models.TextField(blank=True, null=True, verbose_name="Notas Especiales / Decoración")
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='Pendiente') 

    def __str__(self):
        return f"{self.cliente} - {self.mesa} - {self.fecha} {self.hora}"
    
class ReservaPlato(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='platos_preordenados')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    nota_plato = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nota del Plato")

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    class Meta:
        verbose_name = "Plato Pre-ordenado"
        verbose_name_plural = "Pre-orden de Comida"

class Asistencia(models.Model):
    empleado = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    hora_entrada = models.TimeField(auto_now_add=True)
    nota = models.CharField(max_length=255, null=True, blank=True, verbose_name="Motivo de retraso")
    
    def __str__(self):
        return f"{self.empleado.username} - {self.fecha}"

class Venta(models.Model):
    class Meta:
        verbose_name = "Venta/Caja"
        verbose_name_plural = "Ventas/Caja"
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha_venta = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    metodo_pago = models.CharField(max_length=50, choices=[
        ('Efectivo', 'Efectivo'), 
        ('Transferencia', 'Transferencia')
    ])

    def __str__(self):
        return f"Venta {self.id} - {self.producto.nombre}"

class Pedido(models.Model):
    # AGREGAMOS 'Cancelado' PARA NO TENER QUE BORRAR Y DAÑAR EL CONTEO
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En preparación', 'En preparación'),
        ('Listo', 'Listo'),
        ('Pagado', 'Pagado'),
        ('Cancelado', 'Cancelado'), #
    ]
    
    OPCIONES_PAGO = [
        ('Pendiente', '---'),
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia')
    ]

    mesero = models.ForeignKey('auth.User', on_delete=models.CASCADE) 
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observaciones = models.TextField(blank=True, null=True, verbose_name="Notas Generales")

    # DATOS CLIENTE
    cliente_nombre = models.CharField(max_length=200, default="Consumidor Final")
    cliente_cedula = models.CharField(max_length=13, default="9999999999")
    cliente_telefono = models.CharField(max_length=20, verbose_name="Teléfono", blank=True, null=True)
    cliente_direccion = models.CharField(max_length=200, verbose_name="Dirección", blank=True, null=True)
    cliente_email = models.EmailField(verbose_name="Correo", blank=True, null=True)

    metodo_pago = models.CharField(max_length=20, choices=OPCIONES_PAGO, default='Pendiente')
    comprobante_pago = models.ImageField(upload_to='comprobantes/', null=True, blank=True, verbose_name="Foto Transferencia")

    # TICKET DIARIO 
    numero_diario = models.PositiveIntegerField(default=1, editable=False, verbose_name="ID")

    def save(self, *args, **kwargs):
        if not self.pk:  # Solo si es nuevo
            ultimo = Pedido.objects.aggregate(Max('numero_diario'))
            mayor = ultimo['numero_diario__max']
        
            self.numero_diario = (mayor + 1) if mayor else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido #{self.numero_diario} - {self.cliente_nombre}"

class DetallePedido(models.Model): # <--- CAMBIO IMPORTANTE: models.Model
    # Relaciones y Datos
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    # TU CAMPO DE NOTA
    nota = models.CharField(max_length=200, null=True, blank=True)

    # El salvavidas del precio
    def save(self, *args, **kwargs):
        if not self.precio_unitario and self.producto:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        if self.cantidad and self.precio_unitario:
            return self.cantidad * self.precio_unitario
        return 0
        
# =========================================================
# 5. CALCULADORA AUTOMÁTICA DE TOTALES (SIGNALS)
# =========================================================

@receiver(post_save, sender=DetallePedido)
@receiver(post_delete, sender=DetallePedido)
def actualizar_total_pedido(sender, instance, **kwargs):
    """
    Cada vez que se guarda o borra un plato, esta función corre,
    suma todo lo que hay en la mesa y actualiza el recibo final.
    """
    pedido = instance.pedido
    
    # Sumamos: Cantidad * Precio de cada plato en el pedido
    nuevo_total = 0
    for detalle in pedido.detalles.all():
        # Nos aseguramos de que no haya valores nulos para evitar errores
        cant = detalle.cantidad if detalle.cantidad else 0
        prec = detalle.precio_unitario if detalle.precio_unitario else 0
        nuevo_total += cant * prec
    
    # Guardamos el nuevo total en el Pedido
    pedido.total = nuevo_total
    pedido.save()

class Caja(models.Model):
    class Meta:
        managed = False  # No crea tabla en la base de datos
        verbose_name = "Cobros"
        verbose_name_plural = "Cobros"

# =========================================================
# 6. CONTROL DE CAJA (APERTURA Y CIERRE)
# =========================================================
class SesionCaja(models.Model):
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Inicial")
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Monto Cierre")
    estado = models.CharField(max_length=20, default='Abierta', choices=[('Abierta', 'Abierta'), ('Cerrada', 'Cerrada')])

    def __str__(self):
        return f"Caja {self.fecha_apertura.date()} - {self.usuario.username}"

    class Meta:
        verbose_name = "Sesión de Caja"
        verbose_name_plural = "Historial de Cajas"

# =========================================================
# 7. CONTROL DE GASTOS (NUEVO)
# =========================================================
class Gasto(models.Model):
    CATEGORIAS_GASTO = [
        ('Proveedores', 'Proveedores / Insumos'),
        ('Servicios', 'Servicios Básicos (Luz/Agua)'),
        ('Personal', 'Pagos a Personal'),
        ('Mantenimiento', 'Mantenimiento / Reparaciones'),
        ('Otro', 'Otros Gastos'),
    ]

    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    concepto = models.CharField(max_length=200, verbose_name="Descripción del Gasto")
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS_GASTO, default='Otro')
    fecha = models.DateTimeField(auto_now_add=True)
    comprobante = models.FileField(upload_to='gastos/', null=True, blank=True, verbose_name="Foto/Recibo (Opcional)")

    def __str__(self):
        return f"{self.concepto} - ${self.monto}"

    class Meta:
        verbose_name = "Gasto Operativo"
        verbose_name_plural = "Gastos Operativos"
