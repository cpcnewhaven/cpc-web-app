// A shared, fixed-size media area for posters and announcements without artwork.
window.CPCAnnouncementMedia = {
  render(announcement) {
    const media = document.createElement('div');
    media.className = 'cpc-announcement-media';
    if (announcement.featuredImage) {
      const img = document.createElement('img');
      img.src = announcement.featuredImage;
      img.alt = ''; // The linked card supplies the title and accessible event details.
      img.loading = 'lazy';
      img.decoding = 'async';
      media.appendChild(img);
    } else {
      media.classList.add('cpc-announcement-media--text');
      media.setAttribute('aria-hidden', 'true');
      const brand = document.createElement('span');
      brand.className = 'cpc-announcement-media__brand';
      brand.textContent = 'CPC NEW HAVEN';
      const icon = document.createElement('i');
      const categories = {children:'fa-leaf', education:'fa-book-open', worship:'fa-church',
        fellowship:'fa-mug-hot', service:'fa-hands-helping', mercy:'fa-heart', general:'fa-bullhorn'};
      icon.className = 'fas ' + (categories[announcement.category] || 'fa-bullhorn');
      const label = document.createElement('span');
      label.className = 'cpc-announcement-media__label';
      const labels = {children:'Children & families', education:'Learning together', worship:'Worship together',
        fellowship:'Life together', service:'Serving our neighbors', mercy:'Caring for one another', general:'Church life'};
      label.textContent = labels[announcement.category] || 'Church life';
      media.append(brand, icon, label);
    }
    return media.outerHTML;
  }
};
