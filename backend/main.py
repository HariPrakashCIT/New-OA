import os, secrets, hashlib, asyncio, json
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import Literal
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field, ConfigDict, field_validator
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from backend.analysis import analyze
from backend import gemma

URL = os.getenv('SUPABASE_URL', '').rstrip('/')
KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
app = FastAPI(title='OsteoCare AI', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(','), allow_methods=['GET','POST','PUT'], allow_headers=['Authorization','Content-Type','X-Device-Key'])

@app.exception_handler(httpx.HTTPError)
async def upstream_unavailable(request, exc):
    return JSONResponse(status_code=503, content={'detail':'Database or authentication service is temporarily unavailable. Please retry.'})

def now(): return datetime.now(timezone.utc)
def stamp(): return now().isoformat()
async def db(method, table, params=None, body=None):
    if not URL or not KEY: raise HTTPException(503, 'Backend Supabase configuration is missing')
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.request(method, URL+'/rest/v1/'+table, params=params, json=body, headers={'apikey':KEY,'Authorization':'Bearer '+KEY,'Prefer':'return=representation'})
    if r.status_code>=400:
        if r.status_code==409: raise HTTPException(409, 'Duplicate reading or an active session already exists')
        raise HTTPException(502, 'Database operation failed')
    return r.json() if r.content else []
async def identity(token):
    if not URL or not KEY: raise HTTPException(503,'Backend Supabase configuration is missing')
    async with httpx.AsyncClient(timeout=10) as client:
        r=await client.get(URL+'/auth/v1/user',headers={'apikey':KEY,'Authorization':'Bearer '+token})
    if r.status_code!=200: raise HTTPException(401,'Please sign in again')
    return r.json()['id']
async def user(authorization: str=Header(default='')):
    if not authorization.startswith('Bearer '): raise HTTPException(401,'Sign in required')
    return await identity(authorization[7:])
async def owned(device_id, uid):
    devices=await db('GET','devices',{'id':'eq.'+device_id,'user_id':'eq.'+uid})
    if not devices: raise HTTPException(404,'Device not found')
    return devices[0]
class Reading(BaseModel):
    model_config=ConfigDict(extra='forbid', strict=True)
    device_id: str = Field(min_length=1,max_length=80)
    timestamp: datetime
    heel_pressure: int=Field(ge=0,le=4095)
    ball_pressure: int=Field(ge=0,le=4095)
    toe_pressure: int=Field(ge=0,le=4095)
    @field_validator('timestamp',mode='before')
    @classmethod
    def timestamp_valid(cls,v):
        if isinstance(v,str):
            try: v=datetime.fromisoformat(v.replace('Z','+00:00'))
            except ValueError: raise ValueError('ISO timestamp required')
        if not isinstance(v,datetime) or v.tzinfo is None: raise ValueError('Timezone required')
        if abs((now()-v).total_seconds())>300: raise ValueError('Device clock must be within five minutes of server')
        return v
class DeviceInput(BaseModel):
    name: str=Field(min_length=1,max_length=80)
class SessionInput(BaseModel): device_id: str
class Profile(BaseModel):
    name: str=Field(max_length=80)
    daily_goal: int=Field(ge=1,le=240)
class ReportInput(BaseModel):
    device_id: str
    period: Literal['day','week','month']='week'

@app.get('/health')
async def health(): return {'status':'ok','configured':bool(URL and KEY)}
@app.get('/ready')
async def ready():
    try:
        await db('GET','profiles',{'select':'id','limit':'1'})
    except (HTTPException,httpx.HTTPError):
        raise HTTPException(503,'Supabase is not reachable or is not configured correctly')
    return {'ready':True}

@app.post('/api/readings',status_code=201)
async def ingest(reading: Reading,x_device_key: str=Header(default='')):
    devices=await db('GET','devices',{'id':'eq.'+reading.device_id})
    if not devices or not secrets.compare_digest(devices[0]['key_hash'],hashlib.sha256(x_device_key.encode()).hexdigest()): raise HTTPException(401,'Invalid device credentials')
    row=reading.model_dump(mode='json'); row['received_at']=stamp()
    await db('POST','readings',body=row)
    return {'accepted':True}
@app.get('/api/devices')
async def devices(uid=Depends(user)):
    rows=await db('GET','devices',{'user_id':'eq.'+uid,'select':'id,name,created_at'})
    for d in rows:
        last=await db('GET','readings',{'device_id':'eq.'+d['id'],'order':'received_at.desc','limit':'1'})
        d['last_reading']=last[0] if last else None
        d['online']=bool(last and (now()-datetime.fromisoformat(last[0]['received_at'].replace('Z','+00:00'))).total_seconds()<15)
    return rows
@app.post('/api/devices',status_code=201)
async def add_device(body:DeviceInput,uid=Depends(user)):
    key=secrets.token_urlsafe(32); device_id='OSTEOCARE_'+secrets.token_hex(5).upper()
    await db('POST','devices',body={'id':device_id,'user_id':uid,'name':body.name,'key_hash':hashlib.sha256(key.encode()).hexdigest()})
    return {'id':device_id,'key':key,'name':body.name}
async def readings_for(device_id,uid,days):
    await owned(device_id,uid)
    # Supabase's default page cap is 1000. Page explicitly; bound reports to protect server memory.
    result=[]
    for offset in range(0,50000,1000):
        rows=await db('GET','readings',{'device_id':'eq.'+device_id,'timestamp':'gte.'+(now()-timedelta(days=days)).isoformat(),'order':'timestamp.desc','limit':'1000','offset':str(offset)})
        result.extend(rows)
        if len(rows)<1000: break
    return result
@app.get('/api/readings')
async def history(device_id:str,days:int=1,uid=Depends(user)):
    if days not in [1,7,30]: raise HTTPException(422,'Use 1, 7 or 30 days')
    rows=await readings_for(device_id,uid,days)
    return {'readings':rows,'truncated':len(rows)==50000}
@app.get('/api/profile')
async def profile(uid=Depends(user)):
    rows=await db('GET','profiles',{'id':'eq.'+uid})
    return rows[0] if rows else {'name':'','daily_goal':20}
@app.put('/api/profile')
async def save_profile(body:Profile,uid=Depends(user)):
    rows=await db('GET','profiles',{'id':'eq.'+uid})
    return await db('PATCH' if rows else 'POST','profiles',{'id':'eq.'+uid} if rows else None,body.model_dump() if rows else dict(id=uid,**body.model_dump()))
@app.get('/api/sessions')
async def sessions(uid=Depends(user)): return await db('GET','sessions',{'user_id':'eq.'+uid,'order':'started_at.desc','limit':'100'})
@app.post('/api/sessions',status_code=201)
async def start_session(body:SessionInput,uid=Depends(user)):
    await owned(body.device_id,uid)
    return (await db('POST','sessions',body={'user_id':uid,'device_id':body.device_id}))[0]
@app.post('/api/sessions/{session_id}/stop')
async def stop_session(session_id:str,uid=Depends(user)):
    rows=await db('PATCH','sessions',{'id':'eq.'+session_id,'user_id':'eq.'+uid,'ended_at':'is.null'},{'ended_at':stamp()})
    if not rows: raise HTTPException(404,'Active session not found')
    return rows[0]
@app.post('/api/reports',status_code=201)
async def report(body:ReportInput,uid=Depends(user)):
    rows=await readings_for(body.device_id,uid,{'day':1,'week':7,'month':30}[body.period])
    a=analyze(rows); a['device_id']=body.device_id; a['truncated']=len(rows)==50000
    return (await db('POST','reports',body={'user_id':uid,'period':body.period,'analysis':a}))[0]
@app.get('/api/reports')
async def reports(uid=Depends(user)): return await db('GET','reports',{'user_id':'eq.'+uid,'order':'created_at.desc','limit':'100'})
class ExplanationConsent(BaseModel):
    consent: Literal[True]

@app.get('/api/ai/status')
async def ai_status(uid=Depends(user)):
    return gemma.status()

@app.post('/api/reports/{report_id}/explain')
async def explain_report(report_id:str,body:ExplanationConsent,uid=Depends(user)):
    rows=await db('GET','reports',{'id':'eq.'+report_id,'user_id':'eq.'+uid})
    if not rows: raise HTTPException(404,'Report not found')
    analysis=dict(rows[0]['analysis'])
    if analysis.get('ai_explanation'): return rows[0]
    explanation=await gemma.explain(analysis)
    analysis['ai_explanation']=explanation
    saved=await db('PATCH','reports',{'id':'eq.'+report_id,'user_id':'eq.'+uid},{'analysis':analysis})
    if not saved: raise HTTPException(404,'Report not found')
    return saved[0]

@app.get('/api/reports/{report_id}/pdf')
async def pdf(report_id:str,uid=Depends(user)):
    rows=await db('GET','reports',{'id':'eq.'+report_id,'user_id':'eq.'+uid})
    if not rows: raise HTTPException(404,'Report not found')
    report=rows[0]; a=report['analysis']; buffer=BytesIO(); c=canvas.Canvas(buffer); y=790
    lines=['OsteoCare AI - Mobility signal report',report['created_at'],report['period'].title()+' report',f"Samples analyzed: {a['samples']}", 'Relative ADC shares (heel, ball, toe): '+str(a['shares']),*a['observations'],*a['recommendations'],a['disclaimer']]
    if a.get('ai_explanation'):
        ai=a['ai_explanation']
        lines.extend(['AI explanation - '+ai['model'],ai['text'],ai['disclaimer']])
    if a.get('truncated'): lines.append('Limited to the most recent 50,000 samples in this period.')
    c.setFont('Helvetica',11)
    for line in lines:
        for part in simpleSplit(line,'Helvetica',11,490):
            if y<60: c.showPage(); c.setFont('Helvetica',11); y=790
            c.drawString(50,y,part); y-=20
        y-=8
    c.save()
    return Response(buffer.getvalue(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="osteocare-report.pdf"'})
@app.websocket('/ws/live/{device_id}')
async def live(ws:WebSocket,device_id:str):
    await ws.accept()
    try:
        message=await asyncio.wait_for(ws.receive_json(),timeout=10)
        uid=await identity(message.get('token','')); await owned(device_id,uid)
        # Poll durable storage so WebSockets work across backend replicas and server restarts.
        while True:
            await identity(message.get('token',''))
            await owned(device_id,uid)
            last=await db('GET','readings',{'device_id':'eq.'+device_id,'order':'received_at.desc','limit':'1'})
            row=last[0] if last else None
            online=bool(row and (now()-datetime.fromisoformat(row['received_at'].replace('Z','+00:00'))).total_seconds()<15)
            await ws.send_json({'reading':row,'online':online})
            await asyncio.sleep(1)
    except (WebSocketDisconnect,asyncio.TimeoutError): pass
    except Exception:
        try: await ws.close(code=1008)
        except RuntimeError: pass
