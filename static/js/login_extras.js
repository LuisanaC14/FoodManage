(function() {
    // ============================================================
    // PARTE 1: CORRECCIÓN DEL ERROR (TU SOLUCIÓN AGRESIVA)
    // ============================================================
    const corregirError = () => {
        const cajaError = document.querySelector('.callout-danger') || document.querySelector('.alert-danger') || document.querySelector('.errorlist');
        if (cajaError) {
            cajaError.style.display = 'block';
            cajaError.style.opacity = '1';
            
            if(cajaError.innerText.includes("correctos") || cajaError.innerHTML.includes("match")) {
                 cajaError.innerHTML = "<b>Credenciales incorrectas.</b><br>Inténtelo de nuevo.";
                 cajaError.style.textAlign = "center";
                 cajaError.style.background = "rgba(220, 20, 60, 0.9)";
                 cajaError.style.color = "white";
                 cajaError.style.border = "none";
            }
        }
    };

// ============================================================
    // 4. ¡SOLUCIÓN CRÍTICA! FORZAR CAJAS DE NUEVA CONTRASEÑA
    // ============================================================
    const forzarInputsPassword = () => {
        // Buscamos específicamente los campos de nueva contraseña
        const inputsReset = document.querySelectorAll('input[name="new_password1"], input[name="new_password2"]');
        
        inputsReset.forEach(input => {
            // 1. Obligamos al input a verse
            input.style.display = 'block';
            input.style.visibility = 'visible';
            input.style.opacity = '1';
            input.style.width = '100%';
            input.style.backgroundColor = '#2b3035';
            input.style.color = 'white';
            input.style.border = '1px solid #666';
            input.style.padding = '10px';
            input.style.borderRadius = '4px';
            input.style.marginBottom = '15px';

            // 2. ¡LO MÁS IMPORTANTE! Obligamos al PADRE (<p>) a verse
            // Si el padre estaba oculto por CSS, esto lo revive.
            if (input.parentElement) {
                input.parentElement.style.display = 'block';
                input.parentElement.style.visibility = 'visible';
                input.parentElement.style.opacity = '1';
                
                // Buscar el label hermano y pintarlo de blanco
                const label = input.parentElement.querySelector('label');
                if (label) {
                    label.style.display = 'block';
                    label.style.color = 'white';
                    label.style.textAlign = 'left';
                    label.style.marginBottom = '5px';
                }
            }
        });

        // 3. Forzar visibilidad de la lista de errores (si falló la contraseña)
        const errorList = document.querySelector('.errorlist');
        if (errorList) {
            errorList.style.display = 'block';
            errorList.style.color = '#ff6b6b';
            errorList.style.background = 'rgba(50,0,0,0.5)';
        }
    };

    // ============================================================
    // EJECUCIÓN MAESTRA
    // ============================================================
    const runAll = () => {
        corregirError();
        forzarInputsPassword(); // <--- Ejecutar la fuerza bruta
    };

    document.addEventListener("DOMContentLoaded", runAll);
    
    // Observer para vigilar cambios y volver a aplicar si algo desaparece
    const observer = new MutationObserver(() => runAll());
    observer.observe(document.body, { childList: true, subtree: true });
    
    setInterval(runAll, 500); // Re-chequeo cada 0.5s por seguridad
})();