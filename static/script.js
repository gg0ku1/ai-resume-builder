/**
 * ResumeAI — script.js
 * Handles: form loading overlay, photo preview, custom sections,
 *          handler section toggles, AI apply buttons, template switcher.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ─── 1. Loading overlay on form submit ───────────────────────────────────
    const resumeForm = document.getElementById('resume-form');
    const loadingOverlay = document.getElementById('loading-overlay');

    if (resumeForm && loadingOverlay) {
        resumeForm.addEventListener('submit', function () {
            loadingOverlay.classList.add('active');
        });
    }

    // ─── 2. Profile photo preview (from CV builder) ──────────────────────────
    const photoInput = document.getElementById('profile_picture');
    const previewContainer = document.getElementById('photo-preview-container');

    if (photoInput && previewContainer) {
        photoInput.addEventListener('change', function () {
            // Remove existing preview
            previewContainer.innerHTML = '';

            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const wrapper = document.createElement('div');
                    wrapper.style.cssText = 'display:inline-flex;align-items:center;gap:12px;margin-top:10px;';

                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.alt = 'Preview';
                    img.style.cssText = 'width:72px;height:72px;border-radius:50%;object-fit:cover;border:2px solid var(--accent);';

                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.textContent = '✕ Remove';
                    removeBtn.style.cssText = 'background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.4);color:#fca5a5;border-radius:6px;padding:6px 12px;font-size:13px;cursor:pointer;';
                    removeBtn.addEventListener('click', function () {
                        photoInput.value = '';
                        previewContainer.innerHTML = '';
                    });

                    wrapper.appendChild(img);
                    wrapper.appendChild(removeBtn);
                    previewContainer.appendChild(wrapper);
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // ─── 3. Add Custom Section (from CV builder) ─────────────────────────────
    const addSectionBtn = document.getElementById('add-section-btn');
    const dynamicSectionsContainer = document.getElementById('dynamic-sections');

    if (addSectionBtn && dynamicSectionsContainer) {
        addSectionBtn.addEventListener('click', function () {
            const title = prompt('Enter section title (e.g., Certifications, Awards, Languages):');
            if (!title || !title.trim()) return;

            const sid = 'custom_' + Date.now();
            const safeTitle = title.trim().replace(/</g, '&lt;').replace(/>/g, '&gt;');

            const sectionHTML = `
<div class="form-section" id="${sid}" style="animation: fadeIn 0.3s ease;">
  <div class="form-section-title">
    <div class="section-icon teal"><i class="fas fa-plus"></i></div>
    ${safeTitle}
    <button type="button" onclick="removeSection('${sid}')"
      style="margin-left:auto;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);
             color:#fca5a5;border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;">
      <i class="fas fa-trash"></i> Remove
    </button>
  </div>
  <input type="hidden" name="dynamic_section_title_${sid}" value="${safeTitle}">
  <div class="form-group">
    <label for="ds_${sid}">${safeTitle} Details</label>
    <textarea id="ds_${sid}" name="dynamic_section_${sid}" rows="4"
      placeholder="Enter ${safeTitle} details here…"></textarea>
  </div>
</div>`;

            dynamicSectionsContainer.insertAdjacentHTML('beforeend', sectionHTML);

            // Scroll to the new section
            document.getElementById(sid)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    // ─── 4. Handler: section collapse / expand ────────────────────────────────
    // Already set up via inline onclick="toggleSection(id)" in handler.html
    // but we also auto-open all on page load (they're .open by default)

});

// ─── Global functions called from HTML ────────────────────────────────────────

/**
 * Toggle a section body open/closed on the handler page.
 * @param {string} bodyId - ID of the .section-body element
 */
function toggleSection(bodyId) {
    const body = document.getElementById(bodyId);
    if (!body) return;

    const isOpen = body.classList.contains('open');
    body.classList.toggle('open', !isOpen);

    // Flip the chevron icon
    const key = bodyId.replace('-body', '');
    const icon = document.getElementById('icon-' + key);
    if (icon) {
        icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
    }
}

/**
 * Copy AI suggestion text into the editable textarea.
 * @param {string} key - Section key (e.g., 'skills', 'experience')
 */
function applyAI(key) {
    const aiText = document.getElementById('ai-text-' + key);
    const field   = document.getElementById('field-' + key);

    if (aiText && field) {
        field.value = aiText.textContent.trim();

        // Visual feedback: flash the textarea green briefly
        field.style.transition = 'box-shadow 0.3s';
        field.style.boxShadow = '0 0 0 3px rgba(0,217,192,0.4)';
        setTimeout(() => { field.style.boxShadow = ''; }, 1200);
    }
}

/**
 * Switch the resume template by updating the class on #resume-doc.
 * @param {string} tpl - 'modern' | 'classic' | 'compact'
 * @param {HTMLElement} btn - The button that was clicked
 */
function setTemplate(tpl, btn) {
    const doc = document.getElementById('resume-doc');
    if (!doc) return;

    // Remove all tpl- classes
    doc.className = doc.className.replace(/tpl-\w+/g, '').trim();
    doc.classList.add('tpl-' + tpl);

    // Update active button
    document.querySelectorAll('.tpl-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
}

/**
 * Remove a dynamically-added custom section from the form.
 * @param {string} sid - Section DOM id
 */
function removeSection(sid) {
    const el = document.getElementById(sid);
    if (el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-10px)';
        el.style.transition = 'all 0.25s ease';
        setTimeout(() => el.remove(), 250);
    }
}

/**
 * Call /regenerate via AJAX and put the result into the AI output textarea.
 * @param {string} key - Section key (e.g. 'skills', 'experience')
 * @param {string} name - Candidate name
 */
async function regenerateSection(key, name) {
    const rawTextarea = document.getElementById('raw-' + key);
    const outputTextarea = document.getElementById('field-' + key);
    const btn = document.getElementById('regen-' + key);
    const status = document.getElementById('regen-status-' + key);

    if (!rawTextarea || !outputTextarea) return;

    const content = rawTextarea.value.trim();
    if (!content) {
        status.textContent = '⚠ Enter some content first.';
        return;
    }

    // Loading state
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…';
    status.textContent = '';

    try {
        const response = await fetch('/regenerate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, content, name })
        });

        if (!response.ok) throw new Error('Server error ' + response.status);

        const data = await response.json();

        outputTextarea.value = data.content;

        // Flash the output textarea green
        outputTextarea.style.transition = 'box-shadow 0.3s';
        outputTextarea.style.boxShadow = '0 0 0 3px rgba(0,217,192,0.5)';
        setTimeout(() => { outputTextarea.style.boxShadow = ''; }, 1500);

        status.style.color = 'var(--teal)';
        status.textContent = '✓ Regenerated!';
        setTimeout(() => { status.textContent = ''; }, 3000);

    } catch (err) {
        status.style.color = '#fca5a5';
        status.textContent = '✗ Failed: ' + err.message;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Regenerate AI';
    }
}

