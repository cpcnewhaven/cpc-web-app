async function loadEvents() {
  const r = await fetch('/api/events', { cache: 'no-store' });
  const data = await r.json();
  const root = document.getElementById('events-app');
  if (!root) return;
  if (data.error) { root.innerHTML = `<p class="err">${data.error}</p>`; return; }

  const events = (data.events || []).filter(e => e && e.start);
  if (!events.length) {
    root.innerHTML = `<p class="muted">No upcoming events at this time.</p>`;
    return;
  }

  // Build filter UI
  const cats = Array.from(new Set(events.map(e => (e.category || "General").trim() || "General")))
    .sort((a, b) => a.localeCompare(b));
  const controls = document.createElement('div');
  controls.className = 'evt-controls';
  controls.innerHTML = `
    <input id="evt-q" class="evt-input" placeholder="Search events…" />
    <div class="evt-chips">
      <button data-cat="All" class="chip active">All</button>
      ${cats.map(c => `<button data-cat="${c}" class="chip">${c}</button>`).join('')}
    </div>
  `;
  root.appendChild(controls);

  const list = document.createElement('div'); list.id = 'evt-list'; root.appendChild(list);

  function monthLabel(d){ return d.toLocaleString(undefined,{month:'long', year:'numeric'}); }
  function parseDate(iso){ const d = new Date(iso); return isNaN(d.getTime()) ? null : d; }
  function dateRange(ev){
    const s = parseDate(ev.start);
    const e = ev.end ? parseDate(ev.end) : null;
    if (!s) return '';
    const opts = {weekday:'short', month:'short', day:'numeric', hour:'numeric', minute:'2-digit'};
    const sTxt = s.toLocaleString(undefined, opts);
    if (ev.all_day) return s.toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'}) + ' (All day)';
    if (!e) return sTxt;
    const crossDay = s.toDateString() !== e.toDateString();
    const eTxt = e.toLocaleString(undefined, crossDay ? opts : {hour:'numeric',minute:'2-digit'});
    return crossDay ? `${sTxt} → ${eTxt}` : `${sTxt}–${eTxt}`;
  }
  function gmap(loc){ return loc ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc)}` : null; }

  function render(filterCat="All", query=""){
    list.innerHTML = '';
    const q = query.trim().toLowerCase();
    const filtered = events.filter(ev=>{
      const catOk = (filterCat==="All") || (ev.category===filterCat);
      const qOk = !q || `${ev.title} ${ev.description||''} ${ev.location||''}`.toLowerCase().includes(q);
      return catOk && qOk;
    });
    if (!filtered.length) {
      list.innerHTML = `<p class="muted" style="margin-top:0.75rem;">No matches. Try a different category or search.</p>`;
      return;
    }
    // Group by month
    const groups = new Map(); // key: "YYYY-MM" -> { label, items }
    for (const ev of filtered) {
      const s = parseDate(ev.start);
      if (!s) continue;
      const key = `${s.getFullYear()}-${String(s.getMonth()+1).padStart(2,'0')}`;
      if (!groups.has(key)) groups.set(key, { label: monthLabel(s), items: [] });
      groups.get(key).items.push(ev);
    }
    const orderedKeys = Array.from(groups.keys()).sort().reverse();
    for (const key of orderedKeys) {
      const group = groups.get(key);
      const arr = group.items.slice().sort((a,b)=> (a.start||'').localeCompare(b.start||'')); // within-month chronological
      const h = document.createElement('h3'); h.className='evt-month'; h.textContent = group.label; list.appendChild(h);
      for (const ev of arr){
        const card = document.createElement('article'); card.className='evt-card';
        const mapUrl = gmap(ev.location);
        const icsUrl = `/api/events/${ev.id}.ics`;
        card.innerHTML = `
          <div class="evt-head">
            <span class="evt-cat">${ev.category||'General'}</span>
            <h4 class="evt-title">${ev.title}</h4>
          </div>
          <div class="evt-meta">
            <span class="evt-when">${dateRange(ev)}</span>
            ${ev.location ? `<span class="evt-loc">• ${ev.location}</span>` : ''}
          </div>
          ${ev.description ? `<p class="evt-desc">${ev.description.slice(0,240)}${ev.description.length>240?'…':''}</p>` : ''}
          <div class="evt-actions">
            ${mapUrl ? `<a class="btn" target="_blank" rel="noopener" href="${mapUrl}">Map</a>` : ''}
            <a class="btn" href="${icsUrl}">Add to Calendar</a>
            ${ev.url ? `<a class="btn btn-alt" target="_blank" rel="noopener" href="${ev.url}">Details</a>` : ''}
          </div>
        `;
        list.appendChild(card);
      }
    }
  }

  // Wire filters
  controls.addEventListener('click', (e)=>{
    if (e.target.classList.contains('chip')){
      controls.querySelectorAll('.chip').forEach(b=>b.classList.remove('active'));
      e.target.classList.add('active');
      render(e.target.dataset.cat, document.getElementById('evt-q').value);
    }
  });
  controls.querySelector('#evt-q').addEventListener('input', (e)=>{
    const active = controls.querySelector('.chip.active')?.dataset.cat || "All";
    render(active, e.target.value);
  });

  render();
}
document.addEventListener('DOMContentLoaded', loadEvents);
