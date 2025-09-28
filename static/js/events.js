async function loadEvents() {
  const r = await fetch('/api/events', { cache: 'no-store' });
  const data = await r.json();
  const root = document.getElementById('events-app');
  if (!root) return;
  if (data.error) { root.innerHTML = `<p class="err">${data.error}</p>`; return; }

  const events = data.events || [];
  if (!events.length) {
    root.innerHTML = `<p class="muted">No upcoming events at this time.</p>`;
    return;
  }

  // Build filter UI
  const cats = Array.from(new Set(events.map(e => e.category || "General")));
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

  function monthKey(iso){ const d=new Date(iso); return d.toLocaleString(undefined,{month:'long', year:'numeric'}); }
  function dateRange(ev){
    const s = new Date(ev.start);
    const e = ev.end ? new Date(ev.end) : null;
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
    // Group by month
    const groups = {};
    for (const ev of filtered){
      const key = monthKey(ev.start);
      (groups[key] ||= []).push(ev);
    }
    for (const [mon, arr] of Object.entries(groups)){
      const h = document.createElement('h3'); h.className='evt-month'; h.textContent = mon; list.appendChild(h);
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
