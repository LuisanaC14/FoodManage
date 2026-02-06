(function() {
    const setupRegisterToggle = () => {
        // Seleccionamos los campos de contraseña y confirmación
        const passFields = document.querySelectorAll('input[type="password"]');
        
        passFields.forEach((input, index) => {
            // Evitamos duplicar el botón si ya existe
            const containerId = `toggle-reg-${index}`;
            if (!document.getElementById(containerId)) {
                
                // Estilizamos el botón para que encaje con tus iconos actuales
                const eyeHtml = `
                    <div class="input-group-append">
                        <div class="input-group-text" id="${containerId}" style="cursor: pointer; background: rgba(255,255,255,0.1); border-left: none; color: white;">
                            <i class="fas fa-eye"></i>
                        </div>
                    </div>
                `;
                
                input.insertAdjacentHTML('afterend', eyeHtml);

                const btn = document.getElementById(containerId);
                const icon = btn.querySelector('i');

                btn.addEventListener('click', () => {
                    if (input.type === "password") {
                        input.type = "text";
                        icon.classList.replace('fa-eye', 'fa-eye-slash');
                    } else {
                        input.type = "password";
                        icon.classList.replace('fa-eye-slash', 'fa-eye');
                    }
                });
            }
        });
    };

    document.addEventListener("DOMContentLoaded", setupRegisterToggle);
})();