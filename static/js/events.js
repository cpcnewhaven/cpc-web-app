// Phase 3: Events search with /api/search backend

let allCategories = [];
let currentEventPage = 1;
let currentEventQuery = '';
let currentEventCategory = '';
let eventSearchTimer;

async function loadEvents() {
  const root = document.getElementById('events-app');
  if (!root) return;

  // Load categories for dropdown
  await loadEventCategories();

  // Wire up filter controls
  setupEventFilters();

  // Initial load
  searchEvents();
}

async function loadEventCategories() {
  try {
    const response = await fetch('/api/search/meta?type=events');
    const data = await response.json();
    if (data.success && data.meta && data.meta.categories) {
      allCategories = data.meta.categories;
      const select = document.getElementById('eventCategoryFilter');
      allCategories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        select.appendChild(option);
      });
    }
  } catch (error) {
    console.error('Failed to load event categories:', error);
  }
}

function setupEventFilters() {
  const searchInput = document.getElementById('eventSearchInput');
  const filterToggle = document.getElementById('eventFilterToggle');
  const filterControls = document.querySelector('.events-section .mobile-collapsible');
  const categorySelect = document.getElementById('eventCategoryFilter');

  // Mobile filter toggle
  if (filterToggle) {
    filterToggle.addEventListener('click', () => {
      filterControls.classList.toggle('open');
      filterToggle.textContent = filterControls.classList.contains('open') ? 'Filters ▲' : 'Filters ▼';
    });
  }

  // Search input (debounced)
  searchInput.addEventListener('input', () => {
    clearTimeout(eventSearchTimer);
    eventSearchTimer = setTimeout(() => {
      currentEventQuery = searchInput.value;
      currentEventPage = 1;
      searchEvents();
    }, 250);
  });

  // Category filter (immediate)
  categorySelect.addEventListener('change', () => {
    currentEventCategory = categorySelect.value;
    currentEventPage = 1;
    searchEvents();
  });
}

async function searchEvents() {
  const root = document.getElementById('events-app');
  const listContainer = document.getElementById('evt-list') || createEventListContainer();

  listContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: rgba(255,255,255,0.6);">Loading events...</div>';

  try {
    let url = `/api/search?type=events&page=${currentEventPage}&per_page=15`;
    if (currentEventQuery) url += `&q=${encodeURIComponent(currentEventQuery)}`;
    if (currentEventCategory) url += `&category=${encodeURIComponent(currentEventCategory)}`;

    const response = await fetch(url);
    const data = await response.json();

    if (data.results && data.results.length > 0) {
      renderEventResults(data.results, listContainer);

      // Show/update pagination
      const paginationContainer = document.getElementById('eventPagination') || createPaginationContainer();
      if (data.pages > 1) {
        paginationContainer.style.display = 'flex';
        document.getElementById('eventPageInfo').textContent = `Page ${data.page} of ${data.pages}`;
        document.getElementById('prevEventBtn').disabled = data.page === 1;
        document.getElementById('nextEventBtn').disabled = data.page >= data.pages;
        document.getElementById('prevEventBtn').onclick = () => {
          currentEventPage = data.page - 1;
          searchEvents();
        };
        document.getElementById('nextEventBtn').onclick = () => {
          currentEventPage = data.page + 1;
          searchEvents();
        };
      } else {
        paginationContainer.style.display = 'none';
      }
    } else {
      listContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: rgba(255,255,255,0.6);">No events found. Try a different search.</div>';
      const paginationContainer = document.getElementById('eventPagination');
      if (paginationContainer) paginationContainer.style.display = 'none';
    }
  } catch (error) {
    console.error('Event search error:', error);
    listContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: rgba(255,100,100,0.9);">Search error. Please try again.</div>';
  }
}

function createEventListContainer() {
  const root = document.getElementById('events-app');
  const list = document.createElement('div');
  list.id = 'evt-list';
  list.style.cssText = 'max-height: 70vh; overflow-y: auto; overflow-x: hidden; padding-right: 0.5rem; margin-top: 0.75rem;';
  root.appendChild(list);
  return list;
}

function createPaginationContainer() {
  const root = document.getElementById('events-app');
  const pagination = document.createElement('div');
  pagination.id = 'eventPagination';
  pagination.style.cssText = 'display: flex; justify-content: center; align-items: center; gap: 1rem; margin-top: 2rem;';
  pagination.innerHTML = `
    <button id="prevEventBtn" style="padding: 0.5rem 1rem; background: rgba(0,82,163,0.3); border: 1px solid rgba(0,82,163,0.5); border-radius: 6px; color: white; cursor: pointer;">← Previous</button>
    <span id="eventPageInfo" style="color: rgba(255,255,255,0.7);">Page 1</span>
    <button id="nextEventBtn" style="padding: 0.5rem 1rem; background: rgba(0,82,163,0.3); border: 1px solid rgba(0,82,163,0.5); border-radius: 6px; color: white; cursor: pointer;">Next →</button>
  `;
  root.appendChild(pagination);
  return pagination;
}

function renderEventResults(events, container) {
  container.innerHTML = '';

  if (!events.length) {
    container.innerHTML = '<div style="padding: 2rem; text-align: center; color: rgba(255,255,255,0.6);">No events match your search.</div>';
    return;
  }

  // Helper functions
  function monthLabel(d) { return d.toLocaleString(undefined, { month: 'long', year: 'numeric' }); }
  function parseDate(iso) { const d = new Date(iso); return isNaN(d.getTime()) ? null : d; }
  function dateRange(ev) {
    const s = parseDate(ev.date);
    if (!s) return '';
    const opts = { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    return s.toLocaleString(undefined, opts);
  }
  function gmap(loc) { return loc ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc)}` : null; }

  // Group by month
  const groups = new Map();
  for (const ev of events) {
    const s = parseDate(ev.date);
    if (!s) continue;
    const key = `${s.getFullYear()}-${String(s.getMonth() + 1).padStart(2, '0')}`;
    if (!groups.has(key)) groups.set(key, { label: monthLabel(s), items: [] });
    groups.get(key).items.push(ev);
  }

  const orderedKeys = Array.from(groups.keys()).sort().reverse();
  for (const key of orderedKeys) {
    const group = groups.get(key);
    const h = document.createElement('h3');
    h.className = 'evt-month';
    h.textContent = group.label;
    container.appendChild(h);

    for (const ev of group.items) {
      const card = document.createElement('article');
      card.className = 'evt-card';
      const mapUrl = gmap(ev.category);
      const icsUrl = ev.id ? `/api/events/${ev.id}.ics` : null;

      card.innerHTML = `
        <div class="evt-head">
          <span class="evt-cat">${ev.category || 'General'}</span>
          <h4 class="evt-title">${ev.title}</h4>
        </div>
        <div class="evt-meta">
          <span class="evt-when">${dateRange(ev)}</span>
        </div>
        ${ev.description ? `<p class="evt-desc">${ev.description.slice(0, 240)}${ev.description.length > 240 ? '…' : ''}</p>` : ''}
        <div class="evt-actions">
          ${ev.url ? `<a class="btn" target="_blank" rel="noopener" href="${ev.url}">Details</a>` : ''}
        </div>
      `;
      container.appendChild(card);
    }
  }
}

document.addEventListener('DOMContentLoaded', loadEvents);
