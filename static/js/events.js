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
    const data = await fetchUpcomingEvents();

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
    const data = await fetchUpcomingEvents();

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
      imageUrl: ev.imageUrl || ev.image_url || '',
      announcement: ev.announcement || null
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

async function fetchUpcomingEvents() {
  const results = await Promise.allSettled(['/api/events', '/api/event-announcements'].map(async url => {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Unable to load events');
    return response.json();
  }));
  if (results.every(result => result.status === 'rejected')) throw new Error('Unable to load events');
  const calendar = results[0].status === 'fulfilled' ? results[0].value.events || [] : [];
  const announcements = results[1].status === 'fulfilled' ? results[1].value.announcements || [] : [];
  const key = (title, day) => String(title || '').toLowerCase().replace(/[^a-z0-9]/g, '') + ':' + String(day || '').slice(0, 10);
  const announcementKeys = new Set(announcements.map(a => key(a.title, a.eventDate)));
  const events = calendar.filter(ev => !announcementKeys.has(key(ev.title, ev.start)));
  announcements.forEach(a => {
    const doc = new DOMParser().parseFromString(a.description || '', 'text/html');
    doc.querySelectorAll('p, br').forEach(el => el.appendChild(doc.createTextNode(' ')));
    events.push({id: a.id, title: a.title, start: a.eventDate, description: doc.body.textContent,
      category: a.category || 'General', imageUrl: a.featuredImage, announcement: a});
  });
  return {events};
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
  function parseDate(iso) { const d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso + 'T12:00:00' : iso); return isNaN(d.getTime()) ? null : d; }
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
    const opts = { weekday: 'short', month: 'short', day: 'numeric' };
    if (ev.announcement) {
      const a = ev.announcement;
      return s.toLocaleDateString(undefined, opts) + (a.eventStartTime ? ' • ' + a.eventStartTime : '') + (a.eventEndTime ? ' – ' + a.eventEndTime : '');
    }
    return s.toLocaleString(undefined, {...opts, hour: 'numeric', minute: '2-digit'});
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
          ${ev.announcement ? `<a class="btn" href="/announcement/${encodeURIComponent(ev.id)}">View details</a>` : `<details class="evt-calendar-menu">
            <summary><i class="fas fa-calendar-plus" aria-hidden="true"></i> Add to Calendar <i class="fas fa-chevron-down" aria-hidden="true"></i></summary>
            <div class="evt-calendar-menu__panel">
              ${googleUrl ? `<a target="_blank" rel="noopener" href="${googleUrl}"><i class="fas fa-calendar-plus" aria-hidden="true"></i> Google Calendar</a>` : ''}
              ${icsUrl ? `<a href="${icsUrl}"><i class="fas fa-calendar-check" aria-hidden="true"></i> Apple Calendar / Outlook</a>` : ''}
              ${ev.url ? `<a target="_blank" rel="noopener" href="${ev.url}"><i class="fas fa-arrow-up-right-from-square" aria-hidden="true"></i> Event details</a>` : ''}
            </div>
          </details>`}
        </div>
        </div>
      `;
      if (ev.announcement) CPCAnnouncementActions.append(card.querySelector('.evt-actions'), ev.announcement);
      container.appendChild(card);
    }
  }
}

document.addEventListener('DOMContentLoaded', loadEvents);
