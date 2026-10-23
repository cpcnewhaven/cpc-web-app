// Reuse the links in the published announcement instead of maintaining a second signup list.
window.CPCAnnouncementActions = {
  links(announcement) {
    const doc = new DOMParser().parseFromString(announcement.description || '', 'text/html');
    const title = (announcement.title || '').toLowerCase();
    const seen = new Set();
    return Array.from(doc.querySelectorAll('a[href]')).flatMap(anchor => {
      let url;
      try { url = new URL(anchor.getAttribute('href'), window.location.origin); } catch (_) { return []; }
      if (!['https:', 'http:', 'mailto:'].includes(url.protocol) || seen.has(url.href)) return [];
      seen.add(url.href);
      let label = anchor.textContent.trim() || 'Learn more';
      if (url.protocol === 'mailto:') label = /joining/.test(title) ? 'Begin membership' : 'Email CPC';
      else if (/fall festival/.test(title)) label = seen.size === 1 ? 'RSVP for Fall Festival' : 'Volunteer at Fall Festival';
      else if (/parenting/.test(title)) label = 'RSVP for Parenting Seminar';
      else if (/thanksgiving/.test(title)) label = 'Sign up as host or guest';
      else if (/care teams/.test(title)) label = 'Join a Care Team';
      return [{url: url.href, label}];
    });
  },
  append(container, announcement, className) {
    this.links(announcement).forEach(action => {
      const anchor = document.createElement('a');
      anchor.className = className || 'btn';
      anchor.href = action.url;
      anchor.textContent = action.label;
      container.appendChild(anchor);
    });
  }
};
