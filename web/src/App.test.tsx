import React from 'react';
import {render,screen,fireEvent,cleanup,waitFor} from '@testing-library/react';
import {describe,it,expect,vi,afterEach,beforeEach} from 'vitest';
const mock=vi.hoisted(()=>({session:null as any,defaultConfig:null as any,signIn:vi.fn(),signUp:vi.fn()}));
vi.mock('./deployment',()=>({get defaultDeployment(){return mock.defaultConfig}}));
vi.mock('@supabase/supabase-js',()=>({createClient:()=>({auth:{getSession:()=>Promise.resolve({data:{session:mock.session}}),onAuthStateChange:()=>({data:{subscription:{unsubscribe:vi.fn()}}}),signOut:()=>Promise.resolve({error:null}),signInWithPassword:mock.signIn,signUp:mock.signUp}})}));
import {App} from './main';
afterEach(()=>{cleanup();localStorage.clear();mock.session=null;vi.unstubAllGlobals()});
beforeEach(()=>{mock.defaultConfig=null;window.scrollTo=vi.fn();mock.signIn.mockResolvedValue({data:{session:null},error:new Error('Invalid login')})});

describe('Web frontend',()=>{
 it('opens sign-in directly when the hosted connection is supplied',()=>{
  mock.defaultConfig={api:'https://api.example.com',url:'https://project.supabase.co',anon:'public-only'};
  render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:'Connect insole'}));
  expect(screen.getByLabelText('Email address')).toBeTruthy();
  expect(screen.queryByRole('button',{name:'Set up backend first'})).toBeNull();
 });
 it('shows real-data empty states without fabricated telemetry',()=>{
  render(<App/>);
  expect(screen.getByText('Waiting for your first reading')).toBeTruthy();
  expect(screen.getByText('Your movement will appear here')).toBeTruthy();
  expect(screen.queryByText('6,842')).toBeNull();
  expect(screen.getByRole('img').getAttribute('aria-label')).toContain('exactly three');
 });
 it('navigates through every personal workspace page',()=>{
  render(<App/>);
  for(const name of ['Walking sessions','AI workspace','Mobility insights','Reports','History']){
   fireEvent.click(screen.getByRole('button',{name}));
   expect(screen.getByRole('heading',{level:1}).textContent).toBe(name);
  }
  fireEvent.click(screen.getByRole('button',{name:'Settings & profile'}));
  expect(screen.getByRole('heading',{name:'Your profile'})).toBeTruthy();
 });
 it('requires connection setup and rejects insecure remote endpoints',()=>{
  render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Connect insole'}));
  fireEvent.change(screen.getByLabelText('FastAPI backend URL'),{target:{value:'http://remote.example.com'}});
  fireEvent.change(screen.getByLabelText('Supabase project URL'),{target:{value:'https://test.supabase.co'}});
  fireEvent.change(screen.getByLabelText('Supabase anon / publishable key'),{target:{value:'public-key'}});
  fireEvent.submit(screen.getByRole('button',{name:'Save & continue'}).closest('form')!);
  expect(screen.getAllByText('Use HTTPS for remote connections.').length).toBeGreaterThan(0);
  expect(localStorage.getItem('osteocare-config')).toBeNull();
 });
 it('saves public configuration and opens functional authentication form',async()=>{
  render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Connect insole'}));
  fireEvent.change(screen.getByLabelText('FastAPI backend URL'),{target:{value:'https://api.example.com'}});
  fireEvent.change(screen.getByLabelText('Supabase project URL'),{target:{value:'https://test.supabase.co'}});
  fireEvent.change(screen.getByLabelText('Supabase anon / publishable key'),{target:{value:'public-key'}});
  fireEvent.submit(screen.getByRole('button',{name:'Save & continue'}).closest('form')!);
  expect(JSON.parse(localStorage.getItem('osteocare-config')!).api).toBe('https://api.example.com');
  fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'person@example.com'}});
  fireEvent.change(screen.getByLabelText('Password'),{target:{value:'password123'}});
  fireEvent.submit(screen.getByRole('button',{name:'Sign in'}).closest('form')!);
  await waitFor(()=>expect(mock.signIn).toHaveBeenCalledWith({email:'person@example.com',password:'password123'}));
  await waitFor(()=>expect(screen.getAllByText('Invalid login').length).toBeGreaterThan(0));
 });
 it('shows backend failures instead of pretending data loaded',async()=>{
  localStorage.setItem('osteocare-config',JSON.stringify({api:'https://api.example.com',url:'https://test.supabase.co',anon:'public'}));
  mock.session={access_token:'token',user:{id:'owner',email:'owner@example.com'}};
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:()=>Promise.resolve({detail:'Backend Supabase configuration is missing'})}));
  render(<App/>);
  await waitFor(()=>expect(screen.getAllByText('Backend Supabase configuration is missing').length).toBeGreaterThan(0));
  expect(screen.getByText('Waiting for your first reading')).toBeTruthy();
 });
});
