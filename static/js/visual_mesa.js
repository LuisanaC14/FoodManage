document.addEventListener('DOMContentLoaded', function() {
    const selectField = document.getElementById('id_mesa');
    if (!selectField) return;

    // 1. Ocultar el selector feo de Django
    const formRow = selectField.closest('.form-row');
    if (formRow) formRow.style.display = 'none';

    // 2. Control de Pestañas (Pisos)
    const tabs = document.querySelectorAll('.floor-tab-btn');
    const maps = document.querySelectorAll('.floor-map');

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            tabs.forEach(t => t.classList.remove('active'));
            maps.forEach(m => m.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(tab.dataset.target).classList.add('active');
        });
    });

    // 3. Selección de Mesa
    const mesaSpots = document.querySelectorAll('.mesa-spot');

    mesaSpots.forEach(spot => {
        spot.addEventListener('click', function() {
            // Quitar selección previa
            mesaSpots.forEach(s => s.classList.remove('selected'));
            
            // Seleccionar actual
            this.classList.add('selected');

            // Actualizar valor oculto
            const mesaId = this.dataset.mesaId;
            selectField.value = mesaId;
        });
    });

    // 4. Cargar selección existente (si editamos una reserva)
    if (selectField.value) {
        const existing = document.querySelector(`.mesa-spot[data-mesa-id="${selectField.value}"]`);
        if (existing) {
            existing.classList.add('selected');
            // Abrir el piso correcto automáticamente
            const parentMap = existing.closest('.floor-map');
            const activeTab = document.querySelector(`.floor-tab-btn[data-target="${parentMap.id}"]`);
            if (activeTab) activeTab.click();
        }
    }
});