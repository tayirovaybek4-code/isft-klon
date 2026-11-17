"""Local integration smoke tests; no third-party packages required."""
import os,sys,tempfile,subprocess,time,urllib.request,urllib.error,json,http.cookiejar,pathlib,shutil,sqlite3,hashlib
src=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as d:
 root=pathlib.Path(d);shutil.copy(src/'server.py',root/'server.py');shutil.copytree(src/'static',root/'static')
 for name in ('admissions.py','exam_seed.py','sheets_sync.py'):shutil.copy(src/name,root/name)
 with sqlite3.connect(root/'isft.db') as db:
  db.execute('''CREATE TABLE applications(id INTEGER PRIMARY KEY, first_name TEXT NOT NULL,
   last_name TEXT NOT NULL, father_name TEXT, phone TEXT NOT NULL, birth_date TEXT, program TEXT NOT NULL,
   study_type TEXT, status TEXT DEFAULT 'Yangi', created_at TEXT NOT NULL)''')
  db.executemany('INSERT INTO applications(first_name,last_name,phone,program,created_at) VALUES (?,?,?,?,?)',
   [('Oldest' if i==0 else 'Later','Applicant','901234567','Iqtisodiyot','2025-01-01') for i in range(1001)])
 db.close()
 env=os.environ.copy();env.update(ADMIN_PASSWORD='TemporaryIntegrationTestPassword!89',PORT='18766')
 proc=subprocess.Popen([sys.executable,str(root/'server.py')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 try:
  base='http://127.0.0.1:18766';jar=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
  def req(path,method='GET',data=None,csrf=''):
   b=json.dumps(data).encode() if method in ('POST','PATCH') else None
   r=urllib.request.Request(base+path,data=b,method=method,headers={'Content-Type':'application/json','X-CSRF-Token':csrf})
   with op.open(r,timeout=3) as x:return x.status,json.loads(x.read())
  def expect_error(status,path,method='GET',data=None,csrf=''):
   try:req(path,method,data,csrf)
   except urllib.error.HTTPError as e:
    assert e.code==status and json.load(e)['error']
   else:raise AssertionError(f'{path} should return {status}')
  for i in range(40):
   try:req('/api/public/programs');break
   except Exception:
    if proc.poll() is not None:raise AssertionError(proc.stderr.read().decode())
    time.sleep(.1)
  with sqlite3.connect(root/'isft.db') as db:
   db.execute("INSERT INTO applicants(google_sub,email,name,created_at) VALUES('test-sub','test@example.test','Test Student','2026-01-01')")
   db.execute('INSERT INTO applicant_sessions VALUES(?,?,?,?)',(hashlib.sha256(b'test-student-token').hexdigest(),1,'student-csrf',time.time()+3600))
  db.close()
  jar.set_cookie(http.cookiejar.Cookie(0,'student_sid','test-student-token',None,False,'127.0.0.1',False,False,'/',True,False,None,True,None,None,{}))
  assert len(req('/api/public/programs')[1])==16
  assert len(req('/api/public/menu')[1])==6
  try:req('/api/dashboard');raise AssertionError('unauthorized dashboard accessible')
  except urllib.error.HTTPError as e:assert e.code==401
  assert req('/api/login','POST',{'username':'admin','password':env['ADMIN_PASSWORD']})[0]==200
  csrf=req('/api/session')[1]['csrf'];assert csrf
  expect_error(400,'/api/login','POST',[])
  expect_error(400,'/api/apply','POST',None)
  expect_error(400,'/api/programs/2','PATCH',[],csrf)
  assert req('/api/settings','POST',{'hero_title':'Sinov'},csrf)[0]==200
  assert req('/api/public/settings')[1]['hero_title']=='Sinov'
  assert req('/api/menu','POST',{'label':'Test','url':'/about.html'},csrf)[0]==201
  assert req('/api/applications/search?page=2')[1]['items'][0]['id']==951
  search=req('/api/applications/search?q=OLDEST')[1]
  assert search['total']==1 and search['items'][0]['id']==1
  assert req('/api/applications/search?students=1')[1]['total']==0
  assert req('/api/applications/1','PATCH',{'status':'Qabul qilingan'},csrf)[1]['ok']
  assert req('/api/applications/search?students=1')[1]['total']==1
  assert req('/api/programs/2','PATCH',{'name':'Renamed program'},csrf)[1]['ok']
  assert req('/api/dashboard')[1]['ranks'][0]=={'name':'Renamed program','count':1001}
  application={'first_name':'Test','last_name':'Applicant','phone':'+998 (90) 123-45-67',
               'birth_date':'2001-03-10','study_type':'Kunduzgi','program_id':2}
  for invalid in ({'phone':'---------'},{'birth_date':'2001-02-30'},{'birth_date':'2999-01-01'},
                  {'study_type':'Unknown'},{'program_id':999}):
   expect_error(400,'/api/apply','POST',application | invalid,'student-csrf')
  assert req('/api/apply','POST',application,'student-csrf')[0]==201
  legacy_application={key:value for key,value in application.items() if key!='program_id'}
  legacy_application['program']='Renamed program'
  for _ in range(4):assert req('/api/apply','POST',legacy_application,'student-csrf')[0]==200
  expect_error(429,'/api/apply','POST',application,'student-csrf')
  assert req('/api/dashboard')[1]['ranks'][0]=={'name':'Renamed program','count':1002}
  overview=req('/api/admissions/overview')[1]
  assert len(overview['programs'])==16
  assert all(len(json.loads(p['questions']))==28 for p in overview['programs'])
  config=next(p for p in overview['programs'] if p['id']==2)
  questions=json.loads(config['questions'])
  settings={'program_id':2,'questions':questions,'pass_percent':60,'published':True,'admission_open':True,'capacity':1}
  assert req('/api/admissions/config','POST',settings,csrf)[1]['ok']
  request_id=overview['requests'][0]['id']
  expect_error(403,'/api/student/start','POST',{'request_id':request_id},'student-csrf')
  assert req('/api/admissions/permission','POST',{'id':request_id,'status':'Ruxsat berilgan'},csrf)[1]['ok']
  attempt=req('/api/student/start','POST',{'request_id':request_id},'student-csrf')[1]
  assert len(attempt['questions'])==28 and 'correct' not in attempt['questions'][0]
  assert attempt['deadline']-attempt['started']==5400
  assert req('/api/student/start','POST',{'request_id':request_id},'student-csrf')[1]['deadline']==attempt['deadline']
  answers={str(i):q['correct'] for i,q in enumerate(questions[:17])}
  req('/api/student/attempt','POST',{'id':attempt['id'],'answers':answers},'student-csrf')
  assert req('/api/student/attempt?id='+str(attempt['id']))[1]['answers']==answers
  result=req('/api/student/attempt','POST',{'id':attempt['id'],'answers':answers,'finish':True},'student-csrf')[1]
  assert result['passed']==1 and result['correct']==17 and 'Tabriklaymiz' in result['message']
  repeated=req('/api/student/attempt','POST',{'id':attempt['id'],'answers':{},'finish':True},'student-csrf')[1]
  assert repeated['correct']==17
  detail=req('/api/admissions/detail?id='+str(attempt['id']))[1]
  assert detail['questions'][0]['correct']==questions[0]['correct']
  expect_error(403,'/api/student/request','POST',{'program_id':1},'wrong-csrf')
  expect_error(400,'/api/student/request','POST',{'program_id':[]},'student-csrf')
  settings['admission_open']=False
  req('/api/admissions/config','POST',settings,csrf)
  public=next(p for p in req('/api/public/programs')[1] if p['id']==2)
  assert public['admission_open']==0
  # A different exam is forced past its deadline; client answers arriving afterwards must be ignored.
  other=req('/api/student/request','POST',{'program_id':1},'student-csrf')[1]['id']
  first=next(p for p in overview['programs'] if p['id']==1)
  req('/api/admissions/config','POST',settings|{'program_id':1,'admission_open':True,'questions':json.loads(first['questions'])},csrf)
  req('/api/admissions/permission','POST',{'id':other,'status':'Ruxsat berilgan'},csrf)
  late=req('/api/student/start','POST',{'request_id':other},'student-csrf')[1]
  with sqlite3.connect(root/'isft.db') as db:db.execute('UPDATE exam_attempts SET deadline=? WHERE id=?',(time.time()-1,late['id']))
  db.close()
  failed=req('/api/student/attempt','POST',{'id':late['id'],'answers':{'0':0},'finish':True},'student-csrf')[1]
  assert failed['correct']==0 and failed['passed']==0 and 'ishonaman' in failed['message']
  assert req('/api/admissions/overview')[1]['pending_exports']>=4
  # Another student's account cannot read attempts and cannot bypass a full program.
  with sqlite3.connect(root/'isft.db') as db:
   db.execute("INSERT INTO applicants(google_sub,email,name,created_at) VALUES('test-other','other@example.test','Other Student','2026-01-01')")
   db.execute('UPDATE applicant_sessions SET applicant_id=2')
  db.close()
  expect_error(404,'/api/student/attempt?id='+str(attempt['id']))
  expect_error(409,'/api/student/request','POST',{'program_id':2},'student-csrf')
  req('/api/admissions/config','POST',settings|{'admission_open':True},csrf)
  expect_error(409,'/api/student/request','POST',{'program_id':2},'student-csrf')
  expect_error(409,'/api/programs/2','DELETE',csrf=csrf)
  expect_error(400,'/api/admissions/config','POST',settings|{'questions':questions[:5]},csrf)
  with sqlite3.connect(root/'isft.db') as db:db.execute('DELETE FROM applicant_sessions')
  db.close()
  expect_error(401,'/api/student/request','POST',{'program_id':3},'student-csrf')
  expect_error(401,'/api/apply','POST',application,'student-csrf')
  expect_error(403,'/auth/google/callback?state=wrong') if all(env.get(k) for k in ('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_REDIRECT_URI')) else expect_error(503,'/auth/google/start')
  assert req('/api/logout','POST',{},csrf)[0]==200
  print('PASS: legacy migration, search, auth/CSRF, 16 x 28 questions, Google gate, admission requests, permission, exam snapshots, 90-minute timer, autosave, pass/fail, deadline rejection, idempotent submit, admin answers, export queue')
 finally:proc.terminate();proc.wait(timeout=5)
