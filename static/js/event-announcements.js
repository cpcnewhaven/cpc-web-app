// Display event announcements (from Announcement model with event_date) in 3-month calendar view

async function loadEventAnnouncements() {
  const container = document.getElementById('event-announcements-container');
  if (!container) return;

  try {
    const response = await fetch('/api/event-announcements');
    const data = await response.json();

    if (!data.announcements || data.announcements.length === 0) {
      container.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center; padding: 1rem;">No upcoming announcements.</p>';
      return;
    }

    renderEventAnnouncements(data.announcements, container);
  } catch (error) {
    console.error('Failed to load event announcements:', error);
    container.innerHTML = '<p style="color: rgba(255,100,100,0.8);">Error loading announcements.</p>';
  }
}

function renderEventAnnouncements(announcements, container) {
  container.innerHTML = '';

  // Helper functions
  function monthLabel(d) {
    return d.toLocaleString(undefined, { month: 'long', year: 'numeric' });
  }

  function parseDate(iso) {
    const d = new Date(iso + 'T00:00:00Z');
    return isNaN(d.getTime()) ? null : d;
  }

  function dateRange(ann) {
    const d = parseDate(ann.eventDate);
    if (!d) return '';
    const opts = { weekday: 'short', month: 'short', day: 'numeric' };
    let text = d.toLocaleString(undefined, opts);
    if (ann.eventStartTime) {
      text += ' • ' + ann.eventStartTime;
    }
    return text;
  }

  // Group by month
  const groups = new Map();
  for (const ann of announcements) {
    const d = parseDate(ann.eventDate);
    if (!d) continue;
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    if (!groups.has(key)) {
      groups.set(key, { label: monthLabel(d), items: [] });
    }
    groups.get(key).items.push(ann);
  }

  // Render groups
  const orderedKeys = Array.from(groups.keys()).sort();
  for (const key of orderedKeys) {
    const group = groups.get(key);
    const h = document.createElement('h3');
    h.className = 'evt-month';
    h.textContent = group.label;
    container.appendChild(h);

    for (const ann of group.items) {
      const card = document.createElement('article');
      card.className = 'evt-card announcement-card';

      card.innerHTML = `
        <div class="evt-head">
          <span class="evt-cat">${ann.category || 'Announcement'}</span>
          <h4 class="evt-title">${ann.title}</h4>
        </div>
        <div class="evt-meta">
          <span class="evt-when">${dateRange(ann)}</span>
        </div>
        ${ann.description ? `<p class="evt-desc">${ann.description.slice(0, 280)}${ann.description.length > 280 ? '…' : ''}</p>` : ''}
        ${ann.featuredImage ? `<img src="${ann.featuredImage}" alt="${ann.title}" style="margin-top: 0.75rem; border-radius: 8px; max-width: 100%; max-height: 200px; object-fit: cover;">` : ''}
        <div class="evt-actions">
          <a class="btn" href="/announcement/${ann.id}">Read More</a>
        </div>
      `;
      container.appendChild(card);
    }
  }
}

document.addEventListener('DOMContentLoaded', loadEventAnnouncements);
