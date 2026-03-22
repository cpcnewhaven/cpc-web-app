/**
 * CPC Admin – custom JS (no Bootstrap)
 * Replaces Bootstrap's jQuery plugins with vanilla JS:
 *   - Navbar collapse (mobile hamburger)
 *   - Dropdown toggles
 *   - Modal show / hide  (Flask-Admin actions use jQuery .modal())
 *   - Tab switching
 */
(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  ready(function () {
    /* ---------------------------------------------------------------
       Navbar collapse (mobile)
       --------------------------------------------------------------- */
    var toggle = document.querySelector('.navbar-toggle[data-toggle="collapse"]');
    var targetId = toggle && toggle.getAttribute('data-target');
    var target = targetId ? document.querySelector(targetId) : null;
    if (toggle && target) {
      toggle.addEventListener('click', function () {
        target.classList.toggle('in');
      });
    }

    /* ---------------------------------------------------------------
       Dropdown toggle
       --------------------------------------------------------------- */
    document.querySelectorAll('.dropdown-toggle').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var parent = btn.closest('.dropdown');
        if (!parent) return;
        var isOpen = parent.classList.contains('open');
        document.querySelectorAll('.navbar .dropdown.open').forEach(function (d) {
          if (d !== parent) d.classList.remove('open');
        });
        parent.classList.toggle('open', !isOpen);
      });
    });

    document.addEventListener('click', function () {
      document.querySelectorAll('.navbar .dropdown.open').forEach(function (d) {
        d.classList.remove('open');
      });
    });

    /* ---------------------------------------------------------------
       Modal shim  –  Flask-Admin calls $(el).modal('show' | 'hide')
       This jQuery plugin replacement lets those calls work without
       Bootstrap JS.
       --------------------------------------------------------------- */
    if (window.jQuery) {
      jQuery.fn.modal = function (action) {
        return this.each(function () {
          var el = this;
          if (action === 'show') {
            el.style.display = 'flex';
            el.classList.add('in');
            // Add backdrop
            if (!document.getElementById('admin-modal-backdrop')) {
              var bd = document.createElement('div');
              bd.id = 'admin-modal-backdrop';
              bd.className = 'modal-backdrop';
              document.body.appendChild(bd);
            }
          } else if (action === 'hide') {
            el.style.display = 'none';
            el.classList.remove('in');
            var bd = document.getElementById('admin-modal-backdrop');
            if (bd) bd.remove();
          }
        });
      };
    }

    /* Also handle data-toggle="modal" clicks (static markup) */
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('[data-toggle="modal"]');
      if (!trigger) return;
      var sel = trigger.getAttribute('data-target') || trigger.getAttribute('href');
      var modal = sel ? document.querySelector(sel) : null;
      if (modal) {
        e.preventDefault();
        modal.style.display = 'flex';
        modal.classList.add('in');
        if (!document.getElementById('admin-modal-backdrop')) {
          var bd = document.createElement('div');
          bd.id = 'admin-modal-backdrop';
          bd.className = 'modal-backdrop';
          document.body.appendChild(bd);
        }
      }
    });

    /* Close modal on .close or backdrop click */
    document.addEventListener('click', function (e) {
      if (e.target.classList.contains('modal-backdrop') ||
          e.target.classList.contains('modal') ||
          e.target.closest('[data-dismiss="modal"]')) {
        document.querySelectorAll('.modal.in').forEach(function (m) {
          m.style.display = 'none';
          m.classList.remove('in');
        });
        var bd = document.getElementById('admin-modal-backdrop');
        if (bd) bd.remove();
      }
    });

    /* ---------------------------------------------------------------
       Tab switching  (nav-tabs)
       --------------------------------------------------------------- */
    document.querySelectorAll('[data-toggle="tab"]').forEach(function (tab) {
      tab.addEventListener('click', function (e) {
        e.preventDefault();
        var href = tab.getAttribute('href');
        var pane = href ? document.querySelector(href) : null;
        if (!pane) return;
        // Deactivate siblings
        var nav = tab.closest('ul');
        if (nav) nav.querySelectorAll('li').forEach(function (li) { li.classList.remove('active'); });
        tab.closest('li').classList.add('active');
        var content = pane.parentElement;
        if (content) content.querySelectorAll('.tab-pane').forEach(function (p) { p.classList.remove('active', 'in'); });
        pane.classList.add('active', 'in');
      });
    });
  });

  /* ---------------------------------------------------------------
     Smart custom scrollbar
     --------------------------------------------------------------- */
  (function () {
    // Only show when page is actually taller than the viewport
    function needsScrollbar() {
      return document.documentElement.scrollHeight > window.innerHeight + 4;
    }

    var rail, thumb, label;
    var isDragging = false;
    var dragStartY = 0;
    var dragStartScroll = 0;

    function buildScrollbar() {
      if (document.getElementById('admin-scroll-rail')) return;

      rail = document.createElement('div');
      rail.id = 'admin-scroll-rail';

      // Tick marks (every 10%)
      var ticks = document.createElement('div');
      ticks.id = 'admin-scroll-ticks';
      for (var i = 1; i < 10; i++) {
        var tick = document.createElement('div');
        tick.className = 'admin-scroll-tick';
        tick.style.top = (i * 10) + '%';
        ticks.appendChild(tick);
      }
      rail.appendChild(ticks);

      thumb = document.createElement('div');
      thumb.id = 'admin-scroll-thumb';
      rail.appendChild(thumb);

      label = document.createElement('div');
      label.id = 'admin-scroll-label';
      label.innerHTML = '<div class="scroll-label-main"></div><div class="scroll-label-sub"></div>';
      document.body.appendChild(label);
      document.body.appendChild(rail);

      rail.addEventListener('mousedown', onRailClick);
      thumb.addEventListener('mousedown', onThumbDragStart);
    }

    function removeScrollbar() {
      var r = document.getElementById('admin-scroll-rail');
      var l = document.getElementById('admin-scroll-label');
      if (r) r.remove();
      if (l) l.remove();
      rail = thumb = label = null;
    }

    function getScrollInfo() {
      var docH = document.documentElement.scrollHeight;
      var viewH = window.innerHeight;
      var scrollY = window.scrollY || window.pageYOffset;
      var maxScroll = docH - viewH;
      var pct = maxScroll > 0 ? scrollY / maxScroll : 0;
      return { docH: docH, viewH: viewH, scrollY: scrollY, maxScroll: maxScroll, pct: pct };
    }

    // Count visible table rows for context label
    function getRowContext(pct) {
      var rows = document.querySelectorAll('.table tbody tr');
      var total = rows.length;
      if (total === 0) {
        // Try to find pagination info for total
        var paginationInfo = document.querySelector('.pagination-page-size, .page-item.disabled span');
        return Math.round(pct * 100) + '%';
      }
      var idx = Math.max(1, Math.min(total, Math.round(pct * total) + 1));
      return 'row ' + idx + ' of ' + total;
    }

    function updateThumb() {
      if (!rail || !thumb) return;
      var info = getScrollInfo();
      var railH = rail.offsetHeight;
      var thumbH = Math.max(24, Math.round((info.viewH / info.docH) * railH));
      var thumbTop = Math.round(info.pct * (railH - thumbH));
      thumb.style.height = thumbH + 'px';
      thumb.style.top = thumbTop + 'px';
    }

    function showLabel(railY) {
      if (!label) return;
      var info = getScrollInfo();
      var labelMain = label.querySelector('.scroll-label-main');
      var labelSub = label.querySelector('.scroll-label-sub');
      labelMain.textContent = getRowContext(info.pct);
      labelSub.textContent = Math.round(info.pct * 100) + '% down';
      // Position label vertically near the thumb
      var railRect = rail.getBoundingClientRect();
      var posY = railRect.top + (railY != null ? railY : (rail.offsetHeight * info.pct));
      posY = Math.max(20, Math.min(window.innerHeight - 60, posY));
      label.style.top = posY + 'px';
      label.classList.add('is-visible');
    }

    function hideLabel() {
      if (label) label.classList.remove('is-visible');
    }

    // Click on the rail (not the thumb) — jump instantly
    function onRailClick(e) {
      if (e.target === thumb) return; // handled by drag
      var railRect = rail.getBoundingClientRect();
      var clickPct = (e.clientY - railRect.top) / rail.offsetHeight;
      clickPct = Math.max(0, Math.min(1, clickPct));
      var info = getScrollInfo();
      window.scrollTo({ top: Math.round(clickPct * info.maxScroll), behavior: 'auto' });
      showLabel(e.clientY - railRect.top);
    }

    // Drag start on thumb
    function onThumbDragStart(e) {
      e.preventDefault();
      e.stopPropagation();
      isDragging = true;
      dragStartY = e.clientY;
      dragStartScroll = window.scrollY || window.pageYOffset;
      rail.classList.add('is-dragging');
      document.addEventListener('mousemove', onThumbDrag);
      document.addEventListener('mouseup', onThumbDragEnd);
    }

    function onThumbDrag(e) {
      if (!isDragging) return;
      var dy = e.clientY - dragStartY;
      var info = getScrollInfo();
      var railH = rail.offsetHeight;
      var thumbH = thumb.offsetHeight;
      var ratio = info.maxScroll / (railH - thumbH);
      window.scrollTo({ top: Math.round(dragStartScroll + dy * ratio), behavior: 'auto' });
      var railRect = rail.getBoundingClientRect();
      showLabel(e.clientY - railRect.top);
    }

    function onThumbDragEnd() {
      isDragging = false;
      rail.classList.remove('is-dragging');
      document.removeEventListener('mousemove', onThumbDrag);
      document.removeEventListener('mouseup', onThumbDragEnd);
      hideLabel();
    }

    // Show label on rail hover
    function bindHoverLabel() {
      if (!rail) return;
      rail.addEventListener('mousemove', function (e) {
        if (!isDragging) {
          var railRect = rail.getBoundingClientRect();
          // Temporarily compute what position this hover represents
          var hoverPct = (e.clientY - railRect.top) / rail.offsetHeight;
          hoverPct = Math.max(0, Math.min(1, hoverPct));
          var info = getScrollInfo();
          var savedPct = info.pct;
          // Show label for hover position
          var labelMain = label.querySelector('.scroll-label-main');
          var labelSub = label.querySelector('.scroll-label-sub');
          labelMain.textContent = getRowContext(hoverPct);
          labelSub.textContent = Math.round(hoverPct * 100) + '% down';
          var posY = e.clientY;
          posY = Math.max(20, Math.min(window.innerHeight - 60, posY));
          label.style.top = posY + 'px';
          label.classList.add('is-visible');
        }
      });
      rail.addEventListener('mouseleave', function () {
        if (!isDragging) hideLabel();
      });
    }

    function init() {
      if (needsScrollbar()) {
        buildScrollbar();
        updateThumb();
        bindHoverLabel();
      } else {
        removeScrollbar();
      }
    }

    // Init after layout settles
    setTimeout(init, 150);

    window.addEventListener('scroll', function () {
      updateThumb();
    }, { passive: true });

    window.addEventListener('resize', function () {
      if (needsScrollbar()) {
        if (!document.getElementById('admin-scroll-rail')) {
          buildScrollbar();
          bindHoverLabel();
        }
        updateThumb();
      } else {
        removeScrollbar();
      }
    }, { passive: true });

  })();
})();
