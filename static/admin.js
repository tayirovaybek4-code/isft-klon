const $ = selector => document.querySelector(selector);
const panel = $('#panel');
const sidebar = $('#sidebar');
const logout = $('#logout');
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);
const statuses = ['Yangi', 'Ko‘rib chiqilmoqda', 'Qabul qilingan', 'Rad etilgan'];
const nav = {
  dashboard: 'Bosh sahifa',
  applications: 'Arizalar',
  students: 'Talabalar',
  programs: 'Yo‘nalishlar',
  content: 'E’lonlar va yangiliklar',
  pages: 'Sahifalar',
  menu: 'Menyu',
  media: 'Media',
  statistics: 'Statistika',
  sheets: 'Google Sheets',
  audit: 'Faoliyat jurnali',
  settings: 'Sozlamalar',
};
let csrf = '';
let section = 'dashboard';
let view = 0;
let records = [];
let toastTimer;

function toast(message, kind = 'success') {
  const element = $('#toast');
  element.textContent = message;
  element.className = 'toast show ' + kind;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => element.classList.remove('show'), 4200);
}

async function api(path, method = 'GET', data) {
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        'X-CSRF-Token': csrf,
        ...(data === undefined ? {} : {'Content-Type': 'application/json'}),
      },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
  } catch {
    throw new Error('Server bilan aloqa uzildi. Serverni tekshirib, qayta urinib ko‘ring.');
  }
  const result = await response.json().catch(() => null);
  if (response.status === 401 && path !== '/api/login' && csrf) {
    showLogin('Sessiya tugadi. Qayta kiring.');
  }
  if (!response.ok || result === null) throw new Error(result?.error || 'Server javobida xato.');
  return result;
}

function option(value, label, selected) {
  return `<option value="${esc(value)}"${value === selected ? ' selected' : ''}>${esc(label)}</option>`;
}

function action(label, name, id = '', extraClass = '') {
  return `<button class="secondary ${extraClass}" type="button" data-action="${name}" data-id="${esc(id)}">${esc(label)}</button>`;
}

function table(headers, rows, empty = 'Hozircha yozuv yo‘q.') {
  return `<div class="tablewrap" tabindex="0" role="region" aria-label="Ma’lumotlar jadvali">
    <table>
      <thead><tr>${headers.map(header => `<th scope="col">${esc(header)}</th>`).join('')}</tr></thead>
      <tbody>${rows.join('') || `<tr><td colspan="${headers.length}" class="muted">${esc(empty)}</td></tr>`}</tbody>
    </table>
  </div>`;
}

function stat(label, number) {
  return `<div class="stat"><small>${esc(label)}</small><b>${Number(number).toLocaleString('uz-UZ')}</b></div>`;
}

function renderDashboard(data) {
  const largest = Math.max(1, ...data.days.map(day => day.count));
  const bars = data.days.map(day => `
    <div class="bar" title="${esc(day.day)} · ${day.count} ta ariza"
         style="height:${Math.max(2, day.count / largest * 100)}%"></div>`).join('');
  panel.innerHTML = `
    <div class="toolbar">
      <div><h1 class="admin-title">${section === 'statistics' ? 'Arizalar statistikasi' : 'Xush kelibsiz, administrator'}</h1>
        <p class="muted">Qabul arizalarining joriy holati</p></div>
      ${action('Arizalarni ko‘rish', 'go', 'applications')}
    </div>
    <div class="stats">
      ${stat('Jami arizalar', data.total)}
      ${stat('Bugungi arizalar', data.today)}
      ${stat('Qabul qilingan', data.statuses['Qabul qilingan'] ?? 0)}
      ${stat('Ko‘rib chiqilmoqda', data.statuses['Ko‘rib chiqilmoqda'] ?? 0)}
    </div>
    <div class="layout">
      <section class="widget">
        <h3>So‘nggi 30 kun</h3>
        <div class="bars" role="img" aria-label="Kunlar bo‘yicha arizalar grafigi">${bars}</div>
        <div class="chart-dates"><span>${esc(data.days[0].day)}</span><span>${esc(data.days.at(-1).day)}</span></div>
      </section>
      <section class="widget">
        <h3>Ariza holatlari</h3>
        ${statuses.map(status => `<p class="status-summary"><span class="pill">${status}</span>
          <strong>${data.statuses[status] ?? 0}</strong></p>`).join('')}
      </section>
    </div>
    <section class="widget widget-stack">
      <h3>Yo‘nalishlar bo‘yicha arizalar</h3>
      ${table(['№', 'Yo‘nalish', 'Arizalar'], data.ranks.map((row, index) => `
        <tr><td>${index + 1}</td><td>${esc(row.name)}${row.archived ? ' <small class="muted">(arxiv)</small>' : ''}</td>
          <td>${row.count}</td></tr>`))}
    </section>`;
}

function renderApplications(data) {
  records = data;
  const accepted = section === 'students';
  panel.innerHTML = `
    <div class="toolbar">
      <h1 class="admin-title">${accepted ? 'Qabul qilingan talabalar' : 'Qabul arizalari'}</h1>
      ${action('Yangilash', 'go', section)}
    </div>
    <div class="record-filters">
      <label>Qidirish <input id="record-search" type="search" placeholder="Ism, telefon, yo‘nalish yoki ariza raqami"></label>
      ${accepted ? '' : `<label>Holat <select id="status-filter">
        <option value="">Barchasi</option>${statuses.map(status => option(status, status)).join('')}
      </select></label>`}
    </div>
    <p id="record-count" class="muted"></p>
    <div id="application-list" class="widget"></div>`;
  $('#record-search').addEventListener('input', drawApplications);
  $('#status-filter')?.addEventListener('change', drawApplications);
  drawApplications();
}

function drawApplications() {
  const query = $('#record-search').value.trim().toLowerCase().replace(/^#/, '');
  const status = section === 'students' ? 'Qabul qilingan' : $('#status-filter').value;
  const filtered = records.filter(row => {
    if (status && row.status !== status) return false;
    return [row.id, row.first_name, row.last_name, row.father_name, row.phone, row.program]
      .join(' ').toLowerCase().includes(query);
  });
  $('#record-count').textContent = filtered.length + ' ta yozuv';
  $('#application-list').innerHTML = table(
    ['Ariza №', 'Arizachi', 'Telefon', 'Yo‘nalish', 'Yuborilgan', 'Holat', 'Amal'],
    filtered.map(row => `
      <tr>
        <td>#${row.id}</td>
        <td><details>
          <summary>${esc(row.first_name)} ${esc(row.last_name)}</summary>
          <dl class="record-details">
            <dt>Otasining ismi</dt><dd>${esc(row.father_name || '—')}</dd>
            <dt>Tug‘ilgan sana</dt><dd>${esc(row.birth_date || '—')}</dd>
            <dt>Ta’lim shakli</dt><dd>${esc(row.study_type || '—')}</dd>
            <dt>Rozilik</dt><dd>${row.consent === 1 ? 'Ha' : 'Ko‘rsatilmagan'}</dd>
          </dl>
        </details></td>
        <td>${esc(row.phone)}</td>
        <td>${esc(row.program)}</td>
        <td>${esc(row.created_at.replace('T', ' '))}</td>
        <td><select data-status="${row.id}" aria-label="#${row.id} ariza holati">
          ${statuses.map(value => option(value, value, row.status)).join('')}
        </select></td>
        <td>${action('Saqlash', 'save-status', row.id)}</td>
      </tr>`),
    query ? 'Qidiruvga mos ariza topilmadi.' : 'Bu ro‘yxatda arizalar yo‘q.',
  );
}

const collections = {
  programs: {
    path: 'programs', title: 'Ta’lim yo‘nalishlari', add: 'Yo‘nalish qo‘shish',
    headers: ['№', 'Nomi', 'Holati', 'Amallar'],
    cells: row => `<td>${row.id}</td><td>${esc(row.name)}</td><td>${row.active ? 'Faol' : 'Yashirin'}</td>`,
    toggle: 'active',
  },
  content: {
    path: 'content', title: 'E’lonlar va yangiliklar', add: 'Material qo‘shish',
    headers: ['Turi', 'Sarlavha', 'Holati', 'Amallar'],
    cells: row => `<td>${esc(row.kind)}</td><td>${esc(row.title)}</td><td>${row.published ? 'Saytda' : 'Qoralama'}</td>`,
    toggle: 'published',
  },
  pages: {
    path: 'content', title: 'Sahifa materiallari', add: 'Sahifa materiali qo‘shish',
    headers: ['Sahifa', 'Sarlavha', 'Holati', 'Amallar'],
    cells: row => `<td>${({about: 'Biz haqimizda', contact: 'Aloqa'})[row.page] || 'Eski joylashuv'}</td>
      <td>${esc(row.title)}</td><td>${row.published ? 'Saytda' : 'Qoralama'}</td>`,
    toggle: 'published',
  },
  menu: {
    path: 'menu', title: 'Sayt menyusi', add: 'Menyu bandi qo‘shish',
    headers: ['Tartib', 'Nomi', 'Havola', 'Holati', 'Amallar'],
    cells: row => `<td>${esc(row.position)}</td><td>${esc(row.label)}</td><td>${esc(row.url)}</td>
      <td>${row.active ? 'Faol' : 'Yashirin'}</td>`,
  },
};

function renderCollection(data) {
  const config = collections[section];
  records = section === 'pages' ? data.filter(row => row.kind === 'Sahifa')
    : section === 'content' ? data.filter(row => row.kind !== 'Sahifa')
    : data;
  panel.innerHTML = `
    <div class="toolbar"><h1 class="admin-title">${config.title}</h1>${action(config.add, 'new')}</div>
    <div class="widget">${table(config.headers, records.map(row => {
      const toggle = config.toggle;
      const toggleLabel = toggle === 'published' ? 'Chop etish' : 'Faollashtirish';
      return `<tr>${config.cells(row)}<td>
        ${action('Tahrirlash', 'edit', row.id)}
        ${toggle ? action(row[toggle] ? 'Yashirish' : toggleLabel, 'toggle', row.id) : ''}
        ${action('O‘chirish', 'delete', row.id, 'danger')}
      </td></tr>`;
    }))}</div>`;
}

function textInput(key, label, value, maxLength, required = false) {
  return `<label>${esc(label)} <input name="${key}" maxlength="${maxLength}" value="${esc(value)}"
    ${required ? 'required' : ''}></label>`;
}

function checkbox(name, label, checked) {
  return `<label class="check"><input type="checkbox" name="${name}" ${checked ? 'checked' : ''}> ${label}</label>`;
}

function editRecord(row = {}) {
  const current = section;
  const config = collections[current];
  const itemId = row.id;
  let fields;
  if (current === 'programs') {
    fields = textInput('name', 'Yo‘nalish nomi', row.name, 200, true) + `
      <label>Tavsif <textarea name="description" maxlength="10000">${esc(row.description)}</textarea></label>
      ${checkbox('active', 'Faol', row.active !== 0)}`;
  } else if (current === 'menu') {
    fields = textInput('label', 'Tugma nomi', row.label, 100, true) +
      textInput('url', 'Ichki havola, masalan /about.html', row.url || '/', 200, true) + `
      <label>Tartib <input name="position" type="number" min="-10000" max="10000" value="${esc(row.position ?? 0)}" required></label>
      ${checkbox('active', 'Faol', row.active !== 0)}`;
  } else {
    const types = ['E’lon', 'Yangilik', 'Sahifa'];
    const kind = row.kind || (current === 'pages' ? 'Sahifa' : 'Yangilik');
    const page = row.page || (row.title?.toLowerCase().includes('universitet') ? 'about' : 'contact');
    fields = `<label>Material turi <select name="kind">
        ${types.map(type => option(type, type, kind)).join('')}
      </select></label>
      <label id="content-page" ${kind === 'Sahifa' ? '' : 'hidden'}>Saytdagi sahifa
        <select name="page">
          ${option('about', 'Biz haqimizda', page)}${option('contact', 'Aloqa', page)}
        </select>
      </label>` + textInput('title', 'Sarlavha', row.title, 200, true) + `
      <label>Matn <textarea name="body" maxlength="10000" required>${esc(row.body)}</textarea></label>
      ${checkbox('published', 'Saytda chop etish', row.published === 1)}`;
  }
  panel.innerHTML = `
    <div class="toolbar">
      <h1 class="admin-title">${itemId ? 'Tahrirlash' : config.add}</h1>${action('← Orqaga', 'go', current)}
    </div>
    <div class="widget modal-form">
      <form id="edit-form">${fields}${saveControls('Saqlash')}</form>
    </div>`;
  const form = $('#edit-form');
  form.elements.kind?.addEventListener('change', () => {
    $('#content-page').hidden = form.elements.kind.value !== 'Sahifa';
  });
  form.addEventListener('submit', event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    for (const flag of ['published', 'active']) {
      if (form.elements[flag]) data[flag] = form.elements[flag].checked;
    }
    if (form.elements.position) data.position = Number(data.position);
    const path = '/api/' + config.path + (itemId ? '/' + itemId : '');
    submitForm(form, path, itemId ? 'PATCH' : 'POST', data, () => {
      const destination = config.path === 'content' ? (data.kind === 'Sahifa' ? 'pages' : 'content') : current;
      return navigate(destination);
    });
  });
}

function saveControls(label) {
  return `<p class="form-error error" role="alert" hidden></p><button class="btn" type="submit">${label}</button>`;
}

async function submitForm(form, path, method, data, afterSave) {
  const submit = form.querySelector('[type="submit"]');
  const errorBox = form.querySelector('.form-error');
  if (submit.disabled) return;
  submit.disabled = true;
  errorBox.hidden = true;
  const formView = view;
  try {
    await api(path, method, data);
    toast('Saqlandi.');
    if (form.isConnected && formView === view) await afterSave?.();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  } finally {
    submit.disabled = false;
  }
}

function renderSettings(data) {
  const fields = [
    ['site_name', 'Universitet nomi'], ['hero_title', 'Bosh sahifa sarlavhasi'],
    ['hero_subtitle', 'Bosh sahifa izohi'], ['contact_phone', 'Telefon'],
    ['contact_email', 'Email'], ['contact_address', 'Manzil'], ['footer_text', 'Sahifa pastidagi yozuv'],
  ];
  panel.innerHTML = `
    <h1 class="admin-title">Sayt sozlamalari</h1>
    <div class="widget modal-form">
      <form id="settings-form">
        ${fields.map(([key, label]) => textInput(key, label, data[key], 1000)).join('')}
        ${saveControls('Saytga saqlash')}
      </form>
    </div>`;
  const form = $('#settings-form');
  form.addEventListener('submit', event => {
    event.preventDefault();
    submitForm(form, '/api/settings', 'POST', Object.fromEntries(new FormData(form)));
  });
}

function renderMedia(data) {
  records = data;
  panel.innerHTML = `
    <h1 class="admin-title">Media kutubxona</h1>
    <div class="toolbar media-toolbar">
      <label>Rasm fayli <input id="upload-file" type="file" accept="image/png,image/jpeg,image/webp,image/gif"></label>
      ${action('Rasm yuklash', 'upload')}
    </div>
    <p class="hint">PNG, JPG, WEBP yoki GIF. Hajmi 3 MB gacha.</p>
    <div class="widget">${table(['Rasm', 'Fayl nomi', 'Amallar'], data.map(row => `
      <tr><td><img class="media-thumb" src="/media/${esc(row.filename)}" alt="" loading="lazy"></td>
        <td>${esc(row.original_name)}</td><td>
          ${action('Havolani nusxalash', 'copy', row.id)}
          ${action('O‘chirish', 'delete', row.id, 'danger')}
        </td></tr>`))}</div>`;
}

async function uploadMedia() {
  const file = $('#upload-file').files[0];
  if (!file) throw new Error('Avval rasmni tanlang.');
  if (file.size > 3_000_000) throw new Error('Rasm hajmi 3 MB dan oshmasin.');
  const data = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = () => reject(new Error('Rasmni o‘qib bo‘lmadi.'));
    reader.readAsDataURL(file);
  });
  await api('/api/media', 'POST', {name: file.name, data});
}

function renderSheets(data) {
  const url = data.sheet_id ? 'https://docs.google.com/spreadsheets/d/' + encodeURIComponent(data.sheet_id) + '/edit' : '';
  panel.innerHTML = `
    <div class="toolbar"><h1 class="admin-title">Google Sheets</h1>${action('Holatni yangilash', 'go', 'sheets')}</div>
    <section class="widget">
      <h3>${data.configured ? 'Jadval ulangan' : 'Google Sheets hali ulanmagan'}</h3>
      <p class="muted">${data.configured
        ? 'Sayt ochiq turganda yangi arizalar va holat o‘zgarishlari avtomatik yuboriladi.'
        : 'Jadvalni ulash uchun loyiha papkasida GOOGLE_SHEETS.md ni oching.'}</p>
      ${data.error ? `<p class="error" role="status">${esc(data.error)}</p>` : ''}
      ${url ? `<a class="outline-btn" href="${url}" target="_blank" rel="noopener noreferrer">Jadvalni ochish ↗</a>` : ''}
    </section>
    <div class="stats widget-stack">
      ${stat('Jadvalga yozilgan', data.synced)}
      ${stat('Yuborishni kutmoqda', data.pending)}
    </div>`;
}

function renderAudit(data) {
  panel.innerHTML = `<h1 class="admin-title">Faoliyat jurnali</h1>
    <div class="widget">${table(['Vaqt', 'Amal'], data.map(row => `
      <tr><td>${esc(row.created_at.replace('T', ' '))}</td><td>${esc(row.action)}</td></tr>`))}</div>`;
}

const screens = {
  dashboard: ['dashboard', renderDashboard],
  statistics: ['dashboard', renderDashboard],
  applications: ['applications', renderApplications],
  students: ['applications', renderApplications],
  media: ['media', renderMedia],
  settings: ['settings', renderSettings],
  sheets: ['sheets', renderSheets],
  audit: ['audit', renderAudit],
};
for (const [name, collection] of Object.entries(collections)) screens[name] = [collection.path, renderCollection];

async function navigate(next) {
  section = next;
  const requestView = ++view;
  const [path, render] = screens[next];
  $('#heading').textContent = nav[next];
  for (const button of sidebar.querySelectorAll('button')) {
    const selected = button.dataset.id === next;
    button.classList.toggle('active', selected);
    if (selected) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  }
  panel.innerHTML = '<p class="loading" role="status">Yuklanmoqda…</p>';
  try {
    const data = await api('/api/' + path);
    if (requestView === view) render(data);
  } catch (error) {
    if (requestView === view) {
      panel.innerHTML = `<p class="error" role="alert">${esc(error.message)}</p>${action('Qayta urinish', 'go', next)}`;
    }
  }
}

async function handleAction(button) {
  const {action: name, id} = button.dataset;
  const current = section;
  const actionView = view;
  const row = records.find(item => String(item.id) === id);
  const collection = collections[current];
  if (name === 'go') return navigate(id);
  if (name === 'new') return editRecord();
  if (name === 'edit' && row) return editRecord(row);
  if (button.disabled) return;
  button.disabled = true;
  try {
    if (name === 'save-status' && row) {
      const value = $(`[data-status="${row.id}"]`).value;
      await api('/api/applications/' + row.id, 'PATCH', {status: value});
      row.status = value;
      toast('Ariza holati saqlandi.');
      if (view === actionView && current === 'students' && value !== 'Qabul qilingan') drawApplications();
    } else if (name === 'toggle' && row) {
      const flag = collection.toggle;
      await api('/api/' + collection.path + '/' + row.id, 'PATCH', {[flag]: !row[flag]});
      toast('Yangilandi.');
      if (view === actionView) await navigate(current);
    } else if (name === 'delete' && row && confirm('Ushbu yozuvni o‘chirasizmi?')) {
      const path = collection?.path || 'media';
      await api('/api/' + path + '/' + row.id, 'DELETE');
      toast('O‘chirildi.');
      if (view === actionView) await navigate(current);
    } else if (name === 'upload') {
      await uploadMedia();
      toast('Rasm yuklandi.');
      if (view === actionView) await navigate(current);
    } else if (name === 'copy' && row) {
      const url = new URL('/media/' + row.filename, location.origin).href;
      if (navigator.clipboard) await navigator.clipboard.writeText(url);
      else prompt('Rasm havolasi', url);
      toast('Rasm havolasi tayyor.');
    }
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    button.disabled = false;
  }
}

function showLogin(message = '') {
  view++;
  csrf = '';
  records = [];
  $('#admin-sidebar').hidden = true;
  logout.hidden = true;
  $('#heading').textContent = 'Admin panel';
  panel.innerHTML = `
    <section class="widget login-card">
      <p class="eyebrow">ISFT PRO</p>
      <h1 class="admin-title">Administratorga kirish</h1>
      <p class="muted">Arizalar va sayt mazmunini boshqarish uchun kiring.</p>
      <form id="admin-login-form">
        <label>Login <input name="username" autocomplete="username" required value="admin"></label>
        <label>Parol <input name="password" type="password" autocomplete="current-password" required></label>
        <p id="admin-login-error" class="error" role="alert" ${message ? '' : 'hidden'}>${esc(message)}</p>
        <button class="btn" type="submit">Kirish</button>
      </form>
      <a class="text-link" href="/">← Asosiy saytga qaytish</a>
    </section>`;
  const form = $('#admin-login-form');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button');
    const errorBox = $('#admin-login-error');
    if (button.disabled) return;
    button.disabled = true;
    button.textContent = 'Tekshirilmoqda…';
    errorBox.hidden = true;
    try {
      await api('/api/login', 'POST', Object.fromEntries(new FormData(form)));
      const session = await api('/api/session');
      if (!session.logged_in) throw new Error('Sessiyani ochib bo‘lmadi. Brauzer cookie sozlamasini tekshiring.');
      showWorkspace(session.csrf);
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
      button.disabled = false;
      button.textContent = 'Kirish';
    }
  });
}

function showWorkspace(token) {
  csrf = token;
  sidebar.innerHTML = Object.entries(nav).map(([id, label]) => action(label, 'go', id)).join('');
  $('#admin-sidebar').hidden = false;
  logout.hidden = false;
  navigate('dashboard');
}

async function startAdmin() {
  try {
    const session = await api('/api/session');
    if (session.logged_in) showWorkspace(session.csrf);
    else showLogin();
  } catch (error) {
    panel.innerHTML = `<p class="error" role="alert">${esc(error.message)}</p>
      <button class="secondary" type="button" id="retry-login">Qayta urinish</button>`;
    $('#retry-login').addEventListener('click', startAdmin, {once: true});
  }
}

logout.addEventListener('click', async () => {
  logout.disabled = true;
  try {
    await api('/api/logout', 'POST', {});
    showLogin('Sessiyadan chiqdingiz.');
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    logout.disabled = false;
  }
});

document.addEventListener('click', event => {
  const button = event.target.closest('button[data-action]');
  if (button) handleAction(button);
});
startAdmin();
