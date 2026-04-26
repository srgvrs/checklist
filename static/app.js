(async function() {
  const PHASE_ID = window.PHASE_ID;
  let state = window.initialState;

  // Sincronizar con el servidor al cargar
  try {
    const res = await fetch(`/api/state/${PHASE_ID}`);
    state = await res.json();
  } catch (e) {}

  // Función para guardar estado
  async function saveState() {
    await fetch('/api/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phaseId: PHASE_ID, data: state })
    });
  }

  // Checkboxes de semanas
  document.querySelectorAll('.week-check').forEach(cb => {
    cb.addEventListener('change', async function() {
      const idx = parseInt(this.dataset.weekIndex);
      state.tasks[idx] = this.checked;
      await saveState();
    });
  });

  // Horas
  document.querySelectorAll('.hours-input').forEach(inp => {
    inp.addEventListener('change', async function() {
      const idx = this.dataset.weekIndex;
      state.hours[idx] = this.value;
      await saveState();
    });
  });

  // Biblioteca
  const libList = document.getElementById('lib-list');
  document.getElementById('add-lib-btn').addEventListener('click', async () => {
    const title = document.getElementById('lib-title').value.trim();
    const url = document.getElementById('lib-url').value.trim();
    if (!title || !url) return;
    state.library.push({ title, url });
    await saveState();
    renderLibrary();
    document.getElementById('lib-title').value = '';
    document.getElementById('lib-url').value = '';
  });

  libList.addEventListener('click', async (e) => {
    if (e.target.classList.contains('delete-link')) {
      const idx = parseInt(e.target.dataset.index);
      state.library.splice(idx, 1);
      await saveState();
      renderLibrary();
    }
  });

  function renderLibrary() {
    libList.innerHTML = state.library.map((link, i) =>
      `<li><a href="${link.url}" target="_blank">${link.title}</a><span class="delete-link" data-index="${i}">×</span></li>`
    ).join('');
  }

  // PDF management
  const pdfSection = document.getElementById('pdf-section');
  const uploadInput = document.getElementById('pdf-upload-input');
  if (uploadInput) {
    uploadInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('pdf', file);
      const res = await fetch(`/api/upload-pdf/${PHASE_ID}`, { method: 'POST', body: formData });
      const data = await res.json();
      state.pdf = data.filename;
      state.pdf_name = data.pdf_name;
      await saveState();
      location.reload();
    });
  }

  // Botones de PDF existentes
  const renameBtn = document.getElementById('rename-pdf-btn');
  if (renameBtn) {
    renameBtn.addEventListener('click', async () => {
      const newName = prompt('Nuevo nombre para el PDF:', state.pdf_name || state.pdf);
      if (newName !== null && newName.trim() !== '') {
        await fetch(`/api/rename-pdf/${PHASE_ID}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pdf_name: newName.trim() })
        });
        state.pdf_name = newName.trim();
        document.getElementById('pdf-name-display').textContent = state.pdf_name;
        await saveState();
      }
    });
  }

  const replaceBtn = document.getElementById('replace-pdf-btn');
  if (replaceBtn) {
    replaceBtn.addEventListener('click', () => {
      // Crear input oculto para seleccionar nuevo PDF
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.pdf';
      input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('pdf', file);
        await fetch(`/api/upload-pdf/${PHASE_ID}`, { method: 'POST', body: formData });
        location.reload();
      };
      input.click();
    });
  }

  const deleteBtn = document.getElementById('delete-pdf-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      if (confirm('¿Eliminar el PDF permanentemente?')) {
        await fetch(`/api/delete-pdf/${PHASE_ID}`, { method: 'POST' });
        state.pdf = null;
        state.pdf_name = null;
        await saveState();
        location.reload();
      }
    });
  }

  // Aplicar modo terminal si se desea (opcional, se puede activar añadiendo ?terminal=1)
  if (new URLSearchParams(window.location.search).has('terminal')) {
    document.body.classList.add('terminal');
  }
})();