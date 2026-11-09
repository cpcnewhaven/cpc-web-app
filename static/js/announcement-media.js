// A shared media area that renders artwork when present,
// and crafts an intentional typographic mini-poster / event ticket when absent.
window.CPCAnnouncementMedia = {
  render(announcement) {
    announcement = announcement || {};
    const media = document.createElement('div');
    media.className = 'cpc-announcement-media';

    // 1. Featured Image: when artwork exists, display the image cleanly
    if (announcement.featuredImage) {
      media.classList.add('cpc-announcement-media--image');
      const img = document.createElement('img');
      img.src = announcement.featuredImage;
      img.alt = ''; // Linked card supplies title and accessible details.
      img.loading = 'lazy';
      img.decoding = 'async';
      media.appendChild(img);
      return media.outerHTML;
    }

    // 2. No graphic: Render an intentional, crafted typographic mini-poster
    media.classList.add('cpc-announcement-media--poster');
    media.setAttribute('aria-hidden', 'true');

    // Date badge parsing
    let dateBadgeHtml = '';
    const dateVal = announcement.eventDate || announcement.date || announcement.startDate;
    if (dateVal) {
      try {
        const iso = typeof dateVal === 'string' && dateVal.length === 10 ? dateVal + 'T12:00:00' : dateVal;
        const d = new Date(iso);
        if (!isNaN(d.getTime())) {
          const monthShort = d.toLocaleString('en-US', { month: 'short' }).toUpperCase();
          const dayNum = d.getDate();
          const dayWeek = d.toLocaleString('en-US', { weekday: 'short' }).toUpperCase();
          dateBadgeHtml = `
            <div class="cpc-poster__date-badge">
              <span class="cpc-poster__date-month">${monthShort}</span>
              <span class="cpc-poster__date-day">${dayNum}</span>
              <span class="cpc-poster__date-dow">${dayWeek}</span>
            </div>`;
        }
      } catch (e) {}
    }

    if (!dateBadgeHtml) {
      dateBadgeHtml = `
        <div class="cpc-poster__date-badge cpc-poster__date-badge--ongoing">
          <span class="cpc-poster__date-month">CHURCH</span>
          <span class="cpc-poster__date-dow">LIFE</span>
        </div>`;
    }

    // Escape HTML in title
    const titleKey = (announcement.title || '').toLowerCase();
    const tone = /meal|thanksgiving|fellowship/.test(titleKey) ? 'gold' : /mercy|care|group|community/.test(titleKey) ? 'green' : 'blue';
    media.classList.add('cpc-announcement-media--' + tone);

    const rawTitle = (announcement.title || 'CPC New Haven').trim();
    const escapedTitle = rawTitle
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Dynamic title scale class
    let titleSizeClass = 'cpc-poster__title--md';
    if (rawTitle.length < 22) {
      titleSizeClass = 'cpc-poster__title--lg';
    } else if (rawTitle.length > 44) {
      titleSizeClass = 'cpc-poster__title--sm';
    }

    media.innerHTML = `
      <div class="cpc-poster__art" aria-hidden="true">
        <svg class="cpc-poster__art-svg" viewBox="0 0 240 280" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M120 20 C60 20 30 75 30 150 L30 280 L210 280 L210 150 C210 75 180 20 120 20 Z" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.32"/>
          <path d="M120 48 C75 48 50 92 50 150 L50 280 L190 280 L190 150 C190 92 165 48 120 48 Z" stroke="currentColor" stroke-width="1.2" opacity="0.22"/>
          <circle cx="120" cy="115" r="26" stroke="currentColor" stroke-width="1.2" opacity="0.28"/>
          <path d="M120 89 L120 141 M94 115 L146 115" stroke="currentColor" stroke-width="1.2" opacity="0.32"/>
        </svg>
      </div>
      <div class="cpc-poster__header">
        ${dateBadgeHtml}

      </div>
      <div class="cpc-poster__body">
        <div class="cpc-poster__title ${titleSizeClass}">${escapedTitle}</div>
      </div>
    `;

    return media.outerHTML;
  }
};
