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
    const response = await fetch('/api/events');
    const data = await response.json();

    // Extract unique categories from events
    const categories = new Set();
    (data.events || []).forEach(ev => {
      if (ev.category) categories.add(ev.category);
    });

    allCategories = Array.from(categories).sort();
    const select = document.getElementById('eventCategoryFilter');
    allCategories.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat;
      option.textContent = cat;
      select.appendChild(option);
    });
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
    // Fetch from /api/events (Google Calendar)
    const response = await fetch('/api/events');
    const data = await response.json();

    // Normalize Google Calendar events to search results format
    let events = (data.events || []).map(ev => ({
      id: ev.id,
      title: ev.title,
      date: ev.start,
      description: ev.description || '',
      category: ev.category || 'General',
      location: ev.location || '',
      url: ev.url || '',
      end: ev.end || '',
      imageUrl: ev.imageUrl || ev.image_url || ''
    }));

    // Apply filters
    if (currentEventQuery) {
      const q = currentEventQuery.toLowerCase();
      events = events.filter(e =>
        e.title.toLowerCase().includes(q) ||
        (e.description || '').toLowerCase().includes(q)
      );
    }

    if (currentEventCategory) {
      events = events.filter(e => e.category === currentEventCategory);
    }

    // Sort by date
    events.sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return dateA - dateB;
    });

    if (events && events.length > 0) {
      renderEventResults(events, listContainer);

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
  list.style.cssText = 'margin-top: 0.75rem;';
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
  function displayTag(cat) {
    if (!cat) return 'General';
    return String(cat)
      .replace(/[_-]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .split(' ')
      .map(word => word ? word.charAt(0).toUpperCase() + word.slice(1) : word)
      .join(' ');
  }
  function dateRange(ev) {
    const s = parseDate(ev.date);
    if (!s) return '';
    const opts = { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    return s.toLocaleString(undefined, opts);
  }
  function googleCalendarUrl(ev) {
    const start = parseDate(ev.date);
    if (!start) return null;

    const end = parseDate(ev.end) || new Date(start.getTime() + 60 * 60 * 1000);
    const formatDate = (date) => date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
    const details = [ev.description, ev.url ? `More information: ${ev.url}` : ''].filter(Boolean).join('\n\n');
    const params = new URLSearchParams({
      action: 'TEMPLATE',
      text: ev.title,
      dates: `${formatDate(start)}/${formatDate(end)}`,
      details,
      location: ev.location || ''
    });
    return `https://calendar.google.com/calendar/render?${params.toString()}`;
  }
  function formatEventDescription(description, eventId) {
    const text = String(description || '');
    const escaped = text.replace(/[&<>"']/g, (char) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[char]));
    const linkLabel = eventId === 'event_010' ? 'Sign up for Mercy Day' : 'Open link';
    return escaped.replace(/https?:\/\/[^\s<]+/g, (url) => (
      `<a href="${url}" target="_blank" rel="noopener">${linkLabel}</a>`
    ));
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

  const orderedKeys = Array.from(groups.keys()).sort();
  for (const key of orderedKeys) {
    const group = groups.get(key);
    const h = document.createElement('h3');
    h.className = 'evt-month';
    h.textContent = group.label;
    container.appendChild(h);

    for (const ev of group.items) {
      const card = document.createElement('article');
      const startDate = parseDate(ev.date);
      const hasImage = Boolean(ev.imageUrl);
      card.className = `evt-card ${hasImage ? 'evt-card--with-image' : 'evt-card--no-image'}`;
      const icsUrl = ev.id ? `/api/events/${ev.id}.ics` : null;
      const googleUrl = googleCalendarUrl(ev);
      const isOngoing = ev.source === 'ongoing';
      const dateTile = startDate ? `
        <div class="evt-card__date" aria-label="${dateRange(ev)}">
          <span class="evt-card__date-month">${startDate.toLocaleString(undefined, { month: 'short' })}</span>
          <strong class="evt-card__date-day">${startDate.getDate()}</strong>
        </div>` : '';

      card.innerHTML = `
        ${hasImage ? `<div class="evt-card__media"><img src="${ev.imageUrl}" alt="${ev.title}"></div>` : dateTile}
        <div class="evt-card__body">
        <div class="evt-head">
          <span class="evt-cat">${displayTag(ev.category)}</span>
          ${isOngoing ? '<span class="evt-cat" style="margin-left: 0.5rem; background: rgba(255, 196, 87, 0.16); color: #ffd98a;">Ongoing</span>' : ''}
          <h4 class="evt-title">${ev.title}</h4>
        </div>
        <div class="evt-meta">
          <span class="evt-when">${dateRange(ev)}</span>
        </div>
        ${ev.description ? `<p class="evt-desc">${formatEventDescription(ev.description, ev.id)}</p>` : ''}
        <div class="evt-actions evt-actions--calendar">
          <details class="evt-calendar-menu">
            <summary><i class="fas fa-calendar-plus" aria-hidden="true"></i> Add to Calendar <i class="fas fa-chevron-down" aria-hidden="true"></i></summary>
            <div class="evt-calendar-menu__panel">
              ${googleUrl ? `<a target="_blank" rel="noopener" href="${googleUrl}"><i class="fas fa-calendar-plus" aria-hidden="true"></i> Google Calendar</a>` : ''}
              ${icsUrl ? `<a href="${icsUrl}"><i class="fas fa-calendar-check" aria-hidden="true"></i> Apple Calendar / Outlook</a>` : ''}
              ${ev.url ? `<a target="_blank" rel="noopener" href="${ev.url}"><i class="fas fa-arrow-up-right-from-square" aria-hidden="true"></i> Event details</a>` : ''}
            </div>
          </details>
        </div>
        </div>
      `;
      container.appendChild(card);
    }
  }
}

document.addEventListener('DOMContentLoaded', loadEvents);
