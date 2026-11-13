import {act,renderHook,cleanup} from '@testing-library/react';
import {it,expect,vi,afterEach} from 'vitest';
import {useUsbCloud} from './useUsbCloud';
const sample=(id:number)=>({id,timestamp:new Date().toISOString(),received_at:new Date().toISOString(),heel_pressure:12,ball_pressure:34,toe_pressure:56});
afterEach(()=>{cleanup();vi.useRealTimers();vi.unstubAllGlobals()});
it('saves only when enabled, sends to the selected account device and recovers after a failure',async()=>{
 vi.useFakeTimers();
 const fetch=vi.fn().mockResolvedValueOnce({ok:false,status:503}).mockResolvedValue({ok:true,json:async()=>({accepted:true})});vi.stubGlobal('fetch',fetch);
 let props={enabled:false,api:'https://api.example',token:'test-token',deviceId:'D1',sample:sample(-1)};
 const {result,rerender}=renderHook(p=>useUsbCloud(p),{initialProps:props});
 await act(()=>vi.advanceTimersByTimeAsync(1000));expect(fetch).not.toHaveBeenCalled();
 props={...props,enabled:true,sample:sample(-2)};rerender(props);
 await act(()=>vi.advanceTimersByTimeAsync(1000));expect(result.current.saved).toBe(0);expect(result.current.error).toContain('503');
 props={...props,sample:sample(-3)};rerender(props);
 await act(()=>vi.advanceTimersByTimeAsync(1000));expect(result.current.saved).toBe(1);expect(result.current.error).toBe('');
 const [url,request]=fetch.mock.calls[1];expect(url).toBe('https://api.example/api/devices/D1/usb-readings');expect(request.headers.Authorization).toBe('Bearer test-token');
 expect(JSON.parse(request.body)).toEqual({timestamp:props.sample.timestamp,heel_pressure:12,ball_pressure:34,toe_pressure:56});
 await act(()=>vi.advanceTimersByTimeAsync(1000));expect(fetch).toHaveBeenCalledTimes(2);
 rerender({...props,enabled:false,sample:sample(-4)});
 await act(()=>vi.advanceTimersByTimeAsync(1000));expect(fetch).toHaveBeenCalledTimes(2);
});
it('cancels in-flight saves when disabled and does not count them as confirmed',async()=>{
 vi.useFakeTimers();let signal:AbortSignal;
 vi.stubGlobal('fetch',vi.fn().mockImplementation((_url,request)=>{signal=request.signal;return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError'))))}));
 const props={enabled:true,api:'https://api.example',token:'test-token',deviceId:'D1',sample:sample(-1)};
 const {result,rerender}=renderHook(p=>useUsbCloud(p),{initialProps:props});
 await act(()=>vi.advanceTimersByTimeAsync(1000));rerender({...props,enabled:false});
 expect(signal!.aborted).toBe(true);expect(result.current.saved).toBe(0);
});
