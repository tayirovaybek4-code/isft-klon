import admissions
import os, sqlite3, json, secrets, hashlib, hmac, mimetypes, re, time, base64, uuid, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie
from pathlib import Path
from datetime import date, datetime

ROOT=Path(__file__).resolve().parent; DB=ROOT/'isft.db'; STATIC=ROOT/'static'; UPLOAD=ROOT/'uploads'; UPLOAD.mkdir(exist_ok=True)
PROGRAMS=['Axborot tizimlari va texnologiyalari','Iqtisodiyot','Marketing','Bank ishi','Axborot xavfsizligi','Xalqaro munosabatlar','Menejment','Biznes va menejment','Moliya sohasida boshqaruv','Buxgalteriya hisobi va moliya','Xorijiy til va adabiyoti','Maktabgacha ta’lim','Boshlang‘ich ta’lim','Pedagogika','Psixologiya','Filologiya va tillarni o‘qitish (Ingliz tili)']
MAX_BODY=6*1024*1024
LOGIN_ATTEMPTS={}; LOGIN_LOCK=threading.Lock()
APPLICATION_ATTEMPTS={}; APPLICATION_LOCK=threading.Lock()

def connect():
 c=sqlite3.connect(DB,timeout=15); c.row_factory=sqlite3.Row; c.execute('PRAGMA journal_mode=WAL'); return c

def init():
 with connect() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, salt TEXT, digest TEXT); CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL, father_name TEXT, phone TEXT NOT NULL, birth_date TEXT, program TEXT NOT NULL, study_type TEXT, status TEXT DEFAULT 'Yangi', created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS content(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL, published INTEGER DEFAULT 0, created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS programs(id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '', active INTEGER DEFAULT 1); CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, action TEXT, created_at TEXT); CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires REAL NOT NULL); CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS menu(id INTEGER PRIMARY KEY, label TEXT NOT NULL, url TEXT NOT NULL, position INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1); CREATE TABLE IF NOT EXISTS media(id INTEGER PRIMARY KEY, filename TEXT NOT NULL, original_name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, created_at TEXT NOT NULL);''')
  c.execute('BEGIN IMMEDIATE')
  legacy_schema='program_id' not in {column['name'] for column in c.execute('PRAGMA table_info(applications)')}
  if not c.execute('SELECT COUNT(*) FROM programs').fetchone()[0] and (legacy_schema or not c.execute('SELECT 1 FROM applications WHERE program_id IS NOT NULL LIMIT 1').fetchone()):
   c.executemany('INSERT INTO programs(name) VALUES(?)',[(x,) for x in PROGRAMS])
  if legacy_schema:
   c.execute('ALTER TABLE applications ADD COLUMN program_id INTEGER')
   c.execute('''UPDATE applications SET program_id=(
    SELECT MIN(id) FROM programs WHERE name=applications.program HAVING COUNT(*)=1
   )''')
  c.execute('CREATE INDEX IF NOT EXISTS applications_program_id ON applications(program_id)')
  if not c.execute('SELECT COUNT(*) FROM menu').fetchone()[0]: c.executemany('INSERT INTO menu(label,url,position) VALUES(?,?,?)',[(x,y,i) for i,(x,y) in enumerate([('Bosh sahifa','/'),('Universitet','/about.html'),('Yo‘nalishlar','/programs.html'),('Yangiliklar','/news.html'),('Qabul','/apply.html'),('Aloqa','/contact.html')])])
  if not c.execute('SELECT COUNT(*) FROM settings').fetchone()[0]: c.executemany('INSERT INTO settings(key,value) VALUES(?,?)',[('hero_title','Bilimdan boshlanadi. Hayotda davom etadi.'),('hero_subtitle','Ta’lim yo‘nalishlari bilan tanishing va onlayn ariza topshiring.'),('contact_phone',''),('contact_address',''),('contact_email',''),('footer_text','© ISFT Universiteti'),('site_name','ISFT Universiteti')])
  if not c.execute('SELECT COUNT(*) FROM users').fetchone()[0]:
   pwd=os.getenv('ADMIN_PASSWORD','')
   if len(pwd)<12: raise SystemExit('Birinchi ishga tushirishda ADMIN_PASSWORD kamida 12 belgidan iborat bo‘lishi shart. README ni o‘qing.')
   salt=secrets.token_hex(16); dig=hashlib.pbkdf2_hmac('sha256',pwd.encode(),bytes.fromhex(salt),310000).hex(); c.execute('INSERT INTO users(username,salt,digest) VALUES(?,?,?)',('admin',salt,dig))

def now(): return datetime.now().isoformat(timespec='seconds')
def audit(c,action): c.execute('INSERT INTO audit(action,created_at) VALUES(?,?)',(action,now()))

class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args): pass
 def send(self,status=200,obj=None,ctype='application/json; charset=utf-8',headers=None):
  data=json.dumps(obj,ensure_ascii=False).encode() if not isinstance(obj,bytes) else obj
  self.send_response(status); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY'); self.send_header('Referrer-Policy','no-referrer'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"); self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()');
  for k,v in (headers or {}).items(): self.send_header(k,v)
  self.end_headers(); self.wfile.write(data)
 def session(self):
  ck=SimpleCookie()
  try: ck.load(self.headers.get('Cookie',''))
  except Exception: return None
  sid=ck.get('sid')
  if not sid: return None
  token=hashlib.sha256(sid.value.encode()).hexdigest()
  with connect() as c: item=c.execute('SELECT csrf,expires FROM sessions WHERE token_hash=?',(token,)).fetchone()
  if not item or item['expires']<time.time(): return None
  return dict(item)
 def require(self,write=False):
  s=self.session()
  if not s: self.send(401,{'error':'Administrator sifatida kiring'}); return False
  if write and self.headers.get('X-CSRF-Token')!=s['csrf']: self.send(403,{'error':'CSRF tekshiruvi muvaffaqiyatsiz'}); return False
  return True
 def payload(self):
  n=int(self.headers.get('Content-Length','0'))
  if n<1 or n>MAX_BODY: raise ValueError('Ma’lumot hajmi noto‘g‘ri')
  if 'application/json' not in self.headers.get('Content-Type',''): raise ValueError('JSON yuboring')
  data=json.loads(self.rfile.read(n))
  if not isinstance(data,dict): raise ValueError('JSON obyekt yuboring')
  return data
 def do_GET(self):
  if admissions.handle(self,connect,'GET'): return
  p=urlparse(self.path); path=p.path
  if path=='/api/session':
   s=self.session(); return self.send(200,{'logged_in':bool(s),'csrf':s['csrf'] if s else None})
  if path=='/api/public/programs':
   with connect() as c: rows=c.execute('''SELECT p.id,p.name,p.description,COALESCE(c.admission_open,0) admission_open,c.capacity,
     (SELECT COUNT(*) FROM exam_requests r WHERE r.program_id=p.id AND r.status!='Rad etilgan') reserved
     FROM programs p LEFT JOIN exam_configs c ON c.program_id=p.id WHERE p.active=1 ORDER BY p.id''').fetchall()
   return self.send(200,[dict(r) for r in rows])
  if path=='/api/public/settings':
   with connect() as c: return self.send(200,{r['key']:r['value'] for r in c.execute('SELECT * FROM settings')})
  if path=='/api/public/menu':
   with connect() as c: return self.send(200,[dict(r) for r in c.execute('SELECT id,label,url,position FROM menu WHERE active=1 ORDER BY position,id')])
  if path=='/api/public/content':
   with connect() as c: rows=c.execute('SELECT id,kind,title,body,created_at FROM content WHERE published=1 ORDER BY id DESC').fetchall()
   return self.send(200,[dict(r) for r in rows])
  if path.startswith('/api/'):
   if not self.require(): return
   with connect() as c:
    if path=='/api/settings': return self.send(200,{r['key']:r['value'] for r in c.execute('SELECT * FROM settings')})
    if path=='/api/menu': return self.send(200,[dict(r) for r in c.execute('SELECT * FROM menu ORDER BY position,id')])
    if path=='/api/media': return self.send(200,[dict(r) for r in c.execute('SELECT * FROM media ORDER BY id DESC')])
    if path=='/api/dashboard':
     total=c.execute('SELECT COUNT(*) FROM applications').fetchone()[0]; today=c.execute('SELECT COUNT(*) FROM applications WHERE substr(created_at,1,10)=?',(now()[:10],)).fetchone()[0]
     statuses={r['status']:r['n'] for r in c.execute('SELECT status,COUNT(*) n FROM applications GROUP BY status')}
     ranks=[dict(r) for r in c.execute('SELECT p.name,COUNT(a.id) count FROM programs p LEFT JOIN applications a ON a.program_id=p.id GROUP BY p.id ORDER BY count DESC,p.id')]
     days=[dict(r) for r in c.execute("SELECT substr(created_at,1,10) day,COUNT(*) count FROM applications WHERE created_at>=date('now','-29 days') GROUP BY day ORDER BY day")]
     return self.send(200,{'total':total,'today':today,'statuses':statuses,'ranks':ranks,'days':days})
    if path=='/api/applications/search':
     query=parse_qs(p.query)
     try: page=min(max(int(query.get('page',['1'])[0]),1),1_000_000)
     except ValueError: return self.send(400,{'error':'Sahifa raqami noto‘g‘ri'})
     status='Qabul qilingan' if query.get('students')==['1'] else None
     search=query.get('q',[''])[0].casefold()[:200]
     c.create_function('matches_search',-1,lambda *values: search in ' '.join(str(v) for v in values).casefold())
     where='WHERE (? IS NULL OR status=?) AND matches_search(id,first_name,last_name,father_name,phone,program,status,created_at)'
     params=(status,status)
     c.execute('BEGIN')
     total=c.execute(f'SELECT COUNT(*) FROM applications {where}',params).fetchone()[0]
     page=min(page,max(1,(total+49)//50))
     rows=c.execute(f'SELECT * FROM applications {where} ORDER BY id DESC LIMIT 50 OFFSET ?',(*params,(page-1)*50))
     return self.send(200,{'items':[dict(r) for r in rows],'total':total,'page':page})
    if path=='/api/applications': rows=c.execute('SELECT * FROM applications ORDER BY id DESC LIMIT 1000').fetchall()
    elif path=='/api/programs': rows=c.execute('SELECT * FROM programs ORDER BY id').fetchall()
    elif path=='/api/content': rows=c.execute('SELECT * FROM content ORDER BY id DESC').fetchall()
    elif path=='/api/audit': rows=c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100').fetchall()
    else: return self.send(404,{'error':'API topilmadi'})
    return self.send(200,[dict(r) for r in rows])
  if path.startswith('/media/'):
   name=path.split('/')[-1]
   if not re.fullmatch(r'[a-f0-9]{32}\.(png|jpg|webp|gif)',name): return self.send(404,b'Not found','text/plain')
   file=UPLOAD/name
   if not file.is_file(): return self.send(404,b'Not found','text/plain')
   return self.send(200,file.read_bytes(),mimetypes.guess_type(name)[0] or 'application/octet-stream')
  if path=='/': path='/index.html'
  file=(STATIC/path.lstrip('/')).resolve()
  if STATIC.resolve() not in file.parents or not file.is_file(): return self.send(404,b'Not found','text/plain')
  return self.send(200,file.read_bytes(),mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
 def do_POST(self):
  if admissions.handle(self,connect,'POST'): return
  path=urlparse(self.path).path
  try: d=self.payload()
  except (ValueError,TypeError,json.JSONDecodeError) as e: return self.send(400,{'error':str(e)})
  if path=='/api/login':
   ip=self.client_address[0]; t=time.time()
   with LOGIN_LOCK:
    attempts=[v for v in LOGIN_ATTEMPTS.get(ip,[]) if t-v<900]
    LOGIN_ATTEMPTS[ip]=attempts
    if len(attempts)>=8: return self.send(429,{'error':'Ko‘p urinish. 15 daqiqadan keyin qayta urinib ko‘ring'})
    attempts.append(t)
   username=str(d.get('username',''))[:80]; pwd=str(d.get('password',''))
   with connect() as c: row=c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
   if not row: time.sleep(.3); return self.send(401,{'error':'Login yoki parol xato'})
   dig=hashlib.pbkdf2_hmac('sha256',pwd.encode(),bytes.fromhex(row['salt']),310000).hex()
   if not hmac.compare_digest(dig,row['digest']): time.sleep(.3); return self.send(401,{'error':'Login yoki parol xato'})
   sid=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24)
   with connect() as c: c.execute('INSERT INTO sessions(token_hash,csrf,expires) VALUES(?,?,?)',(hashlib.sha256(sid.encode()).hexdigest(),csrf,time.time()+8*3600))
   with LOGIN_LOCK: LOGIN_ATTEMPTS.pop(ip,None)
   secure='; Secure' if os.getenv('ISFT_HTTPS','0')=='1' else ''
   return self.send(200,{'ok':True,'csrf':csrf},headers={'Set-Cookie':f'sid={sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}'})
  if path=='/api/apply':
   try: applicant=admissions.student(self,connect,write=True)
   except admissions.AdmissionError as exc: return self.send(exc.status,{'error':str(exc)})
   ip=self.client_address[0]; cutoff=time.monotonic()-60
   with APPLICATION_LOCK:
    for address,attempts in list(APPLICATION_ATTEMPTS.items()):
     recent=[attempt for attempt in attempts if attempt>cutoff]
     if recent: APPLICATION_ATTEMPTS[address]=recent
     else: del APPLICATION_ATTEMPTS[address]
    attempts=APPLICATION_ATTEMPTS.setdefault(ip,[])
    limited=len(attempts)>=10
    if not limited: attempts.append(time.monotonic())
   if limited: return self.send(429,{'error':'Ariza yuborish urinishlari ko‘p. Bir daqiqadan keyin qayta urinib ko‘ring.'},headers={'Retry-After':'60'})
   fields=('first_name','last_name','father_name','phone','birth_date','program','study_type')
   if any(not isinstance(d.get(key,''),str) for key in fields):
    return self.send(400,{'error':'Ariza maydonlari matn bo‘lishi kerak'})
   vals={key:d.get(key,'').strip() for key in fields}
   phone=vals['phone']
   digits=re.sub(r'[ ()+-]','',phone)
   if not (2<=len(vals['first_name'])<=100 and 2<=len(vals['last_name'])<=100 and len(vals['father_name'])<=100
           and re.fullmatch(r'\+?[0-9 ()-]{9,22}',phone) and 9<=len(digits)<=15):
    return self.send(400,{'error':'Ism, familiya, otasining ismi yoki telefon noto‘g‘ri'})
   birth_date=vals['birth_date']
   if birth_date:
    try:
     if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',birth_date) or date.fromisoformat(birth_date)>date.today():
      raise ValueError
    except ValueError: return self.send(400,{'error':'Tug‘ilgan sana noto‘g‘ri'})
   if vals['study_type'] not in ('','Kunduzgi','Sirtqi','Kechki'):
    return self.send(400,{'error':'Ta’lim shakli noto‘g‘ri'})
   program_id=d.get('program_id')
   if program_id is not None and (type(program_id) is not int or not 1<=program_id<=2**63-1):
    return self.send(400,{'error':'Yo‘nalishni tanlang'})
   with connect() as c:
    c.execute('BEGIN IMMEDIATE')
    selected=c.execute('SELECT p.id,c.admission_open FROM programs p LEFT JOIN exam_configs c ON c.program_id=p.id WHERE (? IS NULL AND p.name=?) OR p.id=? ORDER BY p.id LIMIT 1',(program_id,vals['program'],program_id)).fetchone()
    if not selected: return self.send(400,{'error':'Yo‘nalishni tanlang'})
    if not selected['admission_open']: return self.send(409,{'error':'Bu yo‘nalish uchun qabul yopilgan.'})
    try:
     admissions.route(c,'/api/student/request','POST',{'program_id':selected['id']},{},applicant)
    except admissions.AdmissionError as exc: return self.send(exc.status,{'error':str(exc)})
    previous=c.execute('SELECT id FROM applications WHERE applicant_id=? AND program_id=?',(applicant['id'],selected['id'])).fetchone()
    if previous: return self.send(200,{'ok':True,'application_id':previous['id']})
    cur=c.execute('''INSERT INTO applications(first_name,last_name,father_name,phone,birth_date,program,study_type,created_at,program_id)
     SELECT ?,?,?,?,?,name,?,?,id FROM programs
     WHERE active=1 AND ((? IS NULL AND name=?) OR id=?) ORDER BY id LIMIT 1''',
     (*(vals[key] for key in fields[:5]),vals['study_type'],now(),program_id,vals['program'],program_id))
    if not cur.rowcount: return self.send(400,{'error':'Yo‘nalishni tanlang'})
    c.execute('UPDATE applications SET applicant_id=? WHERE id=?',(applicant['id'],cur.lastrowid))
    vals['program']=c.execute('SELECT program FROM applications WHERE id=?',(cur.lastrowid,)).fetchone()[0]
    admissions.export(c,'Qabul arizalari',cur.lastrowid,[cur.lastrowid,applicant['email'],*vals.values(),now()])
   return self.send(201,{'ok':True,'application_id':cur.lastrowid})
  if not self.require(write=True): return
  with connect() as c:
   if path=='/api/logout':
    ck=SimpleCookie(); ck.load(self.headers.get('Cookie','')); sid=ck.get('sid'); c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(sid.value.encode()).hexdigest(),)) if sid else None
    return self.send(200,{'ok':True},headers={'Set-Cookie':'sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
   if path=='/api/settings':
    allowed={'hero_title','hero_subtitle','contact_phone','contact_address','contact_email','footer_text','site_name'}
    if not isinstance(d,dict) or any(k not in allowed or not isinstance(v,str) or len(v)>1000 for k,v in d.items()): return self.send(400,{'error':'Sozlamalar noto‘g‘ri'})
    for k,v in d.items(): c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,v.strip()))
    audit(c,'Sayt sozlamalari yangilandi'); return self.send(200,{'ok':True})
   if path=='/api/menu':
    label=str(d.get('label','')).strip()[:100]; url=str(d.get('url','')).strip()[:200]
    if not label or not re.fullmatch(r'/[a-zA-Z0-9_/?=&.%-]*',url) or url.startswith('//'): return self.send(400,{'error':'Menyu nomi yoki havola noto‘g‘ri'})
    cur=c.execute('INSERT INTO menu(label,url,position,active) VALUES(?,?,?,?)',(label,url,int(d.get('position',0)),int(bool(d.get('active',True))))); audit(c,'Menyu qo‘shildi'); return self.send(201,{'id':cur.lastrowid})
   if path=='/api/media':
    raw=d.get('data',''); name=str(d.get('name',''))[:200]
    if not isinstance(raw,str) or len(raw)>5_000_000: return self.send(400,{'error':'Fayl juda katta'})
    try: data=base64.b64decode(raw,validate=True)
    except Exception: return self.send(400,{'error':'Fayl kodlanishi noto‘g‘ri'})
    if not data or len(data)>3_000_000: return self.send(400,{'error':'Rasm 3 MB dan kichik bo‘lsin'})
    if data.startswith(b'\x89PNG\r\n\x1a\n'): ext,mime='png','image/png'
    elif data.startswith(b'\xff\xd8\xff'): ext,mime='jpg','image/jpeg'
    elif data.startswith(b'RIFF') and data[8:12]==b'WEBP': ext,mime='webp','image/webp'
    elif data.startswith((b'GIF87a',b'GIF89a')): ext,mime='gif','image/gif'
    else: return self.send(400,{'error':'Faqat PNG, JPG, WEBP yoki GIF rasm yuklang'})
    filename=uuid.uuid4().hex+'.'+ext; (UPLOAD/filename).write_bytes(data)
    cur=c.execute('INSERT INTO media(filename,original_name,mime,size,created_at) VALUES(?,?,?,?,?)',(filename,name,mime,len(data),now())); audit(c,'Rasm yuklandi'); return self.send(201,{'id':cur.lastrowid,'url':'/media/'+filename})
   if path=='/api/content':
    kind=str(d.get('kind',''))
    if kind not in ('E’lon','Yangilik','Sahifa','Reklama'): return self.send(400,{'error':'Tur noto‘g‘ri'})
    title=str(d.get('title','')).strip()[:200]; body=str(d.get('body','')).strip()[:10000]
    if not title or not body: return self.send(400,{'error':'Sarlavha va matnni kiriting'})
    cur=c.execute('INSERT INTO content(kind,title,body,published,created_at) VALUES(?,?,?,?,?)',(kind,title,body,int(bool(d.get('published'))),now())); audit(c,f'{kind} qo‘shildi #{cur.lastrowid}')
    return self.send(201,{'id':cur.lastrowid})
   if path=='/api/programs':
    name=str(d.get('name','')).strip()[:200]
    if not name: return self.send(400,{'error':'Nom kiriting'})
    cur=c.execute('''INSERT INTO programs(id,name,description)
     SELECT MAX(COALESCE((SELECT MAX(id) FROM programs),0),
                COALESCE((SELECT MAX(program_id) FROM applications),0))+1,?,?''',
     (name,str(d.get('description',''))[:4000]))
    audit(c,f'Yo‘nalish qo‘shildi #{cur.lastrowid}'); return self.send(201,{'id':cur.lastrowid})
  return self.send(404,{'error':'API topilmadi'})
 def do_PATCH(self):
  if not self.require(write=True): return
  try: d=self.payload()
  except Exception: return self.send(400,{'error':'JSON noto‘g‘ri'})
  m=re.fullmatch(r'/api/(applications|content|programs|menu)/(\d+)',urlparse(self.path).path)
  if not m: return self.send(404,{'error':'Topilmadi'})
  kind,id=m.group(1),int(m.group(2)); allowed={'applications':{'status'},'content':{'title','body','published'},'programs':{'name','description','active'},'menu':{'label','url','position','active'}}[kind]
  updates={k:v for k,v in d.items() if k in allowed}
  if not updates: return self.send(400,{'error':'O‘zgarish yo‘q'})
  if kind=='applications' and updates.get('status') not in ('Yangi','Ko‘rib chiqilmoqda','Qabul qilingan','Rad etilgan'): return self.send(400,{'error':'Holat noto‘g‘ri'})
  for k,v in updates.items():
   if k=='url' and (not re.fullmatch(r'/[a-zA-Z0-9_/?=&.%-]*',str(v)) or str(v).startswith('//')): return self.send(400,{'error':'Havola noto‘g‘ri'})
   if k in ('title','name','label') and (not str(v).strip() or len(str(v))>200): return self.send(400,{'error':'Nom noto‘g‘ri'})
   if k in ('body','description') and len(str(v))>10000: return self.send(400,{'error':'Matn juda uzun'})
   if k in ('active','published'): updates[k]=int(bool(v))
  table=kind; sql=f'UPDATE {table} SET '+','.join(f'{k}=?' for k in updates)+' WHERE id=?'
  with connect() as c:
   cur=c.execute(sql,[*updates.values(),id]); audit(c,f'{kind} #{id} yangilandi')
  return self.send(200,{'ok':cur.rowcount>0})
 def do_DELETE(self):
  if not self.require(write=True): return
  m=re.fullmatch(r'/api/(content|programs|menu|media)/(\d+)',urlparse(self.path).path)
  if not m: return self.send(404,{'error':'Topilmadi'})
  kind,id=m.group(1),int(m.group(2))
  with connect() as c:
   if kind=='programs' and (c.execute('SELECT 1 FROM exam_requests WHERE program_id=? LIMIT 1',(id,)).fetchone() or c.execute('SELECT 1 FROM applications WHERE program_id=? LIMIT 1',(id,)).fetchone()):
    return self.send(409,{'error':'Bu yo‘nalishga arizalar bor. Qabulni yoping yoki yo‘nalishni yashiring.'})
   if kind=='media':
    row=c.execute('SELECT filename FROM media WHERE id=?',(id,)).fetchone()
    if row: (UPLOAD/row['filename']).unlink(missing_ok=True)
   cur=c.execute(f'DELETE FROM {kind} WHERE id=?',(id,)); audit(c,f'{kind} #{id} o‘chirildi')
  return self.send(200,{'ok':cur.rowcount>0})

if __name__=='__main__':
 import sys
 google_file=ROOT/'google-client.local.json'
 if google_file.is_file():
  try:
   google_data=json.loads(google_file.read_text(encoding='utf-8-sig'))['web']
   for key,value in [('GOOGLE_CLIENT_ID',google_data['client_id']),('GOOGLE_CLIENT_SECRET',google_data['client_secret']),('GOOGLE_REDIRECT_URI','http://127.0.0.1:8000/auth/google/callback')]:
    os.environ.setdefault(key,value)
  except (ValueError,KeyError,TypeError):
   raise SystemExit('google-client.local.json noto‘g‘ri. Google’dan Web client JSON faylini yuklang.')
 if '--configure-sheets' in sys.argv:
  from sheets_sync import configure_sheets
  raise SystemExit(configure_sheets(ROOT/'sheets.local.json'))
 init()
 admissions.initialize(connect)
 admissions.start_expiry_worker(connect)
 admissions.start_export_worker(connect,ROOT/'sheets.local.json')
 port=int(os.getenv('PORT','8000'))
 print(f'ISFT PRO: http://127.0.0.1:{port}')
 ThreadingHTTPServer((os.getenv('ISFT_HOST','127.0.0.1'),port),Handler).serve_forever()
