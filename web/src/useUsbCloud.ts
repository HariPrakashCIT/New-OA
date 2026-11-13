import {useEffect,useRef,useState} from 'react';
import {UsbSample} from './usbSerial';

export function useUsbCloud({enabled,api,token,deviceId,sample}:{enabled:boolean;api:string;token:string;deviceId:string;sample?:UsbSample}){
  const latest=useRef(sample);latest.current=sample;
  const [saved,setSaved]=useState(0),[lastSaved,setLastSaved]=useState(0),[error,setError]=useState('');
  useEffect(()=>{
    setSaved(0);setLastSaved(0);setError('');
    if(!enabled||!api||!token||!deviceId)return;
    let stopped=false,inFlight=false,lastAttempt:number|undefined;
    const abort=new AbortController();
    const tick=async()=>{
      const reading=latest.current;
      if(stopped||inFlight||!reading||reading.id===lastAttempt||Date.now()-Date.parse(reading.timestamp)>5000)return;
      inFlight=true;lastAttempt=reading.id;
      const request=new AbortController();
      const cancel=()=>request.abort();abort.signal.addEventListener('abort',cancel);
      const timeout=setTimeout(cancel,20000);
      try{
        const {timestamp,heel_pressure,ball_pressure,toe_pressure}=reading;
        const response=await fetch(api+'/api/devices/'+encodeURIComponent(deviceId)+'/usb-readings',{
          method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},
          body:JSON.stringify({timestamp,heel_pressure,ball_pressure,toe_pressure}),signal:request.signal
        });
        if(!response.ok)throw Error(response.status===401?'Sign in again to save USB readings.':response.status===404?'Device or USB endpoint unavailable. Refresh your connection settings.':'Cloud save failed (HTTP '+response.status+'). Check your connection; new readings will retry.');
        const body=await response.json();if(body.accepted!==true)throw Error('The backend did not confirm this reading.');
        if(!stopped){setSaved(n=>n+1);setLastSaved(Date.now());setError('')}
      }catch(e){if(!stopped)setError(e instanceof Error&&e.name!=='AbortError'?e.message:'Cloud save timed out. Live USB still works; new readings will retry.')}
      finally{clearTimeout(timeout);abort.signal.removeEventListener('abort',cancel);inFlight=false}
    };
    const timer=setInterval(()=>void tick(),1000);
    return()=>{stopped=true;clearInterval(timer);abort.abort()};
  },[enabled,api,token,deviceId]);
  return {saved,lastSaved,error};
}
