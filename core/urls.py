from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
# Importa tus vistas. Asegúrate de que 'registro' esté aquí.
from gestion.views import (inicio, reporte_ventas, registro, tomar_pedido, guardar_pedido, vista_cocina, terminar_pedido, 
imprimir_ticket, guardar_config_cocina, calendario_reservas, crear_reserva_cliente, pagina_reservas)
from .forms import LoginFormPersonalizado 
from gestion import views

urlpatterns = [
    path('admin/gestion/reserva/calendario/', calendario_reservas, name='calendario_reservas'),
    path('terminar_pedido/<int:pedido_id>/', terminar_pedido, name='terminar_pedido'),
    path('admin/gestion/cocina/', vista_cocina, name='vista_cocina'),
    # ==============================================================================
    # 1. LOGIN PERSONALIZADO
    # ==============================================================================
    path('admin/login/', auth_views.LoginView.as_view(
        template_name='admin/login.html',
        authentication_form=LoginFormPersonalizado
    ), name='admin_login'),

    # ==============================================================================
    # 2. RECUPERACIÓN DE CONTRASEÑA (Rutas limpias sin 'accounts/')
    # Estas rutas deben ir ANTES del admin y accounts para tener prioridad.
    # ==============================================================================
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), 
         name='password_reset'),
         
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), 
         name='password_reset_done'),

    # ESTA ES LA RUTA QUE FALLABA. Ahora está configurada correctamente.
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), 
         name='password_reset_confirm'),

    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), 
         name='password_reset_complete'),

    # ==============================================================================
    # 3. ADMINISTRACIÓN Y AUTENTICACIÓN
    # ==============================================================================
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    # ==============================================================================
    # 4. RUTAS DE LA APLICACIÓN (Aquí arreglamos el error del registro)
    # ==============================================================================
    path('', inicio, name='inicio'),
    path('reporte/', reporte_ventas, name='reporte_ventas'),
    path('pedido/', tomar_pedido, name='tomar_pedido'),
    path('guardar_pedido/', guardar_pedido, name='guardar_pedido'),
    path('imprimir-ticket/<int:pedido_id>/', imprimir_ticket, name='imprimir_ticket'),
    path('api/config-cocina/', guardar_config_cocina, name='guardar_config_cocina'),
    path('reservar/', crear_reserva_cliente, name='crear_reserva'),
    path('caja/', views.dashboard_caja, name='dashboard_caja'),
    path('enviar-email/<int:pedido_id>/', views.enviar_ticket_email, name='enviar_ticket_email'),
    path('reservar-mesa/', pagina_reservas, name='reserva_web'),
    path('historial-mesero/', views.historial_mesero, name='historial_mesero'),
    path('mi-pedido/', views.ver_carrito, name='ver_carrito'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('register/', registro, name='register'), 
    path('api/registrar-pedido/', views.registrar_pedido_web, name='registrar_pedido_web'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
    path('eliminar-cuenta/', views.eliminar_cuenta, name='eliminar_cuenta'),
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)