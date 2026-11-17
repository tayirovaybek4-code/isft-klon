let studentCsrf = '', attempt = null, timer = null, saving = Promise.resolve(), clockOffset = 0;
const examRoot = document.querySelector('#exam-root');
const safe = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function studentApi(path, data) {
  const response = await fetch('/api/student/' + path, {method:data ? 'POST' : 'GET',
    headers:{'Content-Type':'application/json','X-CSRF-Token':studentCsrf}, body:data ? JSON.stringify(data) : undefined});
  const result = await response.json();
  if (!response.ok) throw Error(result.error || 'Ulanishda xatolik');
  return result;
}
function showError(error) {
  const box = document.querySelector('#exam-error');
  if (box) box.textContent = error.message;
}
async function home() {
  clearInterval(timer);
  const session = await studentApi('session');
  if (!session.person) {
    examRoot.innerHTML = `<section class="exam-welcome"><span class="eyebrow">ONLAYN IMTIHON</span>
      <h1>Kelajagingiz sari birinchi qadam</h1><p>Google orqali kiring, yo‘nalishni tanlang va testga ariza bering.</p>
      <div class="exam-steps"><p>01 · Ro‘yxatdan o‘ting</p><p>02 · Testga ruxsat oling</p><p>03 · 28 ta savol · 90 daqiqa</p></div>
      ${session.google_configured ? '<a class="btn" href="/auth/google/start">Google orqali kirish →</a>' : '<p class="notice">Google orqali kirish sozlanmoqda. Qabul bo‘limiga murojaat qiling.</p>'}</section>`;
    return;
  }
  studentCsrf = session.person.csrf;
  const data = await studentApi('home');
  examRoot.innerHTML = `<div class="toolbar"><div><span class="eyebrow">SHAXSIY KABINET</span><h1>${safe(session.person.name)}</h1><p>${safe(session.person.email)}</p></div><button class="secondary" id="student-logout">Chiqish</button></div>
    <p id="exam-error" class="error" role="alert"></p><h2>Testga arizalarim</h2><div class="exam-request-list">
    ${data.requests.map(r=>`<article class="card"><h3>${safe(r.name || 'Yo‘nalish')}</h3><p>${safe(r.status)}</p>
      ${r.attempt_id || r.status==='Ruxsat berilgan' ? `<button class="btn" data-start="${r.id}">${r.attempt_id ? 'Imtihon / natijani ko‘rish' : 'Imtihonni boshlash'}</button>` : '<p>Arizangizni qabul bo‘limi ko‘rib chiqadi.</p>'}</article>`).join('') || '<p>Hali testga ariza bermadingiz.</p>'}</div>
    <h2>Yo‘nalishni tanlang</h2><p>Imtihon bir marta topshiriladi. Boshlangandan so‘ng 90 daqiqa davom etadi. Vaqt tugaganda saqlangan javoblar tekshiriladi.</p>
    <div class="program-grid">${data.programs.map(p=>{
      const closed = !p.admission_open || (p.capacity!==null && p.reserved>=p.capacity);
      const requested = data.requests.some(r=>r.program_id===p.id);
      return `<article class="card"><h3>${safe(p.name)}</h3><p>${closed ? 'Qabul yopiq / joylar to‘lgan' : 'Qabul ochiq'}</p><button class="btn" data-request="${p.id}" ${closed || requested ? 'disabled':''}>${requested ? 'Ariza berilgan' : 'Testga ariza berish'}</button></article>`;
    }).join('')}</div>`;
  document.querySelector('#student-logout').onclick = async()=>{await studentApi('logout',{}); await home();};
}
function renderAttempt(data) {
  attempt = data;
  clockOffset = data.server_time * 1000 - Date.now();
  clearInterval(timer);
  if (data.finished !== null) {
    examRoot.innerHTML = `<section class="exam-result ${data.passed?'passed':''}"><span class="eyebrow">IMTIHON NATIJASI</span><h1>${safe(data.message)}</h1>
      <div class="result-score">${data.correct} / ${data.questions.length}</div><p>${data.percent}% · O‘tish chegarasi ${data.pass_percent}%</p><p>${safe(data.program_name)}</p><a class="btn" href="/exam.html">Kabinetga qaytish</a></section>`;
    return;
  }
  examRoot.innerHTML = `<div class="exam-clock"><strong>${safe(data.program_name)}</strong><span id="countdown" role="timer"></span><span id="save-state" aria-live="polite">Javoblar avtomatik saqlanadi</span></div>
    <p id="exam-error" class="error" role="alert"></p><form id="exam-form">${data.questions.map((q,i)=>`<fieldset class="question"><legend>${i+1}. ${safe(q.text)}</legend>${q.options.map((option,j)=>`<label><input type="radio" name="q${i}" value="${j}" ${data.answers[String(i)]===j?'checked':''}> <span>${safe(option)}</span></label>`).join('')}</fieldset>`).join('')}
    <button class="btn" id="finish-exam">Imtihonni yakunlash</button></form>`;
  document.querySelector('#exam-form').onchange = event=>{
    const key = event.target.name.slice(1), value = Number(event.target.value);
    attempt.answers[key] = value;
    const snapshot = {...attempt.answers};
    document.querySelector('#save-state').textContent='Saqlanmoqda…';
    saving = saving.catch(()=>{}).then(async()=>{
      const result = await studentApi('attempt',{id:attempt.id,answers:snapshot});
      if (result.finished!==null) renderAttempt(result);
      else if (document.querySelector('#save-state')) document.querySelector('#save-state').textContent='Javoblar saqlandi';
    }).catch(error=>{showError(error); if(document.querySelector('#save-state')) document.querySelector('#save-state').textContent='Saqlanmadi. Ulanishni tekshiring.';});
  };
  document.querySelector('#exam-form').onsubmit=async event=>{
    event.preventDefault();
    if (!confirm('Imtihonni yakunlaysizmi? Keyin javoblarni o‘zgartirib bo‘lmaydi.')) return;
    document.querySelector('#finish-exam').disabled=true;
    try { await saving; renderAttempt(await studentApi('attempt',{id:attempt.id,answers:attempt.answers,finish:true})); }
    catch(error) { showError(error); if(document.querySelector('#finish-exam')) document.querySelector('#finish-exam').disabled=false; }
  };
  let checking = false;
  async function tick() {
    const seconds = Math.max(0,Math.ceil(attempt.deadline-(Date.now()+clockOffset)/1000));
    const label = document.querySelector('#countdown');
    if(label) label.textContent = `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
    if (seconds===0 && !checking) {
      checking=true;
      document.querySelectorAll('#exam-form input, #exam-form button').forEach(el=>el.disabled=true);
      try { renderAttempt(await studentApi('attempt?id='+attempt.id)); }
      catch(error) {showError(error); checking=false;}
    }
  }
  timer=setInterval(tick,1000); tick();
}
examRoot.addEventListener('click',async event=>{
  const button=event.target.closest('button');
  if(!button) return;
  try {
    if(button.dataset.request) {button.disabled=true; await studentApi('request',{program_id:Number(button.dataset.request)}); await home();}
    if(button.dataset.start) {
      if(button.textContent==='Imtihonni boshlash' && !confirm('Tayyormisiz? Boshlagach 90 daqiqalik hisob boshlanadi.')) return;
      button.disabled=true;
      renderAttempt(await studentApi('start',{request_id:Number(button.dataset.start)}));
    }
  } catch(error) {button.disabled=false;showError(error);}
});
home().catch(error=>{examRoot.textContent=error.message;});
