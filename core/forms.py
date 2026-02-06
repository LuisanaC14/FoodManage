from django.contrib.auth.forms import AuthenticationForm

class LoginFormPersonalizado(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aquí sobrescribimos el mensaje de error "invalid_login"
        self.error_messages['invalid_login'] = 'Usuario o contraseña incorrectos. Vuelva a intentarlo.'