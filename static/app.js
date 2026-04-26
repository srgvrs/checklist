(async function () {
  const PHASE_ID = window.PHASE_ID;
  let state = { tasks: [], hours: {}, library: [], pdf: null, pdf_name: null };
  let ready = false;

  // ── Cargar estado desde servidor ──────────────────────────
  try {
    const res = await fetch(`/api/state/${PHASE_ID}`);
    if (res.ok) {
      const data = await res.json();
      // Normalizar — asegurar que library siempre sea array
      state = {
        tasks:    Array.isArray(data.tasks)   ? data.tasks   : [],
        hours:    data.hours  && typeof data.hours  === 'object' ? data.hours  : {},
        library:  Array.isArray(data.library) ? data.library : [],
        pdf:      data.pdf      || null,
        pdf_name: data.pdf_name || null,
      };
    }
  } catch (e) {
    console.warn('[roadmap] No se pudo cargar estado del servidor:', e);
  }

  ready = true;

  // Aplicar estado cargado al DOM
  applyStateToDOM();

  // ── Guardar estado ────────────────────────────────────────
  async function saveState() {
    try {
      await fetch('/api/state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phaseId: PHASE_ID, data: state }),
      });
    } catch (e) {
      console.warn('[roadmap] Error al guardar estado:', e);
    }
  }

  // ── Aplicar estado al DOM tras carga ─────────────────────
  function applyStateToDOM() {
    // Checkboxes
    document.querySelectorAll('.week-check').forEach(cb => {
      const idx = parseInt(cb.dataset.weekIndex);
      cb.checked = !!state.tasks[idx];
      cb.closest('.week-card').classList.toggle('done', !!state.tasks[idx]);
    });

    // Horas
    document.querySelectorAll('.hours-input').forEach(inp => {
      const idx = inp.dataset.weekIndex;
      inp.value = state.hours[idx] || '';
    });

    // Biblioteca
    renderLibrary();
  }

  // ── Checkboxes ────────────────────────────────────────────
  document.querySelectorAll('.week-check').forEach(cb => {
    cb.addEventListener('change', async function () {
      const idx = parseInt(this.dataset.weekIndex);
      state.tasks[idx] = this.checked;
      this.closest('.week-card').classList.toggle('done', this.checked);
      await saveState();
    });
  });

  // ── Horas ─────────────────────────────────────────────────
  document.querySelectorAll('.hours-input').forEach(inp => {
    inp.addEventListener('change', async function () {
      state.hours[this.dataset.weekIndex] = this.value;
      await saveState();
    });
  });

  // ── Biblioteca ────────────────────────────────────────────
  function renderLibrary() {
    const list = document.getElementById('lib-list');
    const empty = document.getElementById('lib-empty');
    if (!list) return;

    if (!state.library.length) {
      list.innerHTML = '';
      if (empty) empty.classList.remove('hidden');
      return;
    }
    if (empty) empty.classList.add('hidden');

    list.innerHTML = state.library.map((link, i) => {
      // Sanitizar para evitar XSS básico
      const safeTitle = link.title.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const safeUrl   = link.url.startsWith('http') ? link.url : '#';
      return `<li>
        <a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${safeTitle}</a>
        <span class="delete-link" data-index="${i}" title="Eliminar">×</span>
      </li>`;
    }).join('');
  }

  // Botón agregar — FIX: ahora sí funciona correctamente
  const addBtn = document.getElementById('add-lib-btn');
  if (addBtn) {
    addBtn.addEventListener('click', async () => {
      const titleInput = document.getElementById('lib-title');
      const urlInput   = document.getElementById('lib-url');
      const title = titleInput ? titleInput.value.trim() : '';
      const url   = urlInput   ? urlInput.value.trim()   : '';

      if (!title || !url) {
        // Visual feedback si faltan campos
        if (!title && titleInput) titleInput.style.borderColor = 'var(--red)';
        if (!url   && urlInput)   urlInput.style.borderColor   = 'var(--red)';
        setTimeout(() => {
          if (titleInput) titleInput.style.borderColor = '';
          if (urlInput)   urlInput.style.borderColor   = '';
        }, 1500);
        return;
      }

      // Agregar protocolo si falta
      const fullUrl = url.startsWith('http') ? url : 'https://' + url;

      state.library.push({ title, url: fullUrl });
      await saveState();
      renderLibrary();

      if (titleInput) titleInput.value = '';
      if (urlInput)   urlInput.value   = '';
      titleInput && titleInput.focus();
    });

    // También agregar con Enter en el campo URL
    const urlInput = document.getElementById('lib-url');
    if (urlInput) {
      urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') addBtn.click();
      });
    }
  }

  // Borrar item de biblioteca (delegación de eventos)
  const libList = document.getElementById('lib-list');
  if (libList) {
    libList.addEventListener('click', async (e) => {
      if (e.target.classList.contains('delete-link')) {
        const idx = parseInt(e.target.dataset.index);
        if (!isNaN(idx)) {
          state.library.splice(idx, 1);
          await saveState();
          renderLibrary();
        }
      }
    });
  }

  // ── PDF ───────────────────────────────────────────────────
  const uploadInput = document.getElementById('pdf-upload-input');
  if (uploadInput) {
    uploadInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('pdf', file);
      try {
        const res  = await fetch(`/api/upload-pdf/${PHASE_ID}`, { method: 'POST', body: formData });
        const data = await res.json();
        state.pdf      = data.filename;
        state.pdf_name = data.pdf_name;
        await saveState();
        location.reload();
      } catch (e) {
        console.error('[roadmap] Error subiendo PDF:', e);
      }
    });
  }

  const renameBtn = document.getElementById('rename-pdf-btn');
  if (renameBtn) {
    renameBtn.addEventListener('click', async () => {
      const newName = prompt('Nuevo nombre:', state.pdf_name || state.pdf);
      if (!newName || !newName.trim()) return;
      await fetch(`/api/rename-pdf/${PHASE_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pdf_name: newName.trim() }),
      });
      state.pdf_name = newName.trim();
      const display = document.getElementById('pdf-name-display');
      if (display) display.textContent = state.pdf_name;
      await saveState();
    });
  }

  const replaceBtn = document.getElementById('replace-pdf-btn');
  if (replaceBtn) {
    replaceBtn.addEventListener('click', () => {
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
      if (!confirm('¿Eliminar el PDF permanentemente?')) return;
      await fetch(`/api/delete-pdf/${PHASE_ID}`, { method: 'POST' });
      state.pdf      = null;
      state.pdf_name = null;
      await saveState();
      location.reload();
    });
  }

  // ── Tema ──────────────────────────────────────────────────
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    const saved = localStorage.getItem('theme') || 'dark';
    document.body.classList.toggle('light', saved === 'light');
    updateThemeLabel();

    themeBtn.addEventListener('click', () => {
      const isLight = document.body.classList.toggle('light');
      localStorage.setItem('theme', isLight ? 'light' : 'dark');
      updateThemeLabel();
    });

    function updateThemeLabel() {
      const isLight = document.body.classList.contains('light');
      themeBtn.textContent = isLight ? 'dark' : 'light';
    }
  }
})();