import React from 'react';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import {GemmaStatus,GemmaExplanationPanel} from './GemmaPanel';

it('labels the configured free model accurately',()=>{
 render(<GemmaStatus info={{configured:true,model:'google/gemma-4-26b-a4b-it:free',message:'Configured'}} onSetup={()=>{}}/>);
 expect(screen.getByRole('heading',{name:'Gemma 4 26B A4B (free) report explanations'})).toBeTruthy();
});
afterEach(cleanup);
it('shows inactive hosting without claiming live inference',()=>{
 render(<GemmaStatus info={{configured:false,model:'google/gemma-4-26b-a4b-it:free',message:'Model hosting is not configured.'}} onSetup={()=>{}}/>);
 expect(screen.getByText('NOT ACTIVE')).toBeTruthy();
 expect(screen.getByText('Model hosting is not configured.')).toBeTruthy();
});
it('requires both configured hosting and user consent before generation',()=>{
 const generate=vi.fn(),consent=vi.fn();
 const {rerender}=render(<GemmaExplanationPanel configured={true} samples={12} busy={false} consent={false} onConsent={consent} onGenerate={generate}/>);
 expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
 fireEvent.click(screen.getByRole('checkbox'));expect(consent).toHaveBeenCalledWith(true);
 rerender(<GemmaExplanationPanel configured={true} samples={12} busy={false} consent={true} onConsent={consent} onGenerate={generate}/>);
 fireEvent.click(screen.getByRole('button'));expect(generate).toHaveBeenCalledOnce();
});
it('renders saved model text as plain text with provenance',()=>{
 render(<GemmaExplanationPanel configured={true} samples={12} busy={false} consent={false} onConsent={()=>{}} onGenerate={()=>{}} explanation={{text:'<img src=x onerror=alert(1)>',model:'google/gemma-4-26b-a4b-it:free',generated_at:'2026-11-13T00:00:00Z',disclaimer:'AI text can contain errors.'}}/>);
 expect(screen.queryByRole('img')).toBeNull();expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeTruthy();
 expect(screen.getByText('AI text can contain errors.')).toBeTruthy();
});
