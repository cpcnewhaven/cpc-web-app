/**
 * CPC New Haven - Smart Custom Scrollbar
 * Replicates the sophisticated scrollbar from the admin panel
 * for the main website.
 */
(function () {
    'use strict';

    // Only show when page is actually taller than the viewport
    function needsScrollbar() {
        return document.documentElement.scrollHeight > window.innerHeight + 4;
    }

    var rail, thumb, label;
    var isDragging = false;
    var dragStartY = 0;
    var dragStartScroll = 0;

    function buildScrollbar() {
        if (document.getElementById('cpc-scroll-rail')) return;

        rail = document.createElement('div');
        rail.id = 'cpc-scroll-rail';

        // Tick marks (every 10%)
        var ticks = document.createElement('div');
        ticks.id = 'cpc-scroll-ticks';
        for (var i = 1; i < 10; i++) {
            var tick = document.createElement('div');
            tick.className = 'cpc-scroll-tick';
            tick.style.top = (i * 10) + '%';
            ticks.appendChild(tick);
        }
        rail.appendChild(ticks);

        thumb = document.createElement('div');
        thumb.id = 'cpc-scroll-thumb';
        rail.appendChild(thumb);

        label = document.createElement('div');
        label.id = 'cpc-scroll-label';
        label.innerHTML = '<div class="scroll-label-main"></div><div class="scroll-label-sub"></div>';
        document.body.appendChild(label);
        document.body.appendChild(rail);

        rail.addEventListener('mousedown', onRailClick);
        thumb.addEventListener('mousedown', onThumbDragStart);
    }

    function removeScrollbar() {
        var r = document.getElementById('cpc-scroll-rail');
        var l = document.getElementById('cpc-scroll-label');
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

    // Context label
    function getContext(pct) {
        // Find if we are in a section with a heading
        var headings = document.querySelectorAll('h1, h2, .section-heading');
        var currentHeading = 'Overview';
        
        headings.forEach(function(h) {
            var rect = h.getBoundingClientRect();
            if (rect.top < window.innerHeight / 2) {
                currentHeading = h.textContent.trim();
            }
        });

        if (currentHeading.length > 25) currentHeading = currentHeading.substring(0, 22) + '...';
        
        return currentHeading;
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
        labelMain.textContent = getContext(info.pct);
        labelSub.textContent = Math.round(info.pct * 100) + '% down';
        
        // Position label vertically near the thumb/cursor
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
                var hoverPct = (e.clientY - railRect.top) / rail.offsetHeight;
                hoverPct = Math.max(0, Math.min(1, hoverPct));
                
                var labelMain = label.querySelector('.scroll-label-main');
                var labelSub = label.querySelector('.scroll-label-sub');
                labelMain.textContent = getContext(hoverPct);
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
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { setTimeout(init, 150); });
    } else {
        setTimeout(init, 150);
    }

    window.addEventListener('scroll', function () {
        updateThumb();
    }, { passive: true });

    window.addEventListener('resize', function () {
        if (needsScrollbar()) {
            if (!document.getElementById('cpc-scroll-rail')) {
                buildScrollbar();
                bindHoverLabel();
            }
            updateThumb();
        } else {
            removeScrollbar();
        }
    }, { passive: true });

})();
