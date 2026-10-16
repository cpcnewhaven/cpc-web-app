(() => {
  const body = document.body;
  const csrf = body.dataset.csrf;
  const types = document.querySelector('#service-type');
  const plans = document.querySelector('#service-plan');
  const empty = document.querySelector('#empty-state');
  const editor = document.querySelector('#editor');
  const itemList = document.querySelector('#items');
  const notice = document.querySelector('#notice');
  let currentItems = [];

  const showNotice = (message, success = false) => {
    notice.textContent = message;
    notice.className = `notice ${success ? 'success-notice' : ''}`;
    notice.hidden = false;
  };
  const hideNotice = () => { notice.hidden = true; };
  async function getJson(url) {
    const response = await fetch(url, { credentials: 'same-origin' });
    const data = await response.json();
    if (!response.ok || data.error) throw new Error(data.error || 'Could not load Planning Center data.');
    return data;
  }

  document.querySelectorAll('[data-csrf-form]').forEach((button) => {
    const form = button.closest('form');
    const input = document.createElement('input');
    input.type = 'hidden'; input.name = 'csrf_token'; input.value = csrf;
    form.append(input);
    form.addEventListener('formdata', (event) => event.formData.append('csrf_token', csrf));
  });

  if (body.dataset.pco === '1') {
    getJson('/slides/api/service-types').then((rows) => {
      types.innerHTML = '<option value="">Choose a service type</option>';
      rows.forEach((row) => types.add(new Option(row.name, row.id)));
      if (!rows.length) showNotice('No Planning Center service types were found for this account.');
    }).catch((error) => showNotice(error.message));
  }

  types.addEventListener('change', async () => {
    hideNotice(); plans.disabled = true; plans.innerHTML = '<option>Loading plans…</option>';
    editor.hidden = true; empty.hidden = false;
    if (!types.value) { plans.innerHTML = '<option value="">Choose a service type first</option>'; return; }
    try {
      const rows = await getJson(`/slides/api/plans/${encodeURIComponent(types.value)}`);
      plans.innerHTML = '<option value="">Choose a service plan</option>';
      rows.forEach((row) => {
        const date = row.date ? ` · ${new Date(`${row.date}T12:00:00`).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'})}` : '';
        plans.add(new Option(row.title + date, row.id));
      });
      plans.disabled = false;
      if (!rows.length) { plans.innerHTML = '<option value="">No plans found</option>'; showNotice('No service plans were found for this service type.'); }
    } catch (error) { plans.innerHTML = '<option value="">Plans unavailable</option>'; showNotice(error.message); }
  });

  function renderItems(rows) {
    currentItems = rows.map((row) => ({ title: row.title || '', content: row.content || '' }));
    itemList.replaceChildren();
    currentItems.forEach((item, index) => {
      const card = document.createElement('article'); card.className = 'item-card';
      const number = document.createElement('div'); number.className = 'item-num'; number.textContent = String(index + 1).padStart(2, '0');
      const titleLabel = document.createElement('label');
      const titleCaption = document.createElement('span'); titleCaption.textContent = 'ITEM TITLE';
      const title = document.createElement('input'); title.value = item.title; title.maxLength = 300; title.addEventListener('input', () => { currentItems[index].title = title.value; });
      titleLabel.append(titleCaption, title);
      const contentLabel = document.createElement('label');
      const contentCaption = document.createElement('span'); contentCaption.textContent = 'SLIDE / DOCUMENT TEXT';
      const content = document.createElement('textarea'); content.value = item.content; content.rows = 3; content.maxLength = 10000; content.placeholder = 'Add or edit lyrics, readings, and service notes…'; content.addEventListener('input', () => { currentItems[index].content = content.value; });
      contentLabel.append(contentCaption, content); card.append(number, titleLabel, contentLabel); itemList.append(card);
    });
    document.querySelector('#item-count').textContent = currentItems.length;
    editor.hidden = false; empty.hidden = true;
  }

  plans.addEventListener('change', async () => {
    hideNotice();
    if (!plans.value) { editor.hidden = true; empty.hidden = false; return; }
    plans.disabled = true;
    try {
      const rows = await getJson(`/slides/api/plan/${encodeURIComponent(types.value)}/${encodeURIComponent(plans.value)}`);
      renderItems(rows);
      const planLabel = plans.options[plans.selectedIndex].text.split(' · ')[0];
      document.querySelector('#document-title').value = `Worship Service · ${planLabel}`;
      if (rows.some((item) => !item.content)) showNotice('Some Planning Center items have no text available. Add lyrics or reading text in the review fields before creating files.');
      else showNotice('Service plan loaded. Review and edit each item before creating your files.', true);
    } catch (error) { showNotice(error.message); }
    finally { plans.disabled = false; }
  });

  document.querySelector('#create-button').addEventListener('click', async (event) => {
    const button = event.currentTarget;
    const outputs = [];
    if (document.querySelector('#make-slides').checked) outputs.push('slides');
    if (document.querySelector('#make-doc').checked) outputs.push('doc');
    if (!outputs.length) { showNotice('Choose Google Slides, Google Docs, or both.'); return; }
    button.disabled = true; button.querySelector('span:first-child').textContent = 'Creating…'; hideNotice();
    try {
      const response = await fetch('/slides/api/create', {
        method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
        body: JSON.stringify({title: document.querySelector('#document-title').value, items: currentItems, outputs}),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not create Google files.');
      const links = document.querySelector('#created-links'); links.replaceChildren(); links.hidden = false;
      [['slides', 'Open Google Slides'], ['doc', 'Open Google Doc']].forEach(([key, label]) => {
        if (data.created[key]) { const link = document.createElement('a'); link.href = data.created[key].url; link.target = '_blank'; link.rel = 'noopener'; link.textContent = `${label} ↗`; links.append(link); }
      });
      showNotice('Your files are ready in Google Drive.', true);
    } catch (error) { showNotice(error.message); }
    finally { button.disabled = false; button.querySelector('span:first-child').textContent = 'Create files'; }
  });
})();
