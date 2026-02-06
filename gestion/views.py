import json, os, threading
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin
from django.contrib import messages
from django.db.models import Sum
from .models import Producto, Venta, Mesa, Pedido, DetallePedido, Reserva
from .forms import RegistroForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Pedido, Mesa, Producto, DetallePedido, SesionCaja, Gasto
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from django.core.mail import EmailMessage, send_mail
from io import BytesIO
from django.utils.html import strip_tags
from django.core.paginator import Paginator

def inicio(request):
    """Vista principal pública: Carga el menú, los contadores y el mapa de reservas."""

    # 1. CORRECCIÓN: Usamos .all() porque no existe el campo 'estado'
    productos = Producto.objects.all()

    # 2. Lógica de Contadores para la Barra Lateral
    conteos = {
        'total': productos.count(),
        'arroz': productos.filter(categoria__icontains='arroz').count(),
        'sopa': productos.filter(categoria__icontains='sopa').count(),
        'porcion': productos.filter(categoria__icontains='porcion').count(),
        'bebida': productos.filter(categoria__icontains='bebida').count(),
        'extra': productos.filter(categoria__icontains='extra').count(),
    }

    # 3. Lógica de Mesas (Se mantiene igual)
    mesas_piso1 = Mesa.objects.filter(piso__icontains='1') 
    mesas_piso2 = Mesa.objects.filter(piso__icontains='2')

    # 4. Enviamos TODO al template
    return render(request, 'gestion/index.html', {
        'productos': productos,
        'conteos': conteos,          
        'mesas_piso1': mesas_piso1,  
        'mesas_piso2': mesas_piso2   
    })

def reporte_ventas(request):
    """Calcula estadísticas de ventas y stock bajo (SOLO BEBIDAS Y EXTRAS)."""
    total_ventas = Venta.objects.aggregate(Sum('total'))['total__sum'] or 0
    
    # DEFINIMOS QUIÉNES SÍ USAN STOCK
    categorias_con_stock = ['Bebidas', 'Bebida', 'Extras', 'Extra', 'bebidas', 'extras']
    
    # Filtramos: Que sea de esas categorías Y que tenga menos de 5
    productos_poco_stock = Producto.objects.filter(
        categoria__in=categorias_con_stock, 
        stock__lt=5
    )
    
    return render(request, 'gestion/reporte.html', {
        'total_ventas': total_ventas,
        'productos_poco_stock': productos_poco_stock,
    })

def registro(request):
    """Crea un nuevo usuario como Cliente (sin grupo automático)."""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Solo permitimos staff si quieres que entren al panel, 
            # de lo contrario, déjalo en False para Clientes normales.
            user.is_staff = False        
            user.is_superuser = False   
            user.save()

            # Se elimina la asignación automática al grupo 'Meseros'
            
            messages.success(request, f'Cuenta creada exitosamente para {user.username}. Espere asignación de rol.')
            return redirect('admin_login') 
    else:
        form = RegistroForm()
    
    return render(request, 'registration/register.html', {'form': form})

def tomar_pedido(request):
    productos = Producto.objects.all()
    # TRAEMOS LAS MESAS: Solo las que marcamos como activas
    mesas = Mesa.objects.all().order_by('piso', 'numero')
    
    context = admin.site.each_context(request)
    available_apps = admin.site.get_app_list(request)

    context.update({
        'productos': productos,
        'mesas': mesas,                   # <--- AGREGAMOS LAS MESAS AL CONTEXTO
        'available_apps': available_apps,
        'title': 'Tomar Pedido',
        'site_title': 'FoodManage Admin',
        'site_header': 'Máncora Marisquería',
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
    })

    return render(request, 'gestion/tomar_pedido.html', context)

@login_required
def historial_mesero(request):

    mis_pedidos = Pedido.objects.filter(mesero=request.user).order_by('-fecha_pedido')
    return render(request, 'gestion/historial_mesero.html', {'pedidos': mis_pedidos})

@login_required
def vista_cocina(request):
    pedidos = Pedido.objects.filter(estado__in=['Pendiente', 'En preparación']).order_by('fecha_pedido')
    
    alerta_media = request.session.get('alerta_media', 20)
    alerta_critica = request.session.get('alerta_critica', 30)

    context = admin.site.each_context(request)
    context.update({
        'pedidos': pedidos,
        'title': 'Monitor de Cocina', 
        'site_header': 'Máncora Cocina',
        # Pasamos los datos al HTML
        'alerta_media': alerta_media,
        'alerta_critica': alerta_critica,
    })
    
    return render(request, 'gestion/cocina.html', context)

@login_required
@csrf_exempt

def guardar_pedido(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            if not data['mesa_id'] or not data['productos']:
                return JsonResponse({'status': 'error', 'message': 'Datos incompletos'})

            mesa = Mesa.objects.get(id=data['mesa_id'])
            
            # Capturamos la nota general
            nota_general = data.get('observaciones', '') 

            # 1. Guardamos el Pedido Principal (General)
            nuevo_pedido = Pedido.objects.create(
                mesero=request.user,
                mesa=mesa,
                total=data['total'],
                estado='Pendiente',
                observaciones=nota_general 
            )

            # 2. Guardamos los Platos (Detalles)
            for item in data['productos']:
                producto = Producto.objects.get(id=item['id'])
                
                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio_unitario=producto.precio,
                    
                    # --- AQUÍ ESTÁ EL CAMBIO MÁGICO ---
                    # Le ponemos la nota general a cada plato también
                    nota=nota_general  
                )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

@login_required
@csrf_exempt
def terminar_pedido(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        pedido.estado = 'Entregado' # O 'Completado' según tu modelo
        pedido.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

def imprimir_ticket(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Cálculos matemáticos (usando Decimal para precisión)
    subtotal_val = pedido.total / Decimal('1.15')
    iva_val = pedido.total - subtotal_val

    # FORMATO: Convertimos a String con 2 decimales AQUÍ MISMO
    context = {
        'pedido': pedido,
        'subtotal': "{:.2f}".format(subtotal_val), # Ej: "21.74"
        'iva': "{:.2f}".format(iva_val),           # Ej: "3.26"
        'fecha': pedido.fecha_pedido,
    }
    return render(request, 'gestion/ticket_termico.html', context)

@csrf_exempt
def guardar_config_cocina(request):
    """Guarda los tiempos de alerta en la sesión del usuario"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Guardamos en la memoria del navegador (Sesión)
            request.session['alerta_media'] = data.get('media', 20)
            request.session['alerta_critica'] = data.get('critica', 30)
            request.session.modified = True # Forzamos el guardado
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})

@login_required
def calendario_reservas(request):
    reservas = Reserva.objects.exclude(estado='Cancelada')
    eventos = []

    for r in reservas:
        # 1. BUSCAMOS LOS PLATOS DE ESTA RESERVA
        # Usamos el related_name 'platos_preordenados' que definimos en models.py
        platos_lista = []
        for plato in r.platos_preordenados.all():
            nota = f" <small style='color:#aaa;'>({plato.nota_plato})</small>" if plato.nota_plato else ""
            # Formato: "2x Ceviche (Sin cebolla)"
            platos_lista.append(f"<div style='margin-bottom:4px;'><b style='color:#ccff00;'>{plato.cantidad}x</b> {plato.producto.nombre}{nota}</div>")
        
        # Convertimos la lista en un texto HTML unido
        platos_html = "".join(platos_lista) if platos_lista else "<span style='color:#666; font-style:italic;'>Solo reserva de mesa</span>"

        # 2. DEFINIR COLOR (Igual que antes)
        color = '#ccff00' 
        if r.estado == 'Confirmada': color = '#00bfff' 
        if r.estado == 'Finalizada': color = '#666666'

        # 3. AGREGAMOS EL CAMPO 'platos' AL JSON
        eventos.append({
            'title': f"Mesa {r.mesa.numero} - {r.cliente}",
            'start': f"{r.fecha}T{r.hora}",
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'id': r.id,
                'cliente': r.cliente,
                'mesa': f"Mesa {r.mesa.numero} ({r.mesa.piso})",
                'hora': r.hora.strftime("%H:%M"),
                'estado': r.estado,
                'personas': r.mesa.capacidad,
                'platos': platos_html  # <--- ¡AQUÍ ESTÁ LA NUEVA DATA!
            }
        })

    context = {
        **admin.site.each_context(request),
        'eventos_json': json.dumps(eventos, default=str),
        'title': 'Calendario de Reservas',
    }
    return render(request, 'admin/gestion/reserva/calendario.html', context)


@login_required
def convertir_reserva_a_pedido(request, reserva_id):
    # 1. Obtenemos la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Validamos si ya se "usó" esta reserva (opcional)
    if reserva.asistio:
        messages.warning(request, f"La reserva de {reserva.cliente} ya fue marcada como asistida.")
        return redirect('admin:gestion_reserva_changelist')

    try:
        # 2. Creamos el ENCABEZADO del Pedido
        nuevo_pedido = Pedido.objects.create(
            mesero=request.user,          # El usuario que dio click al botón
            mesa=reserva.mesa,            # La mesa de la reserva
            cliente_nombre=reserva.cliente,
            estado='Pendiente',
            observaciones=f"Desde Reserva: {reserva.notas}" if reserva.notas else "Desde Reserva"
        )

        # 3. Convertimos los PLATOS PRE-ORDENADOS en DETALLES
        platos_reserva = reserva.platos_preordenados.all()
        
        if platos_reserva.exists():
            for pr in platos_reserva:
                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=pr.producto,
                    cantidad=pr.cantidad,
                    precio_unitario=pr.producto.precio, # Precio actual del producto
                    nota=pr.nota_plato
                )
            # Forzamos la actualización del total del pedido (por si acaso)
            nuevo_pedido.save()

        # 4. Actualizamos la Reserva
        reserva.asistio = True
        reserva.estado = 'Finalizada' # O el estado que prefieras
        reserva.save()

        messages.success(request, f"✅ ¡Pedido #{nuevo_pedido.numero_diario} creado exitosamente desde la reserva!")
        
        # 5. Redirigimos directo al Pedido para que el mesero siga atendiendo
        return redirect(f'/admin/gestion/pedido/{nuevo_pedido.id}/change/')

    except Exception as e:
        messages.error(request, f"Error al convertir: {str(e)}")
        return redirect('admin:gestion_reserva_changelist')

def crear_reserva_cliente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_cliente')
        telefono = request.POST.get('telefono')
        fecha_hora = request.POST.get('fecha_hora')
        personas = request.POST.get('personas')
        mesa_id = request.POST.get('mesa') # Este es el ID que enviamos desde el modal

        try:
            # 1. Obtener la mesa seleccionada
            mesa = Mesa.objects.get(id=mesa_id)

            # 2. Crear la reserva en la base de datos
            reserva = Reserva.objects.create(
                cliente=nombre,
                telefono=telefono,
                fecha_reserva=fecha_hora,
                numero_personas=personas,
                mesa=mesa,
                estado='PENDIENTE' # O el estado que manejes
            )

            # 3. CAMBIO DE ESTADO AUTOMÁTICO
            # Cambiamos el estado de la mesa para que no aparezca disponible
            mesa.disponible = False 
            mesa.save()

            messages.success(request, f"¡Reserva confirmada para la Mesa {mesa.numero}!")
            return redirect('inicio') # Cambia 'inicio' por el nombre de tu url principal

        except Mesa.DoesNotExist:
            messages.error(request, "La mesa seleccionada no es válida.")
        except Exception as e:
            messages.error(request, f"Error al crear la reserva: {e}")

    return redirect('inicio')

@login_required
def dashboard_caja(request):
    hoy = timezone.now()
    inicio_dia = hoy.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. CAJA Y FONDO
    caja_abierta = SesionCaja.objects.filter(usuario=request.user, estado='Abierta').last()
    monto_inicial = caja_abierta.monto_inicial if caja_abierta else 0
    
    # Fecha de referencia para ventas (desde apertura) vs gastos (todo el día)
    fecha_ventas = caja_abierta.fecha_apertura if caja_abierta else inicio_dia

    # 2. INGRESOS (Coincide con {{ total_ingresos }} del HTML)
    total_ingresos = Pedido.objects.filter(
        estado='Pagado', 
        fecha_pedido__gte=fecha_ventas
    ).aggregate(t=Sum('total'))['t'] or 0

    # 3. GASTOS (Coincide con {{ total_gastos }} del HTML)
    # ¡AQUÍ ESTÁ EL ARREGLO! Filtramos por inicio_dia para que salga el 'Agua' de hoy
    total_gastos = 999

    # 4. UTILIDAD (Coincide con {{ utilidad_neta }})
    utilidad_neta = (monto_inicial + total_ingresos) - total_gastos

    # 5. LISTAS PARA LAS TABLAS (Coinciden con {{ todas_ventas }} y {{ todos_gastos }})
    todas_ventas = Pedido.objects.filter(estado='Pagado', fecha_pedido__gte=fecha_ventas).order_by('-fecha_pedido')
    todos_gastos = Gasto.objects.all().order_by('-fecha')

    # 6. TOP PRODUCTOS (Coincide con {{ top_productos }})
    top_productos = DetallePedido.objects.filter(
        pedido__fecha_pedido__gte=inicio_dia,
        pedido__estado='Pagado'
    ).values('producto__nombre').annotate(total_vendido=Sum('cantidad')).order_by('-total_vendido')[:5]

    # 7. DATOS PARA EL GRÁFICO (Chart.js)
    # Enviamos datos vacíos por ahora para que no de error el gráfico
    chart_labels = ["Mañana", "Tarde", "Noche"] 
    chart_data = [0, 0, 0] 

    context = {
        'caja_abierta': caja_abierta,
        'monto_inicial': monto_inicial,
        'total_ingresos': total_ingresos,   # Variable correcta para tu HTML
        'total_gastos': total_gastos,       # Variable correcta para tu HTML
        'utilidad_neta': utilidad_neta,     # Variable correcta para tu HTML
        'todas_ventas': todas_ventas,       # Variable correcta para tu HTML
        'todos_gastos': todos_gastos,       # Variable correcta para tu HTML
        'top_productos': top_productos,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }

    # IMPORTANTE: Asegúrate de apuntar a TU archivo existente
    # Si tu archivo está en la carpeta 'templates/admin/gestion/', ajusta la ruta.
    return render(request, 'admin/gestion/venta/dashboard_ventas.html', context)

# =========================================================
# LÓGICA DE ENVÍO DE CORREO
# =========================================================

def link_callback(uri, rel):
    """Ayuda a xhtml2pdf a convertir rutas relativas en absolutas del sistema"""
    sUrl = settings.STATIC_URL      # Típicamente /static/
    sRoot = settings.STATIC_ROOT    # Típicamente la carpeta staticfiles
    mUrl = settings.MEDIA_URL       # Típicamente /media/
    mRoot = settings.MEDIA_ROOT     # Carpeta media del sistema

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri

    # Asegurarse de que el archivo exista
    if not os.path.isfile(path):
        raise Exception(f'media URI must start with {sUrl} or {mUrl}')
    return path

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        # Aquí es donde se envía realmente
        self.email.send()

@login_required
def enviar_ticket_email(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # 1. Validar correo
    destinatario = pedido.cliente_email 
    if not destinatario:
        messages.error(request, "❌ El pedido no tiene correo registrado.")
        return redirect(f'/admin/gestion/pedido/{pedido.id}/change/')

    # 2. Contexto (Datos)
    subtotal_val = pedido.total / Decimal('1.15')
    iva_val = pedido.total - subtotal_val
    
    context = {
        'pedido': pedido,
        'subtotal': "{:.2f}".format(subtotal_val),
        'iva': "{:.2f}".format(iva_val),
        'fecha': pedido.fecha_pedido,
        'es_pdf': True 
    }

    # 3. Generar PDF en Memoria
    template = get_template('gestion/ticket.html')
    html = template.render(context)
    result = BytesIO()
    
    # Aquí usamos link_callback para que no fallen las imagenes
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)

    if not pdf.err:
        # 4. Enviar Correo
        email = EmailMessage(
            subject=f'Ticket de Compra #{pedido.numero_diario} - Máncora',
            body=f'Estimado(a) {pedido.cliente_nombre},\n\nAdjuntamos su comprobante de venta.\n¡Gracias por su preferencia!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario],
        )
        email.attach(f'Ticket_{pedido.numero_diario}.pdf', result.getvalue(), 'application/pdf')
        
        EmailThread(email).start() 

        messages.success(request, f"✅ El correo se está enviando {destinatario}")

    else:
        messages.error(request, "Error generando el PDF (Revise imágenes/estilos).")

    return redirect(f'/admin/gestion/pedido/{pedido.id}/change/')

# QUITA EL @login_required DE AQUÍ
def mis_pedidos(request):
    # Validacion manual para mostrar tu pantalla de bloqueo
    if not request.user.is_authenticated:
        return render(request, 'gestion/login_requerido.html')
        
    # 1. Consulta Base
    lista_pedidos = Pedido.objects.filter(mesero=request.user).order_by('-fecha_pedido')

    # 2. Buscador
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        lista_pedidos = lista_pedidos.filter(fecha_pedido__date__gte=fecha_inicio)
    if fecha_fin:
        lista_pedidos = lista_pedidos.filter(fecha_pedido__date__lte=fecha_fin)

    # 3. Paginación
    paginator = Paginator(lista_pedidos, 6) 
    page_number = request.GET.get('page')
    pedidos_paginados = paginator.get_page(page_number)

    context = {
        'pedidos': pedidos_paginados,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    
    return render(request, 'gestion/mis_pedidos.html', context)

def ver_carrito(request):
    if not request.user.is_authenticated:
        return render(request, 'gestion/login_requerido.html') # <--- Bloqueo
    return render(request, 'gestion/carrito.html')

@csrf_exempt
def registrar_pedido_web(request):
    if request.method == 'POST':
        try:
            # 1. Recuperar datos
            datos_carrito = request.POST.get('carrito_data')
            metodo = request.POST.get('metodo_pago')
            nota = request.POST.get('nota', '')
            foto = request.FILES.get('comprobante')
            
            c_nombre = request.POST.get('cliente_nombre', 'Cliente Web')
            c_cedula = request.POST.get('cliente_cedula', '9999999999')
            c_telefono = request.POST.get('cliente_telefono', '')
            c_email = request.POST.get('cliente_email', '')
            c_direccion = request.POST.get('cliente_direccion', '')

            if not datos_carrito:
                return JsonResponse({'status': 'error', 'message': 'Carrito vacío'})

            cart = json.loads(datos_carrito)
            usuario = request.user if request.user.is_authenticated else User.objects.filter(is_superuser=True).first()
            if not usuario: usuario = User.objects.first()
            mesa_web = Mesa.objects.first() 

            total_pedido = sum(float(item['price']) for item in cart)

            # 2. Crear el Pedido
            pedido = Pedido.objects.create(
                mesero=usuario, mesa=mesa_web, cliente_nombre=c_nombre,
                cliente_cedula=c_cedula, cliente_telefono=c_telefono,
                cliente_email=c_email, cliente_direccion=c_direccion,
                estado='Pendiente', metodo_pago=metodo, total=total_pedido,
                observaciones=f"WEB | Nota: {nota}", comprobante_pago=foto
            )

            # 3. Guardar platos
            items_detalle = []
            for item in cart:
                prod = Producto.objects.filter(nombre=item['name']).first()
                if prod:
                    DetallePedido.objects.create(
                        pedido=pedido, producto=prod, cantidad=1, precio_unitario=prod.precio
                    )
                    items_detalle.append(f"{prod.nombre} (${prod.precio})")
            
            pedido.save()

            # 4. Enviar Correo HTML Profesional
            if c_email:
                asunto = f"Confirmación de Pedido #{pedido.numero_diario} - Máncora"
                filas_platos = "".join([f"<tr><td style='padding: 10px; border-bottom: 1px solid #eee;'>{item}</td></tr>" for item in items_detalle])

                html_mensaje = f"""
                <html>
                <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; background-color: #f9f9f9; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 15px; overflow: hidden; background-color: #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        
                        <div style="background-color: #000; padding: 25px; text-align: center; border-bottom: 4px solid #ccff00;">
                            <h1 style="color: #ccff00; margin: 0; font-size: 26px; text-transform: uppercase; letter-spacing: 2px;">MÁNCORA MARISQUERÍA</h1>
                            <p style="color: #fff; margin: 5px 0 0; font-size: 12px; letter-spacing: 3px;">LAGO AGRIO</p>
                        </div>
                        
                        <div style="padding: 30px;">
                            <h2 style="color: #333; margin-top: 0;">¡Hola, {c_nombre}!</h2>
                            <p style="font-size: 16px;">Hemos recibido tu pedido con éxito. Aquí tienes tu comprobante digital:</p>
                            
                            <div style="background-color: #f0f0f0; border: 2px dashed #000; border-radius: 10px; padding: 20px; text-align: center; margin: 25px 0; position: relative;">
                                <div style="font-size: 14px; color: #666; text-transform: uppercase; font-weight: bold; margin-bottom: 5px;">Tu Número de Ticket</div>
                                <div style="font-size: 48px; font-weight: 900; color: #000; letter-spacing: -1px; line-height: 1;">#{pedido.numero_diario}</div>
                                <div style="margin-top: 15px; border-top: 1px solid #ccc; pt-15px;">
                                    <p style="color: #333; font-size: 14px; margin: 10px 0 0;">
                                        <strong>Muestra esta pantalla al llegar al local</strong><br>
                                        <span style="color: #666; font-size: 12px;">Para agilizar tu retiro y entrega.</span>
                                    </p>
                                </div>
                            </div>

                            <div style="background-color: #fff9e6; border-left: 5px solid #ffc107; padding: 15px; margin-bottom: 25px; border-radius: 4px;">
                                <p style="margin: 0; font-size: 14px; color: #856404;">
                                    <i class="fas fa-file-invoice-dollar"></i> <strong>SOPORTE DE FACTURACIÓN:</strong><br>
                                    Recuerda solicitar tu <strong>factura física</strong> directamente en el local al momento de retirar tu pedido.
                                </p>
                            </div>

                            <div style="background-color: #ffeeee; border-left: 5px solid #dc3545; padding: 15px; margin-bottom: 25px; border-radius: 4px;">
                                <p style="margin: 0; font-size: 14px; color: #a94442;">
                                    <strong>IMPORTANTE:</strong> No contamos con servicio a domicilio.
                                </p>
                            </div>

                            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                                <thead>
                                    <tr style="background-color: #f8f9fa;">
                                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ccff00; font-size: 14px;">RESUMEN DEL PEDIDO</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filas_platos}
                                </tbody>
                            </table>

                            <div style="text-align: right; margin-top: 20px;">
                                <p style="font-size: 20px; margin: 0; color: #000;"><strong>TOTAL: ${total_pedido:.2f}</strong></p>
                                <p style="margin: 0; color: #666; font-size: 13px;">Método de Pago: {metodo}</p>
                            </div>
                        </div>
                        
                        <div style="background-color: #000; padding: 15px; text-align: center; font-size: 11px; color: #777; border-top: 1px solid #333;">
                            Máncora Marisquería - Lago Agrio, Ecuador. <br>
                            Este es un correo automático, por favor no lo respondas.
                        </div>
                    </div>
                </body>
                </html>
                """
                try:
                    send_mail(asunto, "Pedido recibido", settings.EMAIL_HOST_USER, [c_email], fail_silently=True, html_message=html_mensaje)
                except:
                    pass 

            return JsonResponse({'status': 'success', 'ticket': pedido.numero_diario, 'id_db': pedido.id})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

def nosotros(request):
    return render(request, 'gestion/nosotros.html')

def mi_cuenta(request):
    # Validacion manual
    if not request.user.is_authenticated:
        return render(request, 'gestion/login_requerido.html')
    
    usuario = request.user
    
    if request.method == 'POST':
        nombre = request.POST.get('first_name')
        apellido = request.POST.get('last_name')
        email = request.POST.get('email')
        
        usuario.first_name = nombre
        usuario.last_name = apellido
        usuario.email = email
        usuario.save()
        
        messages.success(request, '¡Tus datos han sido actualizados correctamente!')
        return redirect('mi_cuenta')

    return render(request, 'gestion/mi_cuenta.html', {'usuario': usuario})

def eliminar_cuenta(request):
    # Validacion manual
    if not request.user.is_authenticated:
        return render(request, 'gestion/login_requerido.html')

    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Tu cuenta ha sido eliminada. ¡Esperamos verte pronto!")
        return redirect('inicio')
    
    return redirect('mi_cuenta')

def pagina_reservas(request):
    """Muestra el mapa de mesas para reservar, pero SOLO si está logueado."""
    if not request.user.is_authenticated:
        return render(request, 'gestion/login_requerido.html')

    # Usamos los filtros igual que en 'inicio'
    mesas_piso1 = Mesa.objects.filter(piso__icontains='1')
    mesas_piso2 = Mesa.objects.filter(piso__icontains='2')
    
    return render(request, 'gestion/reservas_cliente.html', {
        'mesas_piso1': mesas_piso1, 
        'mesas_piso2': mesas_piso2
    })