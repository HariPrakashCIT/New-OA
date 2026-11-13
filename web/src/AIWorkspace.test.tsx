import React from 'react';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import {AIWorkspace} from './AIWorkspace';
afterEach(cleanup);
const info={configured:false,model:'google/gemma-4-26b-a4b-it:free',message:'No host'};
const analysis={samples:12,shares:[40,35,25],observations:['Twelve samples recorded.'],recommendations:[],disclaimer:'Not a medical assessment.'};
const report={id:'R1',period:'day',created_at:'2026-11-13T00:00:00Z',analysis};
function props(){return {reports:[] as typeof report[],info,busy:false,signedIn:false,hasDevice:false,consent:{},onConsent:vi.fn(),onExplain:vi.fn(),onCreate:vi.fn(),onConnect:vi.fn()}}
it('provides an honest empty workspace and a connection action',()=>{
 const p=props();render(<AIWorkspace {...p}/>);
 expect(screen.getByText('Model not connected')).toBeTruthy();
 expect(screen.getByText('Your story starts with a report')).toBeTruthy();
 expect((screen.getByRole('button',{name:'Daily'}) as HTMLButtonElement).disabled).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'Set up your workspace'}));expect(p.onConnect).toHaveBeenCalledOnce();
});
it('selects a report and keeps measured values separate from AI',()=>{
 const p=props();p.reports=[report,{...report,id:'R2',period:'month',analysis:{...analysis,samples:24,observations:['Twenty-four samples recorded.']}}];
 render(<AIWorkspace {...p} signedIn hasDevice/>);
 expect(screen.getByText('Twelve samples recorded.')).toBeTruthy();
 expect(screen.getByText('40%')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:/Monthly mobility report/}));
 expect(screen.getByText('Twenty-four samples recorded.')).toBeTruthy();
 expect(screen.queryByText('Twelve samples recorded.')).toBeNull();
 expect((screen.getByRole('button',{name:'Explain with Gemma'}) as HTMLButtonElement).disabled).toBe(true);
});
it('creates a real report through its supplied action',()=>{
 const p=props();render(<AIWorkspace {...p} signedIn hasDevice/>);
 fireEvent.click(screen.getByRole('button',{name:'Weekly'}));expect(p.onCreate).toHaveBeenCalledWith('week');
});
it('uses consent for the selected report when requesting an explanation',()=>{
 const p=props();render(<AIWorkspace {...p} reports={[report]} info={{...info,configured:true}} signedIn hasDevice consent={{R1:true}}/>);
 fireEvent.click(screen.getByRole('button',{name:'Explain with Gemma'}));expect(p.onExplain).toHaveBeenCalledWith(report);
 fireEvent.click(screen.getByRole('checkbox'));expect(p.onConsent).toHaveBeenCalledWith('R1',false);
});
