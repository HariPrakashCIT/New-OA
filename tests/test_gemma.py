import asyncio
import json
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend import gemma
from backend import main as m

SUMMARY={'samples':12,'shares':[40,35,25],'device_id':'PRIVATE_DEVICE','user_id':'PRIVATE_USER','observations':['Recording gaps exceed 5 seconds; coverage is incomplete.'],'truncated':True}

def configure(monkeypatch):
    monkeypatch.setenv('GEMMA_API_BASE_URL','https://openrouter.ai/api/v1')
    monkeypatch.setenv('GEMMA_API_KEY','server-only-secret')
    monkeypatch.setenv('GEMMA_MODEL',gemma.MODEL)

def transport(monkeypatch, handler):
    original=httpx.AsyncClient
    monkeypatch.setattr(gemma.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))

def test_missing_service_and_no_data(monkeypatch):
    monkeypatch.delenv('GEMMA_API_BASE_URL',raising=False)
    assert gemma.status()['configured'] is False
    with pytest.raises(HTTPException) as e:asyncio.run(gemma.explain(SUMMARY))
    assert e.value.status_code==503
    with pytest.raises(HTTPException) as e:asyncio.run(gemma.explain({'samples':0}))
    assert e.value.status_code==422

def test_no_remote_http_or_embedded_credentials(monkeypatch):
    for url in ['http://remote.example/v1','https://user:secret@example.com/v1','https://example.com/v1?key=secret']:
        monkeypatch.setenv('GEMMA_API_BASE_URL',url)
        assert not gemma.status()['configured']

@pytest.mark.parametrize('name,value',[
    ('GEMMA_MODEL','google/gemma-4-26b-a4b-it'),
    ('GEMMA_API_BASE_URL','https://other.example/v1'),
    ('GEMMA_API_KEY',''),
])
def test_free_only_blocks_paid_or_incomplete_configuration(monkeypatch,name,value):
    configure(monkeypatch)
    monkeypatch.setenv('GEMMA_FREE_ONLY','true')
    monkeypatch.setenv(name,value)
    def forbidden(*args,**kwargs):pytest.fail('Invalid free configuration must not reach the network')
    monkeypatch.setattr(gemma.httpx,'AsyncClient',forbidden)
    assert not gemma.status()['configured']
    with pytest.raises(HTTPException) as e:asyncio.run(gemma.explain(SUMMARY))
    assert e.value.status_code==503

def test_gemma_request_privacy_and_output(monkeypatch):
    configure(monkeypatch)
    def respond(request):
        assert str(request.url)=='https://openrouter.ai/api/v1/chat/completions'
        assert request.headers['Authorization']=='Bearer server-only-secret'
        body=json.loads(request.content)
        assert body['model']==gemma.MODEL
        assert body['provider']['max_price']=={'prompt':0,'completion':0}
        assert body['provider']['allow_fallbacks'] is False
        assert body['reasoning']['enabled'] is False
        assert 'PRIVATE_' not in request.content.decode()
        facts=json.loads(body['messages'][1]['content'])
        assert facts['sample_count']==12 and facts['report_truncated']
        assert facts['recording_gaps'] and facts['raw_adc_shares_percent']['heel']==40
        return httpx.Response(200,json={'choices':[{'message':{'content':'Recorded 12 samples. Not a medical assessment.'},'finish_reason':'stop'}]})
    transport(monkeypatch,respond)
    result=asyncio.run(gemma.explain(SUMMARY))
    assert result['model']==gemma.MODEL and result['text'].startswith('Recorded')

@pytest.mark.parametrize('code,expected',[(401,503),(403,503),(402,503),(429,503),(500,502)])
def test_upstream_errors_hide_response_secrets(monkeypatch,code,expected):
    configure(monkeypatch);transport(monkeypatch,lambda request:httpx.Response(code,text='PRIVATE SERVER ERROR'))
    with pytest.raises(HTTPException) as e:asyncio.run(gemma.explain(SUMMARY))
    assert e.value.status_code==expected and 'PRIVATE' not in e.value.detail

@pytest.mark.parametrize('reply',[
    {},{'choices':[]},{'choices':[{'message':{'content':''}}]},
    {'choices':[{'message':{'content':'unfinished'},'finish_reason':'length'}]},
    {'choices':[{'message':{'content':'<think>private reasoning</think>answer'},'finish_reason':'stop'}]},
])
def test_bad_or_unfinished_output_is_not_saved(monkeypatch,reply):
    configure(monkeypatch);transport(monkeypatch,lambda request:httpx.Response(200,json=reply))
    with pytest.raises(HTTPException) as e:asyncio.run(gemma.explain(SUMMARY))
    assert e.value.status_code==502

def test_report_ownership_consent_and_storage(monkeypatch):
    async def identity(token):return 'owner'
    monkeypatch.setattr(m,'identity',identity)
    calls=[]
    async def db(method,table,params=None,body=None):
        assert params['user_id']=='eq.owner'
        if params['id']=='eq.OTHER':return []
        if method=='PATCH':calls.append(body);return [{'id':'R1','analysis':body['analysis']}]
        return [{'id':'R1','analysis':dict(SUMMARY)}]
    async def explain(analysis):return {'text':'Test explanation','model':gemma.MODEL,'generated_at':m.stamp(),'disclaimer':'AI text may contain errors.'}
    monkeypatch.setattr(m,'db',db);monkeypatch.setattr(gemma,'explain',explain)
    client=TestClient(m.app);headers={'Authorization':'Bearer valid'}
    assert client.post('/api/reports/R1/explain',json={'consent':True}).status_code==401
    assert client.post('/api/reports/R1/explain',json={'consent':False},headers=headers).status_code==422
    assert client.post('/api/reports/OTHER/explain',json={'consent':True},headers=headers).status_code==404
    response=client.post('/api/reports/R1/explain',json={'consent':True},headers=headers)
    assert response.status_code==200 and response.json()['analysis']['ai_explanation']['model']==gemma.MODEL
    assert calls[0]['analysis']['samples']==SUMMARY['samples']

def test_cached_explanation_does_not_call_model(monkeypatch):
    async def identity(token):return 'owner'
    async def db(*args,**kw):return [{'id':'R1','analysis':{'ai_explanation':{'text':'Already saved'}}}]
    async def forbidden(*args):pytest.fail('Cached explanation must not call model again')
    monkeypatch.setattr(m,'identity',identity);monkeypatch.setattr(m,'db',db);monkeypatch.setattr(gemma,'explain',forbidden)
    response=TestClient(m.app).post('/api/reports/R1/explain',headers={'Authorization':'Bearer valid'},json={'consent':True})
    assert response.status_code==200 and response.json()['analysis']['ai_explanation']['text']=='Already saved'
