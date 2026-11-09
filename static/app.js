const $ = selector => document.querySelector(selector);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);
const icons = ['▣', '▥', '◈', '▤', '⬡', '◎', '▣', '▱', '▦', '▧', '✎', '♧', '▤', '◉', '❖', '✒'];
const params = new URLSearchParams(location.search);

async function api(url, body) {
  let response;
  try {
    response = await fetch(url, body ? {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    } : undefined);
  } catch {
    throw new Error('Server bilan bog‘lanib bo‘lmadi. Saytni ishga tushirib, qayta urinib ko‘ring.');
  }
  const result = await response.json().catch(() => null);
  if (!response.ok || result === null) throw new Error(result?.error || 'Ma’lumotni yuklab bo‘lmadi.');
  return result;
}

function setupMenu() {
  const button = $('#mobile-menu');
  const menu = $('#public-nav');
  function toggle(open) {
    menu.classList.toggle('open', open);
    button.setAttribute('aria-expanded', String(open));
  }
  button.addEventListener('click', () => toggle(!menu.classList.contains('open')));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.classList.contains('open')) {
      toggle(false);
      button.focus();
    }
  });
  menu.addEventListener('click', event => {
    if (event.target.closest('a')) toggle(false);
  });
}

function markCurrentPage() {
  const path = location.pathname === '/index.html' ? '/' : location.pathname;
  for (const link of document.querySelectorAll('#public-nav a')) {
    if (link.pathname === path && link.search === location.search) link.setAttribute('aria-current', 'page');
  }
}

function renderMenu(items) {
  const menu = $('#public-nav');
  const links = [];
  for (const item of items) {
    if (!/^\/(?!\/)[a-zA-Z0-9_/?=&.%-]*$/.test(item.url)) continue;
    const link = document.createElement('a');
    link.href = item.url;
    link.textContent = item.label;
    links.push(link);
  }
  menu.replaceChildren(...links);
  $('#mobile-menu').hidden = links.length === 0;
  markCurrentPage();
}

function renderSettings(settings) {
  const siteName = settings.site_name || 'ISFT Universiteti';
  if (siteName !== 'ISFT Universiteti') {
    document.querySelectorAll('[data-site-name]').forEach(element => { element.textContent = siteName; });
    document.title = document.title.replace(/ — ISFT$/, ' — ' + siteName);
  }
  $('#logo').setAttribute('aria-label', siteName + ' bosh sahifasi');
  const title = $('#hero-title');
  if (title && settings.hero_title && settings.hero_title !== 'ISFT Universiteti') {
    title.textContent = settings.hero_title;
    title.classList.add('custom-hero-title');
  }
  const subtitle = $('#hero-subtitle');
  if (subtitle) subtitle.textContent = settings.hero_subtitle;
  document.querySelectorAll('[data-footer-text]').forEach(element => {
    element.textContent = settings.footer_text;
  });
  renderContact(settings);
}

function renderContact(settings) {
  const phone = settings.contact_phone?.trim();
  const email = settings.contact_email?.trim();
  const phoneUrl = phone && /^\+?[0-9 ()-]+$/.test(phone) ? 'tel:' + phone.replace(/[ ()-]/g, '') : '';
  const emailUrl = email && /^[^\s@:?&#]+@[^\s@:?&#]+\.[^\s@:?&#]+$/.test(email) ? 'mailto:' + email : '';
  for (const [selector, value, url] of [
    ['#contact-phone', phone, phoneUrl],
    ['#contact-email', email, emailUrl],
    ['#contact-address', settings.contact_address, ''],
  ]) {
    const element = $(selector);
    if (!element) continue;
    if (url) {
      const link = document.createElement('a');
      link.href = url;
      link.textContent = value;
      element.replaceChildren(link);
    } else {
      element.textContent = value || 'Ma’lumot kiritilmagan.';
    }
  }
}

function empty(message) {
  return `<p class="public-empty">${escapeHtml(message)}</p>`;
}

function renderPrograms(programs) {
  const grid = $('#program-cards');
  if (grid) {
    grid.innerHTML = programs.map((program, index) => `
      <a class="program-tile" href="/program-detail.html?id=${encodeURIComponent(program.id)}">
        <span class="tile-icon" aria-hidden="true">${icons[index % icons.length]}</span>
        <span>${escapeHtml(program.name)}</span>
      </a>`).join('') || empty('Hozircha faol yo‘nalishlar yo‘q.');
  }
  const detail = $('#program-detail');
  if (detail) {
    const program = programs.find(item => String(item.id) === params.get('id'));
    if (program) $('#program-title').textContent = program.name;
    detail.innerHTML = program ? `
      <article class="card program-info">
        <p>${escapeHtml(program.description || 'Yo‘nalish tavsifi hozircha kiritilmagan.')}</p>
        <a class="btn" href="/apply.html?program_id=${encodeURIComponent(program.id)}">Ariza topshirish →</a>
      </article>` : empty('Yo‘nalish topilmadi yoki qabul uchun yopilgan.');
  }
  const select = $('#program-select');
  if (select) {
    select.replaceChildren(new Option('Yo‘nalishni tanlang', ''));
    for (const program of programs) select.add(new Option(program.name, program.id));
    const selected = programs.find(program => String(program.id) === params.get('program_id'))
      ?? programs.find(program => program.name === params.get('program'));
    if (selected) select.value = String(selected.id);
    $('#apply-fields').disabled = programs.length === 0;
    showApplicationResult(programs.length ? '' : 'Hozircha ariza qabul qilinadigan yo‘nalish yo‘q.', 'error');
  }
}

function renderContent(items) {
  const feed = $('#public-content');
  if (feed) {
    const updates = items.filter(item => item.kind === 'Yangilik' || item.kind === 'E’lon');
    const shown = $('#hero-title') ? updates.slice(0, 3) : updates;
    feed.innerHTML = shown.map((item, index) => `
      <article class="news-card">
        <img src="/news-${index % 3 + 1}.jpg" alt="" loading="lazy">
        <div>
          <span class="eyebrow">${escapeHtml(item.kind)}</span>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.body)}</p>
        </div>
      </article>`).join('') || empty('Hozircha yangilik va e’lonlar yo‘q.');
  }
  const page = $('#page-content');
  if (page) {
    const destination = page.dataset.page;
    const material = items.filter(item => {
      if (item.kind !== 'Sahifa') return false;
      if (item.page) return item.page === destination;
      // Older articles used their title to decide whether to show on About.
      return destination === 'contact' || item.title.toLowerCase().includes('universitet');
    });
    page.innerHTML = material.map(item => `
      <article class="card"><h2>${escapeHtml(item.title)}</h2><p>${escapeHtml(item.body)}</p></article>
    `).join('') || (destination === 'about' ? empty('Batafsil ma’lumot hozircha kiritilmagan.') : '');
  }
}

function showApplicationResult(message, kind = '') {
  const element = $('#apply-result');
  element.className = message ? 'form-result ' + kind : 'form-result';
  element.textContent = message;
  element.hidden = !message;
}

function setupApplication() {
  const form = $('#apply-form');
  if (!form) return;
  const fields = $('#apply-fields');
  const button = form.querySelector('button[type="submit"]');
  const localDate = new Date();
  const today = [
    localDate.getFullYear(),
    String(localDate.getMonth() + 1).padStart(2, '0'),
    String(localDate.getDate()).padStart(2, '0'),
  ].join('-');
  form.elements.birth_date.max = today;
  let lastAttempt;

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (fields.disabled || !form.reportValidity()) return;
    const data = Object.fromEntries(new FormData(form));
    data.program_id = Number(data.program_id);
    data.consent = data.consent === 'yes';
    const body = JSON.stringify(data);
    if (lastAttempt?.body !== body) {
      const bytes = crypto.getRandomValues(new Uint8Array(16));
      const key = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
      lastAttempt = {body, key};
    }
    data.request_id = lastAttempt.key;

    fields.disabled = true;
    button.textContent = 'Yuborilmoqda…';
    showApplicationResult('');
    try {
      const result = await api('/api/apply', data);
      showApplicationResult('Arizangiz saqlandi. Ariza raqami #' + result.application_id + '.', 'success');
      lastAttempt = undefined;
      form.reset();
      $('#apply-result').focus();
    } catch (error) {
      showApplicationResult(error.message, 'error');
    } finally {
      fields.disabled = false;
      button.textContent = 'Arizani yuborish';
    }
  });
}

setupMenu();
markCurrentPage();
setupApplication();
api('/api/public/menu').then(renderMenu).catch(() => { /* Keep the built-in navigation. */ });
api('/api/public/settings').then(renderSettings).catch(() => renderContact({}));
if ($('#program-cards') || $('#program-detail') || $('#apply-form')) {
  api('/api/public/programs').then(renderPrograms).catch(error => {
    const area = $('#program-cards') || $('#program-detail');
    if (area) area.innerHTML = empty(error.message);
    if ($('#apply-form')) showApplicationResult(error.message, 'error');
  });
}
if ($('#public-content') || $('#page-content')) {
  api('/api/public/content').then(renderContent).catch(error => {
    const area = $('#public-content') || $('#page-content');
    area.innerHTML = empty(error.message);
  });
}
