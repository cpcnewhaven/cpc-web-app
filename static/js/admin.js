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
})();
