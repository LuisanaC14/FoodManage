/* =========================================================
   PARTE 1: EL BOTÓN ROJO DE "ELIMINAR SELECCIONADOS"
   ========================================================= */
document.addEventListener("DOMContentLoaded", function() {
    const actionsDiv = document.querySelector('div.actions');
    if (actionsDiv) {
        const select = actionsDiv.querySelector('select[name="action"]');
        const goButton = actionsDiv.querySelector('button[type="submit"]');
        
        if (select && goButton) {
            select.style.display = 'none';
            goButton.style.display = 'none';
            document.querySelectorAll('div.actions label').forEach(l => l.style.display = 'none');

            const newBtn = document.createElement('a');
            newBtn.className = 'btn-neon-delete'; 
            newBtn.href = '#';
            newBtn.innerHTML = '<i class="fas fa-trash-alt"></i> ELIMINAR SELECCIONADOS';

            actionsDiv.insertBefore(newBtn, actionsDiv.firstChild);

            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                select.value = 'delete_selected'; 
                goButton.click();
            });
        }
    }
});

/* =========================================================
   PARTE 2: BOTÓN DE BASURA PARA PLATOS (INLINES)
   ========================================================= */
(function($) {
    $(document).ready(function() {
        
        // --- FUNCIÓN: Convertir checkbox en botón ---
        function initDeleteButtons(row) {
            var deleteTd = row.find('td.delete');
            var checkbox = deleteTd.find('input[type="checkbox"]');

            if (checkbox.length && !deleteTd.find('.btn-trash-custom').length) {
                var btn = $('<a class="btn-trash-custom" title="Eliminar"><i class="fas fa-trash-alt"></i></a>');
                
                if (checkbox.is(':checked')) {
                    btn.addClass('active');
                    row.addClass('row-deleted');
                    row.find('td').not('.delete').css('text-decoration', 'line-through');
                }

                btn.click(function() {
                    var isChecked = !checkbox.is(':checked');
                    checkbox.prop('checked', isChecked);
                    
                    $(this).toggleClass('active', isChecked);
                    row.toggleClass('row-deleted', isChecked);
                    
                    if(isChecked) {
                        row.find('td').not('.delete').css('opacity', '0.5').css('text-decoration', 'line-through');
                    } else {
                        row.find('td').not('.delete').css('opacity', '1').css('text-decoration', 'none');
                    }
                });
                checkbox.after(btn);
            }
        }

        // 1. Aplicar a filas existentes al cargar
        $('tr.form-row').each(function() {
            initDeleteButtons($(this));
        });

        // 2. DETECTAR FILAS NUEVAS ("Agregar otro")
        $(document).on('formset:added', function(event, $row, formsetName) {
            
            // Buscamos el enlace de texto "Eliminar" de Django
            var removeLink = $row.find('a.inline-deletelink');
            
            if (removeLink.length) {
                // Le quitamos el texto por si acaso (aunque el CSS ya lo oculta)
                removeLink.html(''); 
                // Le agregamos la clase para asegurarnos
                removeLink.addClass('btn-trash-custom-link');
            }

            // Aplicamos lógica normal por si Django cambia y pone checkbox
            initDeleteButtons($row);
        });

    });
})(django.jQuery);

/* =========================================================
   PARTE 3: PLACEHOLDER PARA EL BUSCADOR DE ASISTENCIA
   ========================================================= */
document.addEventListener("DOMContentLoaded", function() {
    // Buscamos la caja de texto del buscador estándar de Django
    let searchInput = document.querySelector('#searchbar');
    if (searchInput) {
        searchInput.placeholder = "🔍 Buscar ";
        searchInput.style.textTransform = "uppercase"; // Opcional: Escribe en mayúsculas
    }
});
