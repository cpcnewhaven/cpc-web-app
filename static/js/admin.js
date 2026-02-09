/**
 * CPC Admin – custom JS (no Bootstrap)
 * Navbar collapse + dropdown toggles.
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
    // Navbar toggle (mobile)
    var toggle = document.querySelector('.navbar-toggle[data-toggle="collapse"]');
    var targetId = toggle && toggle.getAttribute('data-target');
    var target = targetId ? document.querySelector(targetId) : null;
    if (toggle && target) {
      toggle.addEventListener('click', function () {
        target.classList.toggle('in');
      });
    }

    // Dropdown toggle (desktop + mobile)
    document.querySelectorAll('.dropdown-toggle').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var parent = btn.closest('.dropdown');
        if (!parent) return;
        var isOpen = parent.classList.contains('open');
        // Close all other dropdowns
        document.querySelectorAll('.navbar .dropdown.open').forEach(function (d) {
          if (d !== parent) d.classList.remove('open');
        });
        parent.classList.toggle('open', !isOpen);
      });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function () {
      document.querySelectorAll('.navbar .dropdown.open').forEach(function (d) {
        d.classList.remove('open');
      });
    });
  });
})();
