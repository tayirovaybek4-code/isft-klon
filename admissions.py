"""Google sign-in, admission requests and timed, server-graded exams."""
import base64
import hashlib
import json
import os
import secrets
import threading
import time
from http.cookies import SimpleCookie
from urllib.parse import urlencode, parse_qs, urlparse
from urllib.request import Request, urlopen

PASS_MESSAGE = 'Tabriklaymiz! Siz ISFT universitetining talabasi bo‘ldingiz!'
FAIL_MESSAGE = 'Men sizga ishonaman. Siz o‘z ustingizda ishlaysiz va bizning oilamizga albatta qo‘shilasiz!'
DURATION = 90 * 60
SYNC_STATUS = {'configured':False,'error':''}


class AdmissionError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def initialize(connect):
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS applicants(id INTEGER PRIMARY KEY, google_sub TEXT UNIQUE NOT NULL,
          email TEXT NOT NULL, name TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS applicant_sessions(token TEXT PRIMARY KEY, applicant_id INTEGER NOT NULL,
          csrf TEXT NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS oauth_states(state TEXT PRIMARY KEY, verifier TEXT NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS exam_configs(program_id INTEGER PRIMARY KEY, admission_open INTEGER DEFAULT 1,
          capacity INTEGER, published INTEGER DEFAULT 0, pass_percent INTEGER DEFAULT 60,
          questions TEXT NOT NULL DEFAULT '[]');
        CREATE TABLE IF NOT EXISTS exam_requests(id INTEGER PRIMARY KEY, applicant_id INTEGER NOT NULL,
          program_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Kutilmoqda', created_at TEXT NOT NULL,
          UNIQUE(applicant_id,program_id));
        CREATE TABLE IF NOT EXISTS exam_attempts(id INTEGER PRIMARY KEY, request_id INTEGER UNIQUE NOT NULL,
          applicant_id INTEGER NOT NULL, program_id INTEGER NOT NULL, program_name TEXT NOT NULL,
          questions TEXT NOT NULL, answers TEXT NOT NULL DEFAULT '{}', pass_percent INTEGER NOT NULL,
          started REAL NOT NULL, deadline REAL NOT NULL, finished REAL, correct INTEGER, percent REAL, passed INTEGER);
        CREATE TABLE IF NOT EXISTS admission_exports(key TEXT PRIMARY KEY, category TEXT NOT NULL,
          payload TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, synced INTEGER NOT NULL DEFAULT 0,
          target TEXT NOT NULL DEFAULT '');
        ''')
        columns = {row['name'] for row in db.execute('PRAGMA table_info(applications)')}
        if 'applicant_id' not in columns:
            db.execute('ALTER TABLE applications ADD COLUMN applicant_id INTEGER')
        from exam_seed import seed_questions
        for program in db.execute('SELECT id,name FROM programs').fetchall():
            db.execute('INSERT OR IGNORE INTO exam_configs(program_id,questions) VALUES(?,?)',
                       (program['id'], json.dumps(seed_questions(program['name']), ensure_ascii=False)))


def export(db, category, key, values):
    db.execute('''INSERT INTO admission_exports(key,category,payload) VALUES(?,?,?)
      ON CONFLICT(key) DO UPDATE SET payload=excluded.payload,version=admission_exports.version+1''',
               (category + ':' + str(key), category, json.dumps(values, ensure_ascii=False)))


def cookie(handler, name):
    parsed = SimpleCookie()
    try:
        parsed.load(handler.headers.get('Cookie', ''))
        return parsed[name].value if name in parsed else ''
    except Exception:
        return ''


def cookie_header(name, value, age, same_site='Strict'):
    secure = '; Secure' if os.getenv('ISFT_HTTPS') == '1' else ''
    return f'{name}={value}; HttpOnly; SameSite={same_site}; Path=/; Max-Age={age}{secure}'


def student(handler, connect, write=False):
    token = hashlib.sha256(cookie(handler, 'student_sid').encode()).hexdigest()
    with connect() as db:
        row = db.execute('''SELECT a.*,s.csrf FROM applicant_sessions s JOIN applicants a ON a.id=s.applicant_id
          WHERE s.token=? AND s.expires>?''', (token, time.time())).fetchone()
    if not row:
        raise AdmissionError('Avval Google orqali kiring.', 401)
    if write and not secrets.compare_digest(handler.headers.get('X-CSRF-Token', ''), row['csrf']):
        raise AdmissionError('Sahifani yangilab, qayta urinib ko‘ring.', 403)
    return dict(row)


def json_request(url, data=None, token=None):
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if data is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    request = Request(url, data=urlencode(data).encode() if data is not None else None, headers=headers)
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read(100_000))


def google_config():
    return [os.getenv(key, '') for key in ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI')]


def oauth(handler, connect, path, query):
    client, secret, redirect = google_config()
    if not all((client, secret, redirect)):
        raise AdmissionError('Google orqali kirish hali sozlanmagan. Qabul bo‘limiga murojaat qiling.', 503)
    if path.endswith('/start'):
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        with connect() as db:
            db.execute('DELETE FROM oauth_states WHERE expires<?', (time.time(),))
            db.execute('INSERT INTO oauth_states VALUES(?,?,?)', (state, verifier, time.time()+600))
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
            'client_id': client, 'redirect_uri': redirect, 'response_type': 'code',
            'scope': 'openid email profile', 'state': state, 'code_challenge': challenge,
            'code_challenge_method': 'S256', 'prompt': 'select_account'})
        handler.send(302, b'', headers={'Location': url, 'Set-Cookie': cookie_header('oauth_state',state,600,'Lax')})
        return
    state = query.get('state', [''])[0]
    if not state or not secrets.compare_digest(state, cookie(handler, 'oauth_state')):
        raise AdmissionError('Kirish so‘rovi eskirgan. Qayta kiring.', 403)
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM oauth_states WHERE state=? AND expires>?', (state,time.time())).fetchone()
        db.execute('DELETE FROM oauth_states WHERE state=?', (state,))
    if not row or 'code' not in query:
        raise AdmissionError('Google orqali kirish yakunlanmadi.')
    try:
        token = json_request('https://oauth2.googleapis.com/token', {
            'code': query['code'][0], 'client_id': client, 'client_secret': secret,
            'redirect_uri': redirect, 'grant_type': 'authorization_code', 'code_verifier': row['verifier']})
        profile = json_request('https://openidconnect.googleapis.com/v1/userinfo', token=token['access_token'])
        if profile.get('email_verified') is not True or not profile.get('sub') or not profile.get('email'):
            raise ValueError('Unverified Google account')
    except Exception:
        raise AdmissionError('Google bilan ulanish yakunlanmadi. Qayta urinib ko‘ring.', 502)
    sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    with connect() as db:
        db.execute('''INSERT INTO applicants(google_sub,email,name,created_at) VALUES(?,?,?,datetime('now'))
          ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email,name=excluded.name''',
                   (profile['sub'],profile['email'],profile.get('name',profile['email'])))
        person = dict(db.execute('SELECT * FROM applicants WHERE google_sub=?',(profile['sub'],)).fetchone())
        db.execute('DELETE FROM applicant_sessions WHERE expires<?',(time.time(),))
        db.execute('INSERT INTO applicant_sessions VALUES(?,?,?,?)',
                   (hashlib.sha256(sid.encode()).hexdigest(),person['id'],csrf,time.time()+86400))
        export(db,'Ro‘yxatdan o‘tganlar',person['id'],[person['id'],person['created_at'],person['name'],person['email']])
    handler.send(302,b'',headers={'Location':'/exam.html','Set-Cookie':cookie_header('student_sid',sid,86400)})


def finish(db, attempt):
    questions, answers = json.loads(attempt['questions']), json.loads(attempt['answers'])
    correct = sum(answers.get(str(i)) == q['correct'] for i,q in enumerate(questions))
    percent = round(correct * 100 / len(questions), 2)
    passed = int(correct * 100 >= attempt['pass_percent'] * len(questions))
    db.execute('UPDATE exam_attempts SET finished=?,correct=?,percent=?,passed=? WHERE id=? AND finished IS NULL',
               (min(time.time(),attempt['deadline']),correct,percent,passed,attempt['id']))
    db.execute('UPDATE applications SET status=? WHERE applicant_id=? AND program_id=?',
               ('Qabul qilingan' if passed else 'Rad etilgan',attempt['applicant_id'],attempt['program_id']))
    person = db.execute('SELECT * FROM applicants WHERE id=?',(attempt['applicant_id'],)).fetchone()
    export(db,'Test topshirganlar',attempt['id'],[
        attempt['id'],person['name'],person['email'],attempt['program_name'],correct,len(questions),percent,
        'O‘tdi' if passed else 'O‘tmadi',attempt['started'],attempt['deadline'],
        json.dumps([{'savol':q['text'],'javob':answers.get(str(i)),'togri':q['correct']} for i,q in enumerate(questions)],ensure_ascii=False)])


def expire(db):
    for row in db.execute('SELECT * FROM exam_attempts WHERE finished IS NULL AND deadline<=?',(time.time(),)).fetchall():
        finish(db,row)


def public_attempt(row):
    data = dict(row)
    questions = json.loads(data.pop('questions'))
    data['answers'] = json.loads(data['answers'])
    data['questions'] = [{'text':q['text'],'options':q['options']} for q in questions]
    data['server_time'] = time.time()
    if data['finished'] is not None:
        data['message'] = PASS_MESSAGE if data['passed'] else FAIL_MESSAGE
    return data


def validate_questions(data):
    questions = data.get('questions')
    if not isinstance(questions,list) or not 1 <= len(questions) <= 100:
        raise AdmissionError('1 dan 100 tagacha savol kiriting.')
    for q in questions:
        if (not isinstance(q,dict) or not isinstance(q.get('text'),str) or not 1 <= len(q['text'].strip()) <= 1000
            or not isinstance(q.get('options'),list) or len(q['options']) != 4
            or any(not isinstance(v,str) or not 1 <= len(v.strip()) <= 500 for v in q['options'])
            or len(set(q['options'])) != 4 or type(q.get('correct')) is not int or not 0 <= q['correct'] < 4):
            raise AdmissionError('Har savolga matn, 4 xil javob va bitta to‘g‘ri javob kiriting.')
    return questions


def handle(handler, connect, method):
    parsed = urlparse(handler.path)
    path, query = parsed.path, parse_qs(parsed.query)
    if not path.startswith(('/api/student/','/api/admissions/','/auth/google/')):
        return False
    try:
        if path in ('/auth/google/start','/auth/google/callback') and method == 'GET':
            oauth(handler,connect,path,query)
            return True
        if path == '/api/student/session' and method == 'GET':
            try:
                person = student(handler,connect)
                person = {key:person[key] for key in ('id','name','email','csrf')}
            except AdmissionError:
                person = None
            handler.send(200,{'person':person,'google_configured':all(google_config())})
            return True
        admin = path.startswith('/api/admissions/')
        if admin:
            if not handler.require(write=method!='GET'):
                return True
            person = None
        else:
            person = student(handler,connect,write=method!='GET')
        data = handler.payload() if method == 'POST' else {}
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            expire(db)
            result = route(db,path,method,data,query,person)
        handler.send(200,result)
    except AdmissionError as exc:
        handler.send(exc.status,{'error':str(exc)})
    except (ValueError,TypeError,KeyError):
        handler.send(400,{'error':'So‘rov ma’lumotlari noto‘g‘ri.'})
    return True


def route(db,path,method,data,query,person):
    for key in ('id','program_id','request_id'):
        if key in data and (type(data[key]) is not int or not 1<=data[key]<=2**63-1):
            raise AdmissionError('Yozuv raqami noto‘g‘ri.')
    if path == '/api/student/logout' and method == 'POST':
        db.execute('DELETE FROM applicant_sessions WHERE applicant_id=?',(person['id'],))
        return {'ok':True}
    if path == '/api/student/home' and method == 'GET':
        programs = [dict(r) for r in db.execute('''SELECT p.id,p.name,c.admission_open,c.published,c.capacity,
          (SELECT COUNT(*) FROM exam_requests r WHERE r.program_id=p.id AND r.status!='Rad etilgan') reserved
          FROM programs p LEFT JOIN exam_configs c ON c.program_id=p.id WHERE p.active=1''')]
        requests = [dict(r) for r in db.execute('''SELECT r.*,p.name,a.id attempt_id FROM exam_requests r
          LEFT JOIN programs p ON p.id=r.program_id LEFT JOIN exam_attempts a ON a.request_id=r.id
          WHERE r.applicant_id=?''',(person['id'],))]
        return {'programs':programs,'requests':requests}
    if path == '/api/student/request' and method == 'POST':
        program_id = data.get('program_id')
        row = db.execute('''SELECT p.name,c.* FROM programs p JOIN exam_configs c ON c.program_id=p.id
          WHERE p.id=? AND p.active=1''',(program_id,)).fetchone()
        if not row or not row['admission_open']:
            raise AdmissionError('Bu yo‘nalish uchun qabul yopilgan.',409)
        existing = db.execute('SELECT id FROM exam_requests WHERE applicant_id=? AND program_id=?',(person['id'],program_id)).fetchone()
        if existing:
            return {'id':existing['id']}
        count = db.execute("SELECT COUNT(*) FROM exam_requests WHERE program_id=? AND status!='Rad etilgan'",(program_id,)).fetchone()[0]
        if row['capacity'] is not None and count >= row['capacity']:
            raise AdmissionError('Yo‘nalish uchun ajratilgan joylar to‘lgan.',409)
        cursor = db.execute("INSERT INTO exam_requests(applicant_id,program_id,created_at) VALUES(?,?,datetime('now'))",(person['id'],program_id))
        export(db,'Testga arizalar',cursor.lastrowid,[cursor.lastrowid,person['name'],person['email'],row['name'],'Kutilmoqda'])
        return {'id':cursor.lastrowid}
    if path == '/api/student/start' and method == 'POST':
        request = db.execute('SELECT * FROM exam_requests WHERE id=? AND applicant_id=?',(data.get('request_id'),person['id'])).fetchone()
        if not request:
            raise AdmissionError('Ariza topilmadi.',404)
        attempt = db.execute('SELECT * FROM exam_attempts WHERE request_id=?',(request['id'],)).fetchone()
        if attempt:
            return public_attempt(attempt)
        config = db.execute('SELECT c.*,p.name FROM exam_configs c JOIN programs p ON p.id=c.program_id WHERE c.program_id=?',(request['program_id'],)).fetchone()
        if request['status'] != 'Ruxsat berilgan' or not config or not config['published']:
            raise AdmissionError('Imtihon uchun ruxsat hali berilmagan.',403)
        validate_questions({'questions':json.loads(config['questions'])})
        started = time.time()
        cursor = db.execute('''INSERT INTO exam_attempts(request_id,applicant_id,program_id,program_name,questions,
          pass_percent,started,deadline) VALUES(?,?,?,?,?,?,?,?)''',
          (request['id'],person['id'],request['program_id'],config['name'],config['questions'],config['pass_percent'],started,started+DURATION))
        return public_attempt(db.execute('SELECT * FROM exam_attempts WHERE id=?',(cursor.lastrowid,)).fetchone())
    if path == '/api/student/attempt' and method in ('GET','POST'):
        attempt_id = data.get('id') if method == 'POST' else query.get('id',[''])[0]
        attempt = db.execute('SELECT * FROM exam_attempts WHERE id=? AND applicant_id=?',(attempt_id,person['id'])).fetchone()
        if not attempt:
            raise AdmissionError('Imtihon topilmadi.',404)
        if method == 'POST' and attempt['finished'] is None:
            answers = data.get('answers',{})
            questions = json.loads(attempt['questions'])
            if not isinstance(answers,dict) or any(k not in {str(i) for i in range(len(questions))} or type(v) is not int or v not in range(4) for k,v in answers.items()):
                raise AdmissionError('Javoblar noto‘g‘ri.')
            saved = json.loads(attempt['answers'])
            saved.update(answers)
            db.execute('UPDATE exam_attempts SET answers=? WHERE id=?',(json.dumps(saved),attempt_id))
            attempt = db.execute('SELECT * FROM exam_attempts WHERE id=?',(attempt_id,)).fetchone()
            if data.get('finish') is True:
                finish(db,attempt)
                attempt = db.execute('SELECT * FROM exam_attempts WHERE id=?',(attempt_id,)).fetchone()
        return public_attempt(attempt)
    if path == '/api/admissions/overview' and method == 'GET':
        return {
          'people':[dict(r) for r in db.execute('SELECT id,name,email,created_at FROM applicants ORDER BY id DESC')],
          'requests':[dict(r) for r in db.execute('''SELECT r.*,a.name,a.email,p.name program FROM exam_requests r
            JOIN applicants a ON a.id=r.applicant_id LEFT JOIN programs p ON p.id=r.program_id ORDER BY r.id DESC''')],
          'attempts':[dict(r) for r in db.execute('''SELECT e.id,e.program_name,e.started,e.finished,e.correct,e.percent,e.passed,a.name,a.email
            FROM exam_attempts e JOIN applicants a ON a.id=e.applicant_id ORDER BY e.id DESC''')],
          'programs':[dict(r) for r in db.execute('SELECT p.id,p.name,c.* FROM programs p LEFT JOIN exam_configs c ON c.program_id=p.id ORDER BY p.id')],
          'sync':SYNC_STATUS,
          'pending_exports':db.execute('SELECT COUNT(*) FROM admission_exports WHERE synced<version').fetchone()[0]}
    if path == '/api/admissions/config' and method == 'POST':
        questions = validate_questions(data)
        if data.get('published') is True and len(questions)!=28:
            raise AdmissionError('Testni ochish uchun aynan 28 ta savol kerak.')
        score, capacity = data.get('pass_percent'),data.get('capacity')
        if type(score) is not int or not 1 <= score <= 100 or (capacity is not None and (type(capacity) is not int or capacity<0)):
            raise AdmissionError('O‘tish foizi 1–100, joylar soni esa 0 yoki musbat son bo‘lsin.')
        if not db.execute('SELECT 1 FROM programs WHERE id=?',(data.get('program_id'),)).fetchone():
            raise AdmissionError('Yo‘nalish topilmadi.',404)
        db.execute('''INSERT INTO exam_configs VALUES(?,?,?,?,?,?) ON CONFLICT(program_id) DO UPDATE SET
          admission_open=excluded.admission_open,capacity=excluded.capacity,published=excluded.published,
          pass_percent=excluded.pass_percent,questions=excluded.questions''',
          (data['program_id'],int(data.get('admission_open') is True),capacity,int(data.get('published') is True),score,json.dumps(questions,ensure_ascii=False)))
        return {'ok':True}
    if path == '/api/admissions/permission' and method == 'POST':
        status = data.get('status')
        if status not in ('Ruxsat berilgan','Rad etilgan'):
            raise AdmissionError('Holat noto‘g‘ri.')
        row = db.execute('''SELECT r.*,a.name,a.email,p.name program FROM exam_requests r JOIN applicants a ON a.id=r.applicant_id
          LEFT JOIN programs p ON p.id=r.program_id WHERE r.id=?''',(data.get('id'),)).fetchone()
        if not row:
            raise AdmissionError('Ariza topilmadi.',404)
        if db.execute('SELECT 1 FROM exam_attempts WHERE request_id=?',(row['id'],)).fetchone():
            raise AdmissionError('Imtihon boshlangan. Ruxsatni o‘zgartirib bo‘lmaydi.',409)
        if row['status']=='Rad etilgan' and status=='Ruxsat berilgan':
            config=db.execute('SELECT * FROM exam_configs WHERE program_id=?',(row['program_id'],)).fetchone()
            used=db.execute("SELECT COUNT(*) FROM exam_requests WHERE program_id=? AND status!='Rad etilgan'",(row['program_id'],)).fetchone()[0]
            if not config or not config['admission_open'] or (config['capacity'] is not None and used>=config['capacity']):
                raise AdmissionError('Qabul yopiq yoki joylar to‘lgan.',409)
        db.execute('UPDATE exam_requests SET status=? WHERE id=?',(status,row['id']))
        export(db,'Testga arizalar',row['id'],[row['id'],row['name'],row['email'],row['program'],status])
        return {'ok':True}
    if path == '/api/admissions/detail' and method == 'GET':
        row=db.execute('SELECT * FROM exam_attempts WHERE id=?',(query.get('id',[''])[0],)).fetchone()
        if not row:
            raise AdmissionError('Natija topilmadi.',404)
        result=dict(row)
        result['questions']=json.loads(result['questions'])
        result['answers']=json.loads(result['answers'])
        return result
    raise AdmissionError('Sahifa topilmadi.',404)


def start_expiry_worker(connect):
    def run():
        while True:
            try:
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    expire(db)
            except Exception:
                pass
            time.sleep(5)
    threading.Thread(target=run,daemon=True,name='exam-deadlines').start()


def start_export_worker(connect, path):
    from sheets_sync import load_config, GoogleContentRedirect
    from urllib.request import build_opener
    try:
        config=load_config(path)
    except ValueError as exc:
        SYNC_STATUS['error']=str(exc)
        return
    if not config:
        return
    SYNC_STATUS['configured']=True
    with connect() as db:
        db.execute('UPDATE admission_exports SET synced=0 WHERE target!=?',(config.target,))
    def run():
        while True:
            try:
                with connect() as db:
                    rows=db.execute('SELECT * FROM admission_exports WHERE synced<version OR target!=? ORDER BY key LIMIT 25',(config.target,)).fetchall()
                if rows:
                    payload={'protocol':'isft-sheets-v1','dataset':'admissions','secret':config.secret,
                             'spreadsheet_id':config.sheet_id,'rows':[{'key':r['key'],'category':r['category'],
                             'values':json.loads(r['payload']),'version':r['version']} for r in rows]}
                    request=Request(config.url,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
                    with build_opener(GoogleContentRedirect()).open(request,timeout=20) as response:
                        result=json.loads(response.read(65536))
                    if result.get('ok') is not True or result.get('spreadsheet_id')!=config.sheet_id or result.get('keys')!=[r['key'] for r in rows]:
                        raise ValueError('Google jadvali yozuvlarni tasdiqlamadi. Apps Script versiyasini tekshiring.')
                    with connect() as db:
                        db.executemany('UPDATE admission_exports SET synced=?,target=? WHERE key=? AND version=?',
                            [(r['version'],config.target,r['key'],r['version']) for r in rows])
                SYNC_STATUS['error']=''
            except Exception:
                SYNC_STATUS['error']='Google jadvaliga yuborilmadi. Ulanish va Apps Script sozlamalarini tekshiring. Qayta uriniladi.'
            time.sleep(5 if not SYNC_STATUS['error'] else 30)
    threading.Thread(target=run,daemon=True,name='admissions-google-sync').start()
