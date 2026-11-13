"""GPU model server. Start with uvicorn model-hosting.server:app or from this directory.
This service needs its own GPU host; it is not part of static Sites hosting.
"""
import asyncio
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

MODEL_ID='google/gemma-4-E4B-it'
state={}
lock=asyncio.Lock()

@asynccontextmanager
async def lifespan(app):
    import torch
    from transformers import AutoProcessor, AutoModelForMultimodalLM
    if not os.getenv('MODEL_API_KEY'): raise RuntimeError('Set MODEL_API_KEY in the host secret manager')
    if not torch.cuda.is_available(): raise RuntimeError('A CUDA-capable GPU host is required for this deployment recipe')
    state['torch']=torch
    state['processor']=AutoProcessor.from_pretrained(MODEL_ID)
    state['model']=AutoModelForMultimodalLM.from_pretrained(MODEL_ID,dtype='auto',device_map='auto').eval()
    yield
    state.clear()

app=FastAPI(title='OsteoCare Gemma inference',lifespan=lifespan)
class Message(BaseModel):
    role:Literal['system','user']
    content:str=Field(min_length=1,max_length=10000)
class Completion(BaseModel):
    model:Literal['google/gemma-4-E4B-it']
    messages:list[Message]=Field(min_length=1,max_length=2)
    max_tokens:int=Field(default=600,ge=1,le=700)
    temperature:float=Field(default=0.2,ge=0,le=1)
    stream:Literal[False]=False

def authorize(value):
    key=os.getenv('MODEL_API_KEY','')
    if not key or not secrets.compare_digest(value,'Bearer '+key):raise HTTPException(401,'Unauthorized')

@app.get('/health')
async def health():return {'ready':bool(state.get('model')),'model':MODEL_ID}

def generate(body):
    processor=state['processor'];model=state['model'];torch=state['torch']
    inputs=processor.apply_chat_template([m.model_dump() for m in body.messages],tokenize=True,return_dict=True,
        return_tensors='pt',add_generation_prompt=True,enable_thinking=False).to(model.device)
    input_len=inputs['input_ids'].shape[-1]
    if input_len>4096:raise HTTPException(422,'Input exceeds the service token limit')
    options={'max_new_tokens':body.max_tokens,'do_sample':body.temperature>0}
    if body.temperature>0:options['temperature']=body.temperature
    with torch.inference_mode(): output=model.generate(**inputs,**options)
    generated=output[0][input_len:]
    text=processor.decode(generated,skip_special_tokens=True).strip()
    return text,'length' if len(generated)>=body.max_tokens else 'stop'

@app.post('/v1/chat/completions')
async def complete(body:Completion,authorization:str=Header(default='')):
    authorize(authorization)
    try:await asyncio.wait_for(lock.acquire(),timeout=0.1)
    except asyncio.TimeoutError:raise HTTPException(503,'Model busy')
    try:
        text,reason=await asyncio.to_thread(generate,body)
    finally:lock.release()
    return {'id':'chatcmpl-'+uuid.uuid4().hex,'object':'chat.completion','created':int(time.time()),'model':MODEL_ID,
            'choices':[{'index':0,'message':{'role':'assistant','content':text},'finish_reason':reason}]}
