nav.splice(4,0,['admission-people','Ro‘yxatdan o‘tganlar'],['admission-requests','Testga arizalar'],['admission-results','Test topshirganlar'],['admission-tests','Test va qabul sozlamalari']);
let admissionData;
async function admissionsPanel(view) {
  admissionData=await api('/api/admissions/overview');
  const panel=$('#panel');
  const notice=`<p class="notice">${admissionData.sync.configured?'Google ulangan':'Google hali ulanmagan. GOOGLE_SHEETS.bat orqali ulang.'} ${esc(admissionData.sync.error)}</p><p class="notice">Google jadvaliga yuborishni kutayotgan yozuvlar: ${admissionData.pending_exports}</p>`;
  if(view==='admission-people') panel.innerHTML='<h2>Ro‘yxatdan o‘tganlar</h2>'+notice+table(['Ism','Google pochta','Sana'],admissionData.people.map(r=>`<tr><td>${esc(r.name)}</td><td>${esc(r.email)}</td><td>${esc(r.created_at)}</td></tr>`));
  if(view==='admission-requests') panel.innerHTML='<h2>Testga arizalar</h2><p>Arizani tekshirib, imtihon topshirishga ruxsat bering.</p>'+notice+table(['Ism','Pochta','Yo‘nalish','Holat','Amal'],admissionData.requests.map(r=>`<tr><td>${esc(r.name)}</td><td>${esc(r.email)}</td><td>${esc(r.program)}</td><td>${esc(r.status)}</td><td><button class="btn" data-permit="${r.id}">Ruxsat berish</button> <button class="secondary" data-reject="${r.id}">Rad etish</button></td></tr>`));
  if(view==='admission-results') panel.innerHTML='<h2>Test topshirganlar</h2>'+notice+table(['Ism','Yo‘nalish','Ball','Natija','Javoblar'],admissionData.attempts.map(r=>`<tr><td>${esc(r.name)}<br>${esc(r.email)}</td><td>${esc(r.program_name)}</td><td>${r.percent??'—'}%</td><td>${r.finished===null?'Ishlamoqda':r.passed?'O‘tdi':'O‘tmadi'}</td><td><button class="secondary" data-exam-detail="${r.id}">Ko‘rish</button></td></tr>`));
  if(view==='admission-tests') panel.innerHTML='<h2>Test va qabul sozlamalari</h2><p>Har yo‘nalish uchun savollar, o‘tish bali, joylar soni va qabul holatini belgilang. Imtihon davomiyligi 90 daqiqa.</p>'+table(['Yo‘nalish','Qabul','Test','Savollar','Amal'],admissionData.programs.map(r=>`<tr><td>${esc(r.name)}</td><td>${r.admission_open?'Ochiq':'Yopiq'}</td><td>${r.published?'Ochiq':'Qoralama'}</td><td>${JSON.parse(r.questions||'[]').length}</td><td><button class="btn" data-test-edit="${r.id}">Sozlash</button></td></tr>`));
}
function questionFields(q,index) {
  return `<fieldset class="question editor-question"><legend>Savol ${index+1}</legend><label>Savol matni<textarea class="question-text" required maxlength="1000">${esc(q.text)}</textarea></label><div class="answer-editor">${q.options.map((value,i)=>`<label>${'ABCD'[i]} javob<input class="question-option" value="${esc(value)}" required maxlength="500"></label>`).join('')}</div><label>To‘g‘ri javob<select class="question-correct">${q.options.map((_,i)=>`<option value="${i}" ${i===q.correct?'selected':''}>${'ABCD'[i]}</option>`).join('')}</select></label><button class="secondary" type="button" data-remove-question>Bu savolni o‘chirish</button></fieldset>`;
}
function editExam(id) {
  const r=admissionData.programs.find(p=>p.id===id);
  const questions=JSON.parse(r.questions||'[]');
  $('#panel').innerHTML=`<button class="secondary" data-go="admission-tests">← Orqaga</button><h2>${esc(r.name)}</h2><p class="notice">Boshlang‘ich savollar qoralama. Matn va to‘g‘ri javoblarni tekshirib, keyin testni oching. Boshlangan imtihonlarga bu o‘zgarishlar ta’sir qilmaydi.</p>
    <form id="exam-editor"><div class="widget exam-settings"><label class="check"><input type="checkbox" name="admission_open" ${r.admission_open?'checked':''}> Qabul ochiq</label><label>Joylar soni (bo‘sh bo‘lsa cheklanmagan)<input type="number" name="capacity" min="0" value="${r.capacity??''}"></label><label>O‘tish bali (%)<input type="number" name="pass_percent" required min="1" max="100" value="${r.pass_percent??60}"></label><label class="check"><input type="checkbox" name="published" ${r.published?'checked':''}> Testni abituriyentlarga ochish</label><p>90 daqiqa · Har savol teng ball</p></div><div id="question-editor">${questions.map(questionFields).join('')}</div><button type="button" class="secondary" id="add-question">+ Savol qo‘shish</button> <button class="btn">Sozlamalar va savollarni saqlash</button><p id="exam-save-message" role="status"></p></form>`;
  $('#add-question').onclick=()=>$('#question-editor').insertAdjacentHTML('beforeend',questionFields({text:'',options:['','','',''],correct:0},document.querySelectorAll('.editor-question').length));
  $('#exam-editor').onsubmit=async event=>{
    event.preventDefault();
    const f=event.target;
    const questions=[...document.querySelectorAll('.editor-question')].map(el=>({text:el.querySelector('.question-text').value.trim(),options:[...el.querySelectorAll('.question-option')].map(x=>x.value.trim()),correct:Number(el.querySelector('.question-correct').value)}));
    try {
      await api('/api/admissions/config','POST',{program_id:id,admission_open:f.elements.admission_open.checked,published:f.elements.published.checked,capacity:f.elements.capacity.value===''?null:Number(f.elements.capacity.value),pass_percent:Number(f.elements.pass_percent.value),questions});
      $('#exam-save-message').textContent='Saqlandi. Savollar va qabul holati yangilandi.';
    } catch(error) {$('#exam-save-message').textContent=error.message;}
  };
}
document.addEventListener('click',async event=>{
  const b=event.target.closest('button');
  if(!b) return;
  try {
    if(b.hasAttribute('data-remove-question')) b.closest('.editor-question').remove();
    if(b.dataset.testEdit) editExam(Number(b.dataset.testEdit));
    if(b.dataset.permit || b.dataset.reject) {
      await api('/api/admissions/permission','POST',{id:Number(b.dataset.permit||b.dataset.reject),status:b.dataset.permit?'Ruxsat berilgan':'Rad etilgan'});
      await admissionsPanel('admission-requests');
    }
    if(b.dataset.examDetail) {
      const r=await api('/api/admissions/detail?id='+b.dataset.examDetail);
      $('#panel').innerHTML=`<button class="secondary" data-go="admission-results">← Natijalarga</button><h2>${esc(r.program_name)}</h2><p>${r.correct??'—'} ta to‘g‘ri · ${r.percent??'—'}%</p>`+r.questions.map((q,i)=>`<article class="question"><h3>${i+1}. ${esc(q.text)}</h3><p>Tanlangan javob: <strong>${esc(q.options[r.answers[String(i)]]??'Belgilanmagan')}</strong></p><p>To‘g‘ri javob: ${esc(q.options[q.correct])}</p></article>`).join('');
    }
  } catch(error) {toast(error.message);}
});
