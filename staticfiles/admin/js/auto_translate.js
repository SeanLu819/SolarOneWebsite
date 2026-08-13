/**
 * Auto-translate button handler — vanilla JS, no jQuery dependency.
 * Buttons are rendered by TranslationsWidget in admin.py.
 */
(function () {
  'use strict';

  function init() {
    document.querySelectorAll('.auto-translate-btn').forEach(function (btn) {
      if (btn._autoTranslateBound) return;
      btn._autoTranslateBound = true;
      btn.addEventListener('click', function () {
        handleTranslateClick(btn);
      });
    });
  }

  function handleTranslateClick(btn) {
    var targetId = btn.getAttribute('data-target-id') || 'id_translations';
    var textarea = document.getElementById(targetId);
    if (!textarea) return;

    var status = btn.parentNode.querySelector('.auto-translate-status');
    setStatus(status, '', '#666');
    btn.disabled = true;
    btn.textContent = '⏳ Translating...';

    var isProject = !!document.getElementById('id_title');
    var isProduct = !!document.getElementById('id_name');

    var fields = {};

    if (isProject) {
      var title = val('id_title');
      var description = val('id_description');
      var location = val('id_location');
      var results = val('id_results');
      if (title) fields.title = title;
      if (description) fields.description = description;
      if (location) fields.location = location;
      if (results) fields.results = results;
    }

    if (isProduct) {
      var name = val('id_name');
      var pdescription = val('id_description');
      if (name) fields.name = name;
      if (pdescription) fields.description = pdescription;
    }

    if (Object.keys(fields).length === 0) {
      setStatus(status, 'No English content to translate.', '#c00');
      resetBtn(btn);
      return;
    }
    // Send single-language translation request to reduce multi-language limits
    var targetLang = btn.getAttribute('data-lang') || '';
    var payload = { fields: fields };
    if (targetLang) payload.target_lang = targetLang;

    var csrfToken = getCookie('csrftoken') || '';
    var url = window.location.origin + '/admin/translate/';

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return resp.json();
      })
      .then(function (data) {
        if (data.error) throw new Error(data.error);

        // Expect data.translations to be an object mapping lang -> { field: text }
        var lang = targetLang || Object.keys(data.translations || {})[0];
        if (!lang) throw new Error('No translation returned');

        var translated = data.translations[lang] || {};

        // Try to merge into existing JSON in the per-language textarea
        var existing = {};
        try {
          var raw = textarea.value.trim();
          if (raw) existing = JSON.parse(raw);
        } catch (e) { /* ignore */ }

        var merged = Object.assign({}, existing, translated);
        textarea.value = JSON.stringify(merged, null, 2);
        setStatus(status, '✓ Translation complete!', '#080');
        resetBtn(btn);
      })
      .catch(function (err) {
        setStatus(status, '✗ Error: ' + err.message, '#c00');
        resetBtn(btn);
      });
  }

  function val(id) {
    var el = document.getElementById(id);
    return el ? (el.value || '').trim() : '';
  }

  function setStatus(statusEl, msg, color) {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.style.color = color || '#666';
  }

  function resetBtn(btn) {
    btn.disabled = false;
    btn.textContent = '🔄 Auto-Translate Description';
  }

  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : '';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Also re-init on Django admin inline formsets (just in case)
  document.addEventListener('DOMNodeInserted', function (e) {
    if (e.target && e.target.classList && e.target.classList.contains('auto-translate-btn')) {
      init();
    }
  });
})();