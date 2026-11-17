const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let csrf='',section='dashboard',records=[];
const nav=[['dashboard','⌂ Bosh sahifa'],['applications','▤ Arizalar'],['students','♙ Talabalar'],['programs','▱ Yo‘nalishlar'],['content','▣ E’lonlar va yangiliklar'],['pages','▤ Sahifalar (CMS)'],['menu','☷ Menyu boshqaruvi'],['media','▧ Media kutubxona'],['statistics','◫ Statistika va tahlil'],['audit','◷ Faoliyat jurnali'],['settings','⚙ Sozlamalar']];
function toast(msg){$('#toast').textContent=msg;$('#toast').classList.add('show');setTimeout(()=>$('#toast').classList.remove('show'),3500)}
async function api(url,method='GET',data){const r=await fetch(url,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:data?JSON.stringify(data):undefined});const out=await r.json();if(!r.ok)throw Error(out.error||'Xatolik');return out}
function table(head,rows){return `<div class="tablewrap"><table><thead><tr>${head.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`}
function stat(label,n){return `<div class="stat"><small>${esc(label)}</small><b>${Number(n).toLocaleString('en-US')}</b><span>● Ma’lumotlar bazasidan</span></div>`}
function bars(days){const max=Math.max(1,...days.map(x=>x.count));return `<div class="bars">${days.map(d=>`<div title="${esc(d.day)}: ${d.count}" class="bar" style="height:${Math.max(3,d.count/max*100)}%"><label>${esc(d.day.slice(5))}</label></div>`).join('')}</div>`}
function statusSelect(r){return `<select data-status="${r.id}">${['Yangi','Ko‘rib chiqilmoqda','Qabul qilingan','Rad etilgan'].map(x=>`<option ${r.status===x?'selected':''}>${x}</option>`).join('')}</select>`}
async function dashboard(){const d=await api('/api/dashboard');$('#panel').innerHTML=`<div class="toolbar"><div><h1 style="font-size:30px;margin:0">Xush kelibsiz, Administrator!</h1><p class="muted">Jonli arizalar statistikasi</p></div><button class="btn" data-go="content">+ Yangi e’lon</button></div><div class="stats">${stat('Jami arizalar',d.total)}${stat('Bugungi arizalar',d.today)}${stat('Qabul qilinganlar',d.statuses['Qabul qilingan']||0)}${stat('Ko‘rib chiqilmoqda',d.statuses['Ko‘rib chiqilmoqda']||0)}</div><div class="layout"><div class="widget"><h3>Arizalar dinamikasi (30 kun)</h3>${bars(d.days.length?d.days:[{day:new Date().toISOString().slice(0,10),count:0}])}</div><div class="widget"><h3>Arizalar holati</h3>${Object.entries(d.statuses).map(([k,v])=>`<p><span class="pill">${esc(k)}</span> <strong style="float:right">${v}</strong></p>`).join('')||'<p class="muted">Arizalar hali kelmagan</p>'}</div></div><div class="widget" style="margin-top:17px"><h3>Yo‘nalishlar bo‘yicha statistika (${d.ranks.length} ta)</h3>${table(['№','Yo‘nalish','Arizalar'],d.ranks.map((r,i)=>`<tr><td>${i+1}</td><td>${esc(r.name)}</td><td>${r.count}</td></tr>`))}</div>`}
async function applications(students = false) {
  const panel = $('#panel');
  panel.innerHTML = `<div class="toolbar"><h2>${students ? 'Qabul qilingan talabalar' : 'Arizalar'}</h2>
    <input id="search-record" type="search" maxlength="200" aria-label="Arizalarni qidirish" placeholder="Ism, telefon yoki yo‘nalish..."></div>
    <div class="widget" id="application-results"></div>
    <div class="toolbar">
      <button type="button" class="secondary" id="previous-page" disabled>← Oldingi</button>
      <span id="page-status" aria-live="polite"></span>
      <button type="button" class="secondary" id="next-page" disabled>Keyingi →</button>
    </div>`;
  const search = $('#search-record');
  const results = $('#application-results');
  const previous = $('#previous-page');
  const next = $('#next-page');
  const status = $('#page-status');
  let page = 1, revision = 0, timer;

  async function load(target) {
    const current = ++revision;
    previous.disabled = next.disabled = true;
    const query = new URLSearchParams({page: target, q: search.value.trim(), students: students ? '1' : '0'});
    try {
      const data = await api('/api/applications/search?' + query);
      if (current !== revision || !results.isConnected) return;
      page = data.page;
      const pages = Math.max(1, Math.ceil(data.total / 50));
      results.innerHTML = data.items.length ? table(
        ['ID', 'Ism familiya', 'Telefon', 'Yo‘nalish', 'Sana', 'Holat', 'Amal'],
        data.items.map(r => `<tr><td>#${r.id}</td><td>${esc(r.first_name)} ${esc(r.last_name)}</td><td>${esc(r.phone)}</td><td>${esc(r.program)}</td><td>${esc(r.created_at.slice(0,10))}</td><td>${statusSelect(r)}</td><td><button class="secondary" data-save-status="${r.id}">Saqlash</button></td></tr>`)
      ) : '<p class="muted">Ariza topilmadi.</p>';
      status.textContent = `${page} / ${pages} · ${data.total} ta ariza`;
      previous.disabled = page <= 1;
      next.disabled = page >= pages;
    } catch (err) {
      if (current !== revision || !results.isConnected) return;
      results.textContent = err.message;
      status.textContent = '';
    }
  }

  search.oninput = () => {
    clearTimeout(timer);
    revision++;
    previous.disabled = next.disabled = true;
    timer = setTimeout(() => { if (results.isConnected) load(1); }, 250);
  };
  previous.onclick = () => load(page - 1);
  next.onclick = () => load(page + 1);
  await load(1);
}
async function programs(){records=await api('/api/programs');$('#panel').innerHTML=`<div class="toolbar"><h2>Yo‘nalishlar (${records.length})</h2><button class="btn" data-new="program">+ Yo‘nalish qo‘shish</button></div><div class="widget">${table(['ID','Nomi','Holati','Amallar'],records.map(r=>`<tr><td>${r.id}</td><td>${esc(r.name)}</td><td>${r.active?'Faol':'Yashirilgan'}</td><td><button class="secondary" data-edit-program="${r.id}">Tahrirlash</button><button class="secondary" data-toggle-program="${r.id}">${r.active?'Yashirish':'Faollashtirish'}</button><button class="secondary danger" data-delete-program="${r.id}">O‘chirish</button></td></tr>`))}</div>`}
async function content(kind){records=await api('/api/content');const rows=records.filter(r=>!kind||r.kind===kind);$('#panel').innerHTML=`<div class="toolbar"><h2>${kind||'E’lonlar va yangiliklar'} (${rows.length})</h2><button class="btn" data-new="content">+ Yangi material</button></div><div class="widget">${table(['ID','Turi','Sarlavha','Holati','Amallar'],rows.map(r=>`<tr><td>${r.id}</td><td>${esc(r.kind)}</td><td>${esc(r.title)}</td><td>${r.published?'Saytda':'Qoralama'}</td><td><button class="secondary" data-edit-content="${r.id}">Tahrirlash</button><button class="secondary" data-publish="${r.id}">${r.published?'Yashirish':'Chop etish'}</button><button class="secondary danger" data-delete-content="${r.id}">O‘chirish</button></td></tr>`))}</div>`}
function editor(kind,r={}){const program=kind==='program';$('#panel').innerHTML=`<div class="toolbar"><h2>${r.id?'Tahrirlash':'Yangi '+(program?'yo‘nalish':'material')}</h2><button class="secondary" data-go="${program?'programs':'content'}">← Orqaga</button></div><div class="widget modal-form"><form id="edit-form">${!program?`<label>Material turi<select name="kind"><option ${r.kind==='E’lon'?'selected':''}>E’lon</option><option ${r.kind==='Yangilik'?'selected':''}>Yangilik</option><option ${r.kind==='Sahifa'?'selected':''}>Sahifa</option><option ${r.kind==='Reklama'?'selected':''}>Reklama</option></select></label>`:''}<label>${program?'Yo‘nalish nomi':'Sarlavha'}<input name="${program?'name':'title'}" value="${esc(program?r.name:r.title)}" required maxlength="200"></label><label>${program?'Tavsif':'Matn'}<textarea name="${program?'description':'body'}" required>${esc(program?r.description:r.body)}</textarea></label><label class="check"><input type="checkbox" name="${program?'active':'published'}" ${r.id?(program?r.active:r.published)?'checked':'':'checked'}> ${program?'Faol':'Saytda chop etish'}</label><button class="btn">Saqlash</button></form></div>`;$('#edit-form').onsubmit=async e=>{e.preventDefault();const form=e.target,d=Object.fromEntries(new FormData(form));d[program?'active':'published']=form.elements[program?'active':'published'].checked;try{await api('/api/'+(program?'programs':'content')+(r.id?'/'+r.id:''),r.id?'PATCH':'POST',d);toast('Muvaffaqiyatli saqlandi');navigate(program?'programs':'content')}catch(err){toast(err.message)}}}

async function menu(){records=await api('/api/menu');$('#panel').innerHTML=`<div class="toolbar"><h2>Menyu boshqaruvi</h2><button class="btn" data-new-menu="1">+ Tugma qo‘shish</button></div><div class="widget">${table(['Tartib','Nom','Havola','Holat','Amallar'],records.map(r=>`<tr><td>${r.position}</td><td>${esc(r.label)}</td><td>${esc(r.url)}</td><td>${r.active?'Faol':'Yashirin'}</td><td><button class="secondary" data-edit-menu="${r.id}">Tahrirlash</button><button class="secondary danger" data-delete-menu="${r.id}">O‘chirish</button></td></tr>`))}</div>`}
function menuEditor(r={}){$('#panel').innerHTML=`<h2>${r.id?'Menyuni tahrirlash':'Menyu qo‘shish'}</h2><div class="widget modal-form"><form id="menu-form"><label>Tugma nomi<input name="label" maxlength="100" required value="${esc(r.label)}"></label><label>Ichki sahifa havolasi (/ bilan boshlanadi)<input name="url" required value="${esc(r.url||'/')}"></label><label>Tartib raqami<input name="position" type="number" value="${r.position??0}"></label><label class="check"><input name="active" type="checkbox" ${r.active===0?'':'checked'}> Faol</label><button class="btn">Saqlash</button></form></div>`;$('#menu-form').onsubmit=async e=>{e.preventDefault();const f=e.target,d=Object.fromEntries(new FormData(f));d.active=f.elements.active.checked;d.position=Number(d.position);try{await api('/api/menu'+(r.id?'/'+r.id:''),r.id?'PATCH':'POST',d);toast('Menyu saqlandi');navigate('menu')}catch(err){toast(err.message)}}}
async function media(){records=await api('/api/media');$('#panel').innerHTML=`<div class="toolbar"><h2>Media kutubxona</h2><input id="upload-file" type="file" accept="image/png,image/jpeg,image/webp,image/gif"><button class="btn" data-upload="1">Rasm yuklash</button></div><div class="widget">${table(['Rasm','Fayl','Havola','Amal'],records.map(r=>`<tr><td><img src="/media/${esc(r.filename)}" alt="" style="width:85px;max-height:65px;object-fit:cover"></td><td>${esc(r.original_name)}</td><td><button class="secondary" data-copy="/media/${esc(r.filename)}">Havolani nusxalash</button></td><td><button class="secondary danger" data-delete-media="${r.id}">O‘chirish</button></td></tr>`))}</div>`}
async function uploadMedia(){const file=$('#upload-file').files[0];if(!file)throw Error('Rasmni tanlang');if(file.size>3_000_000)throw Error('Rasm 3 MB dan kichik bo‘lsin');const data=await new Promise((resolve,reject)=>{const fr=new FileReader();fr.onload=()=>resolve(String(fr.result).split(',')[1]);fr.onerror=reject;fr.readAsDataURL(file)});await api('/api/media','POST',{name:file.name,data});toast('Rasm yuklandi');navigate('media')}
async function settings(){const d=await api('/api/settings');const fields=[['site_name','Universitet nomi'],['hero_title','Bosh sahifa sarlavhasi'],['hero_subtitle','Bosh sahifa izohi'],['contact_phone','Telefon'],['contact_email','Email'],['contact_address','Manzil'],['footer_text','Pastki yozuv']];$('#panel').innerHTML=`<h2>Sayt sozlamalari</h2><div class="widget modal-form"><form id="settings-form">${fields.map(([k,l])=>`<label>${l}<input name="${k}" maxlength="1000" value="${esc(d[k])}"></label>`).join('')}<button class="btn">Saytga saqlash</button></form></div>`;$('#settings-form').onsubmit=async e=>{e.preventDefault();try{await api('/api/settings','POST',Object.fromEntries(new FormData(e.target)));toast('Sayt sozlamalari saqlandi')}catch(err){toast(err.message)}}}

async function audit(){const data=await api('/api/audit');$('#panel').innerHTML=`<h2>Faoliyat jurnali</h2><div class="widget">${table(['Vaqt','Amal'],data.map(r=>`<tr><td>${esc(r.created_at)}</td><td>${esc(r.action)}</td></tr>`))}</div>`}
async function navigate(s){section=s;$('#heading').textContent=nav.find(x=>x[0]===s)?.[1]||s;document.querySelectorAll('#sidebar button').forEach(b=>b.classList.toggle('active',b.dataset.go===s));try{if(s.startsWith('admission-'))await admissionsPanel(s);else if(s==='dashboard'||s==='statistics')await dashboard();else if(s==='applications'||s==='students')await applications(s==='students');else if(s==='programs')await programs();else if(s==='content'||s==='pages')await content(s==='pages'?'Sahifa':null);else if(s==='audit')await audit();else if(s==='menu')await menu();else if(s==='media')await media();else if(s==='settings')await settings()}catch(err){$('#panel').innerHTML=`<p class="error">${esc(err.message)}</p>`}}
document.addEventListener('click',async e=>{const b=e.target.closest('button');if(!b)return;const x=b.dataset;try{if(x.go)return navigate(x.go);if(x.newMenu)return menuEditor();if(x.editMenu)return menuEditor(records.find(r=>r.id==x.editMenu));if(x.upload)return uploadMedia();if(x.copy){await navigator.clipboard.writeText(location.origin+x.copy);return toast('Havola nusxalandi')}if(x.deleteMenu||x.deleteMedia){if(!confirm('O‘chirishni tasdiqlaysizmi?'))return;await api('/api/'+(x.deleteMenu?'menu':'media')+'/'+(x.deleteMenu||x.deleteMedia),'DELETE');toast('O‘chirildi');return navigate(section)}if(x.new)return editor(x.new);if(x.editProgram)return editor('program',records.find(r=>r.id==x.editProgram));if(x.editContent)return editor('content',records.find(r=>r.id==x.editContent));if(x.saveStatus){const select=$(`[data-status="${x.saveStatus}"]`);await api('/api/applications/'+x.saveStatus,'PATCH',{status:select.value});toast('Ariza holati saqlandi');return}if(x.toggleProgram){const r=records.find(r=>r.id==x.toggleProgram);await api('/api/programs/'+r.id,'PATCH',{active:!r.active});toast('Yangilandi');return programs()}if(x.publish){const r=records.find(r=>r.id==x.publish);await api('/api/content/'+r.id,'PATCH',{published:!r.published});toast('Yangilandi');return content(section==='pages'?'Sahifa':null)}if(x.deleteProgram||x.deleteContent){if(!confirm('Rostdan ham o‘chirasizmi?'))return;const kind=x.deleteProgram?'programs':'content',id=x.deleteProgram||x.deleteContent;await api('/api/'+kind+'/'+id,'DELETE');toast('O‘chirildi');return navigate(section)}}catch(err){toast(err.message)}});
async function startAdmin(){
  try {
    const s = await api('/api/session');
    if (!s.logged_in) return showAdminLogin();
    csrf = s.csrf;
    $('#sidebar').innerHTML = nav.map(([id,label]) => `<button data-go="${id}">${label}</button>`).join('');
    $('#logout').onclick = async () => {
      try { await api('/api/logout','POST',{}); location.reload(); }
      catch (err) { toast(err.message); }
    };
    await navigate('dashboard');
  } catch (err) {
    $('#panel').innerHTML = `<p class="error">${esc(err.message)}</p>`;
  }
}
function showAdminLogin(message=''){
  $('#sidebar').innerHTML = '';
  $('#heading').textContent = 'Administratorga kirish';
  $('#logout').style.display = 'none';
  $('#panel').innerHTML = `
    <div class="widget modal-form" style="max-width:480px;margin:50px auto">
      <h2>ISFT Admin Panel</h2>
      <p class="muted">Davom etish uchun administrator login va parolini kiriting.</p>
      <form id="admin-login-form">
        <label>Login<input name="username" autocomplete="username" required value="admin"></label>
        <label>Parol<input name="password" type="password" autocomplete="current-password" required></label>
        <p class="error" id="admin-login-error">${esc(message)}</p>
        <button class="btn" type="submit">Kirish</button>
      </form>
      <p class="muted"><a href="/">← Asosiy saytga qaytish</a></p>
    </div>`;
  $('#admin-login-form').onsubmit = async e => {
    e.preventDefault();
    const form = e.target;
    const button = form.querySelector('button[type="submit"]');
    const error = $('#admin-login-error');
    button.disabled = true;
    button.textContent = 'Tekshirilmoqda...';
    error.textContent = '';
    try {
      const data = Object.fromEntries(new FormData(form));
      await api('/api/login','POST',data);
      $('#logout').style.display = '';
      await startAdmin();
    } catch (err) {
      error.textContent = err.message || 'Login yoki parol xato';
      button.disabled = false;
      button.textContent = 'Kirish';
    }
  };
}
startAdmin();
