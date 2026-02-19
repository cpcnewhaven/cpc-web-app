/**
 * Admin WYSIWYG – works in every scenario
 * - All forms with description or event_info get a rich editor + live preview
 * - Banner mode (banner=1) is skipped
 * - Quill load failure: form stays usable (no layout change, plain textarea)
 * - Multiple editors on one form (e.g. description + event_info) supported
 */
(function () {
  'use strict';

  var QUILL_CDN = 'https://cdn.quilljs.com/1.3.7/quill.min.js';
  var QUILL_CSS = 'https://cdn.quilljs.com/1.3.7/quill.snow.css';
  var QUILL_LOCAL = null; /* set window.ADMIN_QUILL_URL to use local copy, e.g. "/static/js/quill.min.js" */
  var LOAD_TIMEOUT_MS = 12000;
  var RICH_FIELDS = ['description', 'event_info'];

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  function getPreviewHtml(html) {
    if (!html || (html.trim() === '')) return '';
    var div = document.createElement('div');
    div.innerHTML = html;
    var allowed = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'ul', 'ol', 'li', 'h2', 'h3', 'blockquote'];
    var out = [];
    function walk(node) {
      if (node.nodeType === 1) {
        var tag = node.tagName.toLowerCase();
        if (allowed.indexOf(tag) !== -1) {
          var attrs = tag === 'a' && node.getAttribute('href')
            ? ' href="' + escapeHtml(node.getAttribute('href')) + '"' : '';
          out.push('<' + tag + attrs + '>');
          for (var i = 0; i < node.childNodes.length; i++) walk(node.childNodes[i]);
          out.push('</' + tag + '>');
        } else {
          for (var j = 0; j < node.childNodes.length; j++) walk(node.childNodes[j]);
        }
      } else if (node.nodeType === 3) {
        out.push(escapeHtml(node.textContent));
      }
    }
    walk(div);
    return out.join('');
  }

  function isEmptyHtml(html) {
    if (!html || !html.trim()) return true;
    var div = document.createElement('div');
    div.innerHTML = html;
    return !div.textContent || !div.textContent.trim();
  }

  ready(function () {
    var form = document.querySelector('form');
    if (!form) return;
    if (form.closest('.admin-form-with-preview')) return;
    var params = new URLSearchParams(window.location.search);
    if (params.get('banner') === '1') return;

    var textareas = [];
    RICH_FIELDS.forEach(function (name) {
      form.querySelectorAll('textarea[name="' + name + '"]').forEach(function (ta) {
        textareas.push({ name: name, el: ta });
      });
    });
    if (textareas.length === 0) return;

    var formParent = form.parentNode;
    var wrapper = document.createElement('div');
    wrapper.className = 'admin-form-with-preview';
    var formCol = document.createElement('div');
    formCol.className = 'admin-form-col';
    formCol.appendChild(form);

    var hasEventInfo = textareas.some(function (p) { return p.name === 'event_info'; });
    var previewHtml =
      '<h4>Live preview</h4>' +
      '<div class="admin-preview-card">' +
      '<div class="preview-title" id="admin-preview-title">Your title</div>' +
      '<div class="preview-meta" id="admin-preview-meta"></div>' +
      '<div class="preview-description" id="admin-preview-description">' +
      '<span class="admin-preview-placeholder">Content will appear here as you type.</span></div>';
    if (hasEventInfo) {
      previewHtml +=
        '<div class="preview-event-info-wrap" id="admin-preview-event-info-wrap" style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.08);">' +
        '<div class="preview-event-info-label" style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.5);margin-bottom:4px;">When / Where</div>' +
        '<div class="preview-description preview-event-info" id="admin-preview-event-info">' +
        '<span class="admin-preview-placeholder">When/where will appear here.</span></div></div>';
    }
    previewHtml += '</div>';

    var previewCol = document.createElement('div');
    previewCol.className = 'admin-preview-panel';
    previewCol.innerHTML = previewHtml;
    wrapper.appendChild(formCol);
    wrapper.appendChild(previewCol);
    formParent.appendChild(wrapper);

    var titleInput = form.querySelector('input[name="title"]');
    var typeSelect = form.querySelector('select[name="type"]');
    var categorySelect = form.querySelector('select[name="category"]');
    var tagInput = form.querySelector('input[name="tag"]');
    var seriesSelect = form.querySelector('select[name="series"]');
    var numberInput = form.querySelector('input[name="number"]');
    var previewTitleEl = document.getElementById('admin-preview-title');
    var previewMetaEl = document.getElementById('admin-preview-meta');
    var previewDescEl = document.getElementById('admin-preview-description');
    var previewEventWrap = document.getElementById('admin-preview-event-info-wrap');
    var previewEventEl = document.getElementById('admin-preview-event-info');

    var editors = [];

    function getSelectedLabel(select) {
      if (!select || !select.options) return '';
      var opt = select.options[select.selectedIndex];
      return opt ? opt.text : '';
    }

    function getFieldHtml(name) {
      for (var i = 0; i < editors.length; i++) {
        if (editors[i].name === name && editors[i].quill) return editors[i].quill.root.innerHTML;
      }
      var ta = form.querySelector('textarea[name="' + name + '"]');
      return ta ? ta.value : '';
    }

    function updatePreview() {
      if (!previewTitleEl) return;
      var title = (titleInput && titleInput.value) ? titleInput.value.trim() : 'Your title';
      previewTitleEl.textContent = title || 'Your title';

      var meta = [];
      if (typeSelect && typeSelect.value) meta.push(getSelectedLabel(typeSelect));
      if (categorySelect && categorySelect.value) meta.push(getSelectedLabel(categorySelect));
      if (tagInput && tagInput.value.trim()) meta.push(tagInput.value.trim());
      if (seriesSelect && seriesSelect.value) {
        meta.push(getSelectedLabel(seriesSelect));
      }
      if (numberInput && numberInput.value.trim()) meta.push('No. ' + numberInput.value.trim());
      if (meta.length && previewMetaEl) {
        previewMetaEl.innerHTML = meta.map(function (m) {
          return '<span class="preview-badge">' + escapeHtml(m) + '</span>';
        }).join('');
        previewMetaEl.style.display = '';
      } else if (previewMetaEl) {
        previewMetaEl.innerHTML = '';
        previewMetaEl.style.display = 'none';
      }

      var descHtml = getFieldHtml('description');
      if (previewDescEl) {
        if (descHtml && !isEmptyHtml(descHtml) && descHtml !== '<p><br></p>') {
          previewDescEl.innerHTML = getPreviewHtml(descHtml);
          previewDescEl.querySelectorAll('.admin-preview-placeholder').forEach(function (el) { el.remove(); });
        } else {
          previewDescEl.innerHTML = '<span class="admin-preview-placeholder">Content will appear here as you type.</span>';
        }
      }

      if (hasEventInfo && previewEventEl && previewEventWrap) {
        var eventHtml = getFieldHtml('event_info');
        if (eventHtml && !isEmptyHtml(eventHtml) && eventHtml !== '<p><br></p>') {
          previewEventEl.innerHTML = getPreviewHtml(eventHtml);
          previewEventEl.querySelectorAll('.admin-preview-placeholder').forEach(function (el) { el.remove(); });
          previewEventWrap.style.display = '';
        } else {
          previewEventEl.innerHTML = '<span class="admin-preview-placeholder">When/where will appear here.</span>';
          previewEventWrap.style.display = '';
        }
      }
    }

    function createOneEditor(entry) {
      var ta = entry.el;
      var initialHtml = ta.value || '';
      var wrap = document.createElement('div');
      wrap.className = 'admin-wysiwyg-wrap';
      if (entry.name === 'event_info') wrap.classList.add('admin-wysiwyg-event-info');
      ta.parentNode.insertBefore(wrap, ta);
      ta.style.display = 'none';

      var quill = new window.Quill(wrap, {
        theme: 'snow',
        modules: {
          toolbar: entry.name === 'event_info'
            ? [['bold', 'italic'], ['link'], [{ list: 'ordered' }, { list: 'bullet' }]]
            : [
                ['bold', 'italic', 'underline'],
                ['link', { list: 'ordered' }, { list: 'bullet' }],
                [{ header: [1, 2, 3] }],
                ['blockquote']
              ],
          clipboard: { matchVisual: false }
        }
      });
      if (initialHtml) quill.root.innerHTML = initialHtml;

      quill.on('text-change', function () {
        ta.value = quill.root.innerHTML;
        updatePreview();
      });
      editors.push({ name: entry.name, textarea: ta, quill: quill });
    }

    function createEditors() {
      if (!window.Quill) return;
      textareas.forEach(createOneEditor);
      if (titleInput) { titleInput.addEventListener('input', updatePreview); titleInput.addEventListener('change', updatePreview); }
      if (typeSelect) typeSelect.addEventListener('change', updatePreview);
      if (categorySelect) categorySelect.addEventListener('change', updatePreview);
      if (tagInput) tagInput.addEventListener('input', updatePreview);
      if (seriesSelect) seriesSelect.addEventListener('change', updatePreview);
      if (numberInput) numberInput.addEventListener('input', updatePreview);
      form.addEventListener('submit', function () {
        editors.forEach(function (e) { e.textarea.value = e.quill.root.innerHTML; });
      });
      updatePreview();
    }

    function fallback() {
      formParent.appendChild(form);
      wrapper.remove();
    }

    function tryLoadQuill() {
      if (window.Quill) {
        createEditors();
        return;
      }
      var timedOut = false;
      var done = false;
      var t = setTimeout(function () {
        timedOut = true;
        if (!done) { done = true; fallback(); }
      }, LOAD_TIMEOUT_MS);

      var baseUrl = typeof window.ADMIN_QUILL_BASE === 'string' ? window.ADMIN_QUILL_BASE.replace(/\/$/, '') : '';
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = baseUrl ? baseUrl + '/quill.snow.css' : QUILL_CSS;
      document.head.appendChild(link);
      var script = document.createElement('script');
      var scriptUrl = (typeof window.ADMIN_QUILL_URL === 'string' && window.ADMIN_QUILL_URL)
        ? window.ADMIN_QUILL_URL
        : QUILL_CDN;
      script.src = scriptUrl;
      script.onload = function () {
        if (timedOut) return;
        done = true;
        clearTimeout(t);
        createEditors();
      };
      script.onerror = function () {
        if (!done) { done = true; clearTimeout(t); fallback(); }
      };
      document.head.appendChild(script);
    }

    tryLoadQuill();
  });
})();
