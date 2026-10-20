(() => {
  const body = document.body;
  const csrf = body.dataset.csrf;
  const isPco = body.dataset.pco === '1';
  const isGoogle = body.dataset.google === '1';

  // Wizard state
  let currentStep = 1;
  const wizardSteps = document.querySelectorAll('.wizard-step');
  const wizardPanels = {
    1: document.querySelector('#step-panel-1'),
    2: document.querySelector('#step-panel-2'),
    3: document.querySelector('#step-panel-3'),
    4: document.querySelector('#step-panel-4'),
  };

  // Tabs within Step 1
  const tabs = document.querySelectorAll('.source-tab');
  const panels = {
    bulletin: document.querySelector('#tab-bulletin'),
    'planning-center': document.querySelector('#tab-planning-center'),
    combine: document.querySelector('#tab-combine'),
  };

  // Bulletin inputs
  const bulletinUrlInput = document.querySelector('#bulletin-url');
  const fetchBulletinBtn = document.querySelector('#fetch-bulletin-btn');
  const togglePasteBtn = document.querySelector('#toggle-paste-btn');
  const pasteBox = document.querySelector('#paste-box');
  const pasteTextarea = document.querySelector('#bulletin-paste-text');
  const parsePastedBtn = document.querySelector('#parse-pasted-btn');

  // Planning Center inputs
  const types = document.querySelector('#service-type');
  const plans = document.querySelector('#service-plan');
  const combineTypes = document.querySelector('#combine-service-type');
  const combinePlans = document.querySelector('#combine-service-plan');
  const combineBtn = document.querySelector('#combine-btn');
  const combineBulletinUrl = document.querySelector('#combine-bulletin-url');

  // Template inputs
  const templateUrlInput = document.querySelector('#template-url');
  const previewTemplateLink = document.querySelector('#preview-template-link');

  // Step 2 Review elements
  const itemList = document.querySelector('#items');
  const notice = document.querySelector('#notice');
  const docTitleInput = document.querySelector('#document-title');
  const itemCountEl = document.querySelector('#item-count');
  const slideCountEl = document.querySelector('#slide-count');
  const addItemBtn = document.querySelector('#add-item-btn');
  const pipeBanner = document.querySelector('#pipe-banner');

  // Step 3 Slide Preview elements
  const slidesPreviewGrid = document.querySelector('#slides-preview-grid');
  const previewTotalSlidesEl = document.querySelector('#preview-total-slides');

  // Step 4 Publish elements
  const publishSummaryTitle = document.querySelector('#publish-summary-title');
  const publishSummaryDesc = document.querySelector('#publish-summary-desc');
  const publishTemplateLabel = document.querySelector('#publish-template-label');
  const createBtn = document.querySelector('#create-button');
  const publishProgress = document.querySelector('#publish-progress');
  const publishProgressText = document.querySelector('#publish-progress-text');
  const createdLinks = document.querySelector('#created-links');

  let currentItems = [];

  const showNotice = (message, success = false) => {
    notice.textContent = message;
    notice.className = `notice ${success ? 'success-notice' : ''}`;
    notice.hidden = false;
  };
  const hideNotice = () => { notice.hidden = true; };

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || data.error) {
      throw new Error(data.error || 'Server returned an error.');
    }
    return data;
  }

  async function getJson(url) {
    const response = await fetch(url, { credentials: 'same-origin' });
    const data = await response.json();
    if (!response.ok || data.error) throw new Error(data.error || 'Could not load information.');
    return data;
  }

  // Setup CSRF forms for disconnect buttons
  document.querySelectorAll('[data-csrf-form]').forEach((button) => {
    const form = button.closest('form');
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'csrf_token';
    input.value = csrf;
    form.append(input);
    form.addEventListener('formdata', (event) => event.formData.append('csrf_token', csrf));
  });

  // Wizard Step Transition
  function goToStep(step) {
    if (step > 1 && !currentItems.length) {
      showNotice('Please import a bulletin or Planning Center plan first.');
      return;
    }
    currentStep = step;
    hideNotice();

    // Update stepper navigation
    wizardSteps.forEach((s) => {
      const sNum = parseInt(s.dataset.step, 10);
      s.classList.remove('active', 'completed');
      if (sNum === step) s.classList.add('active');
      else if (sNum < step) s.classList.add('completed');
    });

    // Update panels
    Object.entries(wizardPanels).forEach(([num, panel]) => {
      if (panel) panel.hidden = parseInt(num, 10) !== step;
    });

    // Specific panel actions
    if (step === 3) {
      renderSlideCardsPreview();
    } else if (step === 4) {
      updatePublishCard();
    }

    window.scrollTo({ top: 120, behavior: 'smooth' });
  }

  // Stepper click handlers
  wizardSteps.forEach((s) => {
    s.addEventListener('click', () => {
      const targetStep = parseInt(s.dataset.step, 10);
      goToStep(targetStep);
    });
  });

  // Navigation button handlers
  document.querySelectorAll('[data-goto-step]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = parseInt(btn.dataset.gotoStep, 10);
      goToStep(target);
    });
  });

  // Tab switching in Step 1
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const tabKey = tab.dataset.tab;
      Object.entries(panels).forEach(([key, panel]) => {
        if (panel) panel.hidden = key !== tabKey;
      });
      hideNotice();
    });
  });

  // Toggle paste box
  if (togglePasteBtn) {
    togglePasteBtn.addEventListener('click', () => {
      pasteBox.hidden = !pasteBox.hidden;
      if (!pasteBox.hidden) pasteTextarea.focus();
    });
  }

  // Update template preview link when URL changes
  if (templateUrlInput && previewTemplateLink) {
    templateUrlInput.addEventListener('input', () => {
      previewTemplateLink.href = templateUrlInput.value || '#';
    });
  }

  // Helper: flatten items into discrete slide objects
  function getAllSlideObjects() {
    const slides = [];
    currentItems.forEach((item) => {
      if (item.slides && item.slides.length) {
        item.slides.forEach((s) => {
          slides.push({
            title: s.title || item.title,
            content: s.content || '',
            category: item.category || 'liturgy',
          });
        });
      } else {
        const lines = (item.content || '').split('\n').filter((l) => l.trim().length > 0);
        const chunkSize = 5;
        if (!lines.length) {
          slides.push({ title: item.title, content: '', category: item.category });
        } else {
          for (let i = 0; i < lines.length; i += chunkSize) {
            slides.push({
              title: item.title,
              content: lines.slice(i, i + chunkSize).join('\n'),
              category: item.category,
            });
          }
        }
      }
    });
    return slides;
  }

  function calculateTotalSlides() {
    return getAllSlideObjects().length;
  }

  function updateSummary() {
    const totalSlides = calculateTotalSlides();
    if (itemCountEl) itemCountEl.textContent = currentItems.length;
    if (slideCountEl) slideCountEl.textContent = totalSlides;
    if (previewTotalSlidesEl) previewTotalSlidesEl.textContent = totalSlides;
  }

  // Step 2: Render Items list in Review Editor
  function renderItems(rows, titleText = '') {
    currentItems = rows.map((row) => ({
      title: row.title || '',
      content: row.content || '',
      category: row.category || 'liturgy',
      slides: row.slides || null,
      pco_synced: !!row.pco_synced,
    }));

    itemList.replaceChildren();

    currentItems.forEach((item, index) => {
      const card = document.createElement('article');
      card.className = 'item-card';

      const number = document.createElement('div');
      number.className = 'item-num';
      number.textContent = String(index + 1).padStart(2, '0');

      const titleCol = document.createElement('label');
      const topRow = document.createElement('div');
      topRow.className = 'item-card-top';

      const catBadge = document.createElement('span');
      catBadge.className = `item-badge item-badge-${item.category || 'liturgy'}`;
      catBadge.textContent = item.category || 'item';

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'item-remove-btn';
      removeBtn.title = 'Remove item';
      removeBtn.textContent = '✕';
      removeBtn.addEventListener('click', () => {
        currentItems.splice(index, 1);
        renderItems(currentItems, docTitleInput.value);
      });

      topRow.append(catBadge, removeBtn);

      const titleInput = document.createElement('input');
      titleInput.value = item.title;
      titleInput.maxLength = 300;
      titleInput.placeholder = 'Item title (e.g. Call to Worship, Hymn)';
      titleInput.addEventListener('input', () => {
        currentItems[index].title = titleInput.value;
      });

      titleCol.append(topRow, titleInput);

      const contentCol = document.createElement('label');
      const contentHead = document.createElement('div');
      contentHead.className = 'item-card-top';

      const contentLabel = document.createElement('span');
      contentLabel.textContent = 'SLIDE / LITURGY CONTENT';
      contentLabel.style.fontSize = '9px';
      contentLabel.style.color = '#8197ab';
      contentLabel.style.fontWeight = '600';

      const slideBadge = document.createElement('span');
      slideBadge.className = 'item-slide-badge';
      const sCount = item.slides ? item.slides.length : Math.max(1, Math.ceil((item.content.split('\n').filter(l => l.trim()).length || 1) / 5));
      slideBadge.textContent = `${sCount} ${sCount === 1 ? 'slide' : 'slides'}`;

      contentHead.append(contentLabel, slideBadge);

      const contentTextarea = document.createElement('textarea');
      contentTextarea.value = item.content;
      contentTextarea.rows = 3;
      contentTextarea.maxLength = 10000;
      contentTextarea.placeholder = 'Add or edit lyrics, readings, prayers, and service notes…';
      contentTextarea.addEventListener('input', () => {
        currentItems[index].content = contentTextarea.value;
        currentItems[index].slides = null; // Invalidate cached slides on manual edits
        updateSummary();
        const freshCount = Math.max(1, Math.ceil((contentTextarea.value.split('\n').filter(l => l.trim()).length || 1) / 5));
        slideBadge.textContent = `${freshCount} ${freshCount === 1 ? 'slide' : 'slides'}`;
      });

      contentCol.append(contentHead, contentTextarea);

      card.append(number, titleCol, contentCol);
      itemList.append(card);
    });

    if (titleText && !docTitleInput.value) {
      docTitleInput.value = titleText;
    }

    updateSummary();
  }

  // Step 3: Render visual slide projector cards
  function renderSlideCardsPreview() {
    const slides = getAllSlideObjects();
    slidesPreviewGrid.replaceChildren();

    slides.forEach((s, idx) => {
      const card = document.createElement('div');
      card.className = 'slide-preview-card';

      const head = document.createElement('div');
      head.className = 'slide-preview-head';

      const title = document.createElement('div');
      title.className = 'slide-preview-title';
      title.textContent = s.title;

      const num = document.createElement('div');
      num.className = 'slide-preview-num';
      num.textContent = `SLIDE ${String(idx + 1).padStart(2, '0')}`;

      head.append(title, num);

      const bodyEl = document.createElement('div');
      bodyEl.className = 'slide-preview-body';
      bodyEl.textContent = s.content || '(Title slide / Instrumental)';

      card.append(head, bodyEl);
      slidesPreviewGrid.append(card);
    });

    if (previewTotalSlidesEl) previewTotalSlidesEl.textContent = slides.length;
  }

  // Step 4: Update Publish Card
  function updatePublishCard() {
    const title = docTitleInput.value || 'Sunday Worship Service';
    const total = calculateTotalSlides();
    const tplUrl = (templateUrlInput ? templateUrlInput.value : '').trim();

    if (publishSummaryTitle) publishSummaryTitle.textContent = title;
    if (publishSummaryDesc) {
      publishSummaryDesc.textContent = `Ready to generate ${total} slides using the standardized CPC template.`;
    }
    if (publishTemplateLabel) {
      const tMatch = tplUrl.match(/\/d\/([a-zA-Z0-9_-]{20,})/) || [null, tplUrl || 'Standardized CPC Template'];
      publishTemplateLabel.textContent = tMatch[1];
    }
  }

  // Add Item button
  if (addItemBtn) {
    addItemBtn.addEventListener('click', () => {
      currentItems.push({
        title: 'New Service Item',
        content: '',
        category: 'liturgy',
        slides: null,
      });
      renderItems(currentItems, docTitleInput.value);
      const allTextareas = itemList.querySelectorAll('textarea');
      if (allTextareas.length) allTextareas[allTextareas.length - 1].focus();
    });
  }

  // Import Bulletin from Google Doc
  if (fetchBulletinBtn) {
    fetchBulletinBtn.addEventListener('click', async () => {
      const docUrl = (bulletinUrlInput.value || '').trim();
      if (!docUrl) {
        showNotice('Please enter a Google Doc URL or ID.');
        return;
      }
      hideNotice();
      fetchBulletinBtn.disabled = true;
      fetchBulletinBtn.querySelector('span:first-child').textContent = 'Fetching Doc…';

      try {
        const data = await postJson('/slides/api/parse-bulletin', { doc_id_or_url: docUrl });
        pipeBanner.hidden = true;
        renderItems(data.items, data.title || 'Sunday Worship Service');
        goToStep(2); // Automatically advance to Step 2
        showNotice(`Imported ${data.items.length} items (${data.slide_count} slides) from bulletin. Review below before creating slides.`, true);
      } catch (err) {
        showNotice(err.message);
      } finally {
        fetchBulletinBtn.disabled = false;
        fetchBulletinBtn.querySelector('span:first-child').textContent = 'Import Bulletin & Continue';
      }
    });
  }

  // Parse pasted bulletin text
  if (parsePastedBtn) {
    parsePastedBtn.addEventListener('click', async () => {
      const text = (pasteTextarea.value || '').trim();
      if (!text) {
        showNotice('Please paste some bulletin text first.');
        return;
      }
      hideNotice();
      parsePastedBtn.disabled = true;
      parsePastedBtn.querySelector('span').textContent = 'Parsing…';

      try {
        const data = await postJson('/slides/api/parse-bulletin', { text });
        pipeBanner.hidden = true;
        renderItems(data.items, 'Sunday Worship Service');
        goToStep(2); // Automatically advance to Step 2
        showNotice(`Parsed ${data.items.length} items (${data.slide_count} slides) from pasted text.`, true);
      } catch (err) {
        showNotice(err.message);
      } finally {
        parsePastedBtn.disabled = false;
        parsePastedBtn.querySelector('span').textContent = 'Parse Pasted Text & Continue →';
      }
    });
  }

  // Load Planning Center Service Types
  if (isPco) {
    getJson('/slides/api/service-types').then((rows) => {
      const optionsHtml = '<option value="">Choose a service type</option>' +
        rows.map((r) => `<option value="${r.id}">${r.name}</option>`).join('');

      if (types) types.innerHTML = optionsHtml;
      if (combineTypes) combineTypes.innerHTML = optionsHtml;

      if (!rows.length) showNotice('No Planning Center service types found for this account.');
    }).catch((err) => showNotice(err.message));
  }

  // PCO Plan selection handler helper
  const setupPlanDropdown = (typeSelect, planSelect, onPlanLoaded) => {
    if (!typeSelect || !planSelect) return;
    typeSelect.addEventListener('change', async () => {
      hideNotice();
      planSelect.disabled = true;
      planSelect.innerHTML = '<option>Loading plans…</option>';
      if (!typeSelect.value) {
        planSelect.innerHTML = '<option value="">Choose a service type first</option>';
        return;
      }
      try {
        const rows = await getJson(`/slides/api/plans/${encodeURIComponent(typeSelect.value)}`);
        planSelect.innerHTML = '<option value="">Choose a service plan</option>';
        rows.forEach((row) => {
          const date = row.date ? ` · ${new Date(`${row.date}T12:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}` : '';
          planSelect.add(new Option(row.title + date, row.id));
        });
        planSelect.disabled = false;
        if (!rows.length) {
          planSelect.innerHTML = '<option value="">No plans found</option>';
          showNotice('No service plans found for this service type.');
        }
      } catch (err) {
        planSelect.innerHTML = '<option value="">Plans unavailable</option>';
        showNotice(err.message);
      }
    });

    if (onPlanLoaded) {
      planSelect.addEventListener('change', onPlanLoaded);
    }
  };

  // PCO-only tab plan load
  setupPlanDropdown(types, plans, async () => {
    hideNotice();
    if (!plans.value) return;
    plans.disabled = true;
    try {
      const rows = await getJson(`/slides/api/plan/${encodeURIComponent(types.value)}/${encodeURIComponent(plans.value)}`);
      pipeBanner.hidden = true;
      const planLabel = plans.options[plans.selectedIndex].text.split(' · ')[0];
      renderItems(rows, `Worship Service · ${planLabel}`);
      goToStep(2); // Automatically advance to Step 2
      showNotice('Planning Center plan loaded. Review items before creating files.', true);
    } catch (err) {
      showNotice(err.message);
    } finally {
      plans.disabled = false;
    }
  });

  // Setup combine plan selector
  setupPlanDropdown(combineTypes, combinePlans, null);

  // Combine Bulletin + Planning Center
  if (combineBtn) {
    combineBtn.addEventListener('click', async () => {
      const docUrl = (combineBulletinUrl ? combineBulletinUrl.value : '').trim();
      const serviceTypeId = combineTypes ? combineTypes.value : '';
      const planId = combinePlans ? combinePlans.value : '';

      if (!docUrl) {
        showNotice('Please enter a Bulletin Google Doc URL or ID.');
        return;
      }
      if (!serviceTypeId || !planId) {
        showNotice('Please select both a Planning Center service type and plan.');
        return;
      }

      hideNotice();
      combineBtn.disabled = true;
      combineBtn.querySelector('span:first-child').textContent = 'Importing & Piping…';

      try {
        // Step 1: Parse the bulletin
        const bulletinData = await postJson('/slides/api/parse-bulletin', { doc_id_or_url: docUrl });
        // Step 2: Pipe PCO song lyrics and items into bulletin
        const pipeData = await postJson('/slides/api/pipe-pco', {
          service_type_id: serviceTypeId,
          plan_id: planId,
          bulletin_items: bulletinData.items,
        });

        pipeBanner.hidden = false;
        pipeBanner.textContent = `Piped lyrics and arrangements from Planning Center into ${pipeData.synced_count || 0} songs.`;
        renderItems(pipeData.items, bulletinData.title || 'Sunday Worship Service');
        goToStep(2); // Advance to Step 2
        showNotice(`Combined bulletin & Planning Center: ${pipeData.items.length} items (${pipeData.slide_count} slides) ready.`, true);
      } catch (err) {
        showNotice(err.message);
      } finally {
        combineBtn.disabled = false;
        combineBtn.querySelector('span:first-child').textContent = 'Import & Pipe Planning Center Lyrics →';
      }
    });
  }

  // Create Files (Google Slides / Doc)
  if (createBtn) {
    createBtn.addEventListener('click', async (event) => {
      const button = event.currentTarget;
      const outputs = [];
      if (document.querySelector('#make-slides').checked) outputs.push('slides');
      if (document.querySelector('#make-doc').checked) outputs.push('doc');

      if (!outputs.length) {
        showNotice('Choose Google Slides, Google Doc, or both.');
        return;
      }

      const templateId = (templateUrlInput ? templateUrlInput.value : '').trim();
      button.disabled = true;
      publishProgress.hidden = false;
      publishProgressText.textContent = 'Cloning standardized template and populating slides in Google Drive…';
      hideNotice();

      try {
        const responseData = await postJson('/slides/api/create', {
          title: docTitleInput.value || 'Sunday Worship Service',
          items: currentItems,
          outputs,
          template_id: templateId,
        });

        publishProgress.hidden = true;
        createdLinks.replaceChildren();
        createdLinks.hidden = false;

        const linkConfigs = [
          ['slides', 'Open Google Slides (Standardized Template)'],
          ['doc', 'Open Google Doc'],
        ];

        linkConfigs.forEach(([key, label]) => {
          if (responseData.created && responseData.created[key]) {
            const itemObj = responseData.created[key];
            const link = document.createElement('a');
            link.href = itemObj.url;
            link.target = '_blank';
            link.rel = 'noopener';
            link.textContent = `${label} ↗`;
            createdLinks.append(link);
          }
        });

        showNotice('Your slides are populated and ready in Google Drive!', true);
      } catch (err) {
        publishProgress.hidden = true;
        showNotice(err.message);
      } finally {
        button.disabled = false;
      }
    });
  }
})();
