from datetime import timedelta
import hashlib
import asyncio
import httpx
import pytest
from fastapi.testclient import TestClient
from backend import main as m
from backend.analysis import analyze

def test_storage_uses_isolated_osteocare_tables(monkeypatch):
    monkeypatch.setattr(m,'URL','https://project.example')
    monkeypatch.setattr(m,'KEY','test-service-key')
    original=httpx.AsyncClient
    seen=[]
    def respond(request):
        seen.append(request.url.path)
        assert request.headers['apikey']=='test-service-key'
        return httpx.Response(200,json=[])
    monkeypatch.setattr(m.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(respond),**kw))
    for table in ['profiles','devices','readings','sessions','reports']:
        asyncio.run(m.db('GET',table))
    assert seen==['/rest/v1/osteocare_'+table for table in ['profiles','devices','readings','sessions','reports']]

@pytest.fixture
def client(monkeypatch):
    async def identity(token):
        if token!='valid': raise m.HTTPException(401,'Invalid token')
        return 'owner'
    monkeypatch.setattr(m,'identity',identity)
    return TestClient(m.app)

def reading(**changes):
    return dict(device_id='D1',timestamp=m.stamp(),heel_pressure=200,ball_pressure=300,toe_pressure=100,**changes)

def test_requires_signin(client):
    assert client.get('/api/devices').status_code==401

def test_invalid_readings(client):
    for change in [{'heel_pressure':-1},{'toe_pressure':4096},{'ball_pressure':None},{'heel_pressure':True},{'toe_pressure':'12'},{'timestamp':'2020-01-01T00:00:00Z'},{'timestamp':'2026-11-12T00:00:00'},{'extra':2}]:
        data=reading();data.update(change)
        assert client.post('/api/readings',json=data).status_code==422
    data=reading();del data['heel_pressure']
    assert client.post('/api/readings',json=data).status_code==422

def test_ingestion_key_and_persistence(client,monkeypatch):
    stored=[]
    async def db(method,table,params=None,body=None):
        if method=='GET':return [{'id':'D1','user_id':'owner','key_hash':hashlib.sha256(b'secret').hexdigest()}]
        stored.append(body);return [body]
    monkeypatch.setattr(m,'db',db)
    assert client.post('/api/readings',json=reading(),headers={'X-Device-Key':'bad'}).status_code==401
    assert not stored
    assert client.post('/api/readings',json=reading(),headers={'X-Device-Key':'secret'}).status_code==201
    assert stored[0]['heel_pressure']==200 and 'received_at' in stored[0]

def test_other_users_device_hidden(client,monkeypatch):
    async def db(*args,**kwargs):return []
    monkeypatch.setattr(m,'db',db)
    assert client.get('/api/readings?device_id=OTHER',headers={'Authorization':'Bearer valid'}).status_code==404
    assert client.post('/api/sessions',json={'device_id':'OTHER'},headers={'Authorization':'Bearer valid'}).status_code==404
    assert client.get('/api/reports/OTHER/pdf',headers={'Authorization':'Bearer valid'}).status_code==404

def test_offline_uses_receipt_time(client,monkeypatch):
    async def db(method,table,params=None,body=None):
        if table=='devices':return [{'id':'D1','name':'Insole'}]
        return [dict(reading(),received_at=(m.now()-timedelta(seconds=20)).isoformat())]
    monkeypatch.setattr(m,'db',db)
    r=client.get('/api/devices',headers={'Authorization':'Bearer valid'})
    assert r.status_code==200 and not r.json()[0]['online']

def test_pdf_real_report(client,monkeypatch):
    async def db(*args,**kwargs):return [{'period':'day','created_at':m.stamp(),'analysis':analyze([reading()])}]
    monkeypatch.setattr(m,'db',db)
    r=client.get('/api/reports/R1/pdf',headers={'Authorization':'Bearer valid'})
    assert r.status_code==200 and r.content.startswith(b'%PDF')

def test_live_authenticated_and_offline(client,monkeypatch):
    async def db(method,table,params=None,body=None):
        if table=='devices':return [{'id':'D1'}]
        return []
    monkeypatch.setattr(m,'db',db)
    with client.websocket_connect('/ws/live/D1') as ws:
        ws.send_json({'token':'valid'})
        assert ws.receive_json()=={'reading':None,'online':False}

def test_analysis_no_fabricated_results():
    a=analyze([]);assert a['samples']==0 and a['shares'] is None
    a=analyze([dict(timestamp=m.stamp(),heel_pressure=0,ball_pressure=0,toe_pressure=0)])
    assert a['shares'] is None
    a=analyze([dict(timestamp=m.stamp(),heel_pressure=4095,ball_pressure=20,toe_pressure=10)])
    assert any('saturation' in s for s in a['observations'])
    assert a['shares'][0]>99


def test_readiness_fails_without_configuration(client,monkeypatch):
    monkeypatch.setattr(m,'URL','')
    monkeypatch.setattr(m,'KEY','')
    assert client.get('/health').json()['configured'] is False
    assert client.get('/ready').status_code==503

def test_readiness_checks_storage(client,monkeypatch):
    async def db(*args,**kwargs): return []
    monkeypatch.setattr(m,'db',db)
    assert client.get('/ready').json()=={'ready':True}


def test_usb_requires_account_and_device_ownership(client,monkeypatch):
    sample=reading();sample.pop('device_id')
    assert client.post('/api/devices/D1/usb-readings',json=sample).status_code==401
    calls=[]
    async def db(method,table,params=None,body=None):
        calls.append((method,table,params,body))
        return []
    monkeypatch.setattr(m,'db',db)
    assert client.post('/api/devices/OTHER/usb-readings',json=sample,headers={'Authorization':'Bearer valid'}).status_code==404
    assert calls==[('GET','devices',{'id':'eq.OTHER','user_id':'eq.owner'},None)]


def test_usb_stores_three_real_samples_without_device_secret(client,monkeypatch):
    stored=[]
    async def db(method,table,params=None,body=None):
        if table=='devices':
            assert params=={'id':'eq.D1','user_id':'eq.owner'}
            return [{'id':'D1'}]
        stored.append(body);return [body]
    monkeypatch.setattr(m,'db',db)
    sample=reading();sample.pop('device_id')
    result=client.post('/api/devices/D1/usb-readings',json=sample,headers={'Authorization':'Bearer valid'})
    assert result.status_code==201 and result.json()=={'accepted':True}
    assert stored[0]['device_id']=='D1' and stored[0]['ball_pressure']==300
    assert stored[0]['received_at'] and stored[0]['timestamp']


def test_usb_rejects_invalid_and_spoofed_samples(client):
    sample=reading();sample.pop('device_id')
    for change in [{'heel_pressure':None},{'toe_pressure':4096},{'device_id':'OTHER'},{'ball_pressure':False},{'timestamp':'2020-01-01T00:00:00Z'}]:
        assert client.post('/api/devices/D1/usb-readings',json={**sample,**change},headers={'Authorization':'Bearer valid'}).status_code==422


def knee_packet():
    return dict(device_id='D1',timestamp=m.stamp(),v=1,seq=12,ms=5000,fsr=[123,456,0],total=579,pressed=[False,True,False])


def test_knee_wifi_packet_maps_exact_sensor_order(client,monkeypatch):
    stored=[]
    async def db(method,table,params=None,body=None):
        if method=='GET': return [{'id':'D1','key_hash':hashlib.sha256(b'secret').hexdigest()}]
        stored.append(body);return [body]
    monkeypatch.setattr(m,'db',db)
    assert client.post('/api/knee-readings',json=knee_packet(),headers={'X-Device-Key':'bad'}).status_code==401
    assert not stored
    assert client.post('/api/knee-readings',json=knee_packet(),headers={'X-Device-Key':'secret'}).status_code==201
    assert [stored[0][k] for k in ['heel_pressure','ball_pressure','toe_pressure']]==[123,456,0]


def test_knee_wifi_rejects_corrupt_packets(client):
    for change in [{'fsr':[1,2]},{'fsr':[0,0,4096]},{'fsr':[False,456,0]},{'total':10},{'pressed':[True,True,True]},{'v':2},{'seq':-1},{'timestamp':'2020-01-01T00:00:00Z'}]:
        assert client.post('/api/knee-readings',json={**knee_packet(),**change}).status_code==422


def test_knee_zone_patterns_and_gemma_summary():
    from backend.gemma import summary_for
    a=analyze([dict(timestamp=m.stamp(),heel_pressure=0,ball_pressure=301,toe_pressure=300),dict(timestamp=m.stamp(),heel_pressure=200,ball_pressure=501,toe_pressure=100)])
    assert a['zone_stats']['heel']=={'min':0,'mean':100.0,'max':200,'above_300_percent':0.0}
    assert a['zone_stats']['ball']['above_300_percent']==100
    assert a['zone_stats']['toe']['above_300_percent']==0
    assert summary_for(a)['zone_statistics_adc']==a['zone_stats']
