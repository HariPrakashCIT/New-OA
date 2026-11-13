import {useEffect,useRef,useState} from 'react';
import {parseUsbLine,serialAccess,SerialPort,UsbLineDecoder,UsbSample} from './usbSerial';

export function useUsbSerial(){
  const [mode,setMode]=useState(false),[connected,setConnected]=useState(false),[connecting,setConnecting]=useState(false);
  const [samples,setSamples]=useState<UsbSample[]>([]),[count,setCount]=useState(0),[invalid,setInvalid]=useState(0);
  const [error,setError]=useState(''),[clock,setClock]=useState(Date.now());
  const port=useRef<SerialPort|null>(null),reader=useRef<ReadableStreamDefaultReader<Uint8Array>|null>(null);
  const running=useRef<Promise<void>|null>(null),opening=useRef(false),generation=useRef(0),sequence=useRef(0);
  const mounted=useRef(true);
  const supported=!!serialAccess()&&window.isSecureContext!==false;
  useEffect(()=>{mounted.current=true;const timer=setInterval(()=>setClock(Date.now()),1000);return()=>{mounted.current=false;generation.current++;clearInterval(timer);void reader.current?.cancel().catch(()=>{});}},[]);
  async function disconnect(){
    generation.current++;
    try{await reader.current?.cancel()}catch{}
    await running.current;
    if(mounted.current){setConnected(false);setConnecting(false)}
  }
  async function useWifi(){await disconnect();setMode(false);setSamples([]);setCount(0);setError('')}
  async function connect(){
    if(opening.current||port.current)return;
    if(!supported){setError('USB requires desktop Chrome or Edge over HTTPS.');return}
    opening.current=true;setConnecting(true);setError('');
    const attempt=++generation.current;
    let chosen:SerialPort|undefined;
    try{
      // Keep requestPort in the direct user gesture; do not request access on page load.
      chosen=await serialAccess()!.requestPort();
      if(attempt!==generation.current||!mounted.current)return;
      await chosen.open({baudRate:115200});
      if(attempt!==generation.current||!mounted.current){await chosen.close();return}
      if(!chosen.readable){await chosen.close();throw Error('This port has no readable serial stream.')}
      port.current=chosen;
      setMode(true);setConnected(true);setSamples([]);setCount(0);setInvalid(0);setClock(Date.now());
      const input=chosen.readable.getReader();reader.current=input;
      const decoder=new TextDecoder(),lines=new UsbLineDecoder();
      const readLoop=async()=>{
        try{
          while(attempt===generation.current){
            const result=await input.read();
            if(result.done)break;
            for(const line of lines.push(decoder.decode(result.value,{stream:true}))){
              const pressure=parseUsbLine(line);
              if(!pressure){if(mounted.current)setInvalid(n=>n+1);continue}
              if(attempt!==generation.current||!mounted.current)break;
              const timestamp=new Date().toISOString();
              const sample={...pressure,id:--sequence.current,timestamp,received_at:timestamp};
              setSamples(old=>[...old,sample].slice(-1800));setCount(n=>n+1);
            }
          }
          if(attempt===generation.current&&mounted.current)setError('USB disconnected. Reconnect the cable and click Connect USB.');
        }catch{
          if(attempt===generation.current&&mounted.current)setError('USB connection lost. Check the cable, close Serial Monitor and reconnect.');
        }finally{
          input.releaseLock();reader.current=null;
          try{await chosen!.close()}catch{}
          port.current=null;
          if(mounted.current)setConnected(false);
        }
      };
      running.current=readLoop();
    }catch(e){
      if(attempt===generation.current&&mounted.current){
        const name=e && typeof e==='object' && 'name' in e?String(e.name):'';
        setError(name==='NotFoundError'?'No port selected. Click Connect USB to try again.':'Cannot open USB. Close Arduino Serial Monitor and other tabs using this port, then try again.');
      }
    }finally{opening.current=false;if(mounted.current)setConnecting(false)}
  }
  const latest=samples[samples.length-1];
  const online=connected&&!!latest&&clock-Date.parse(latest.timestamp)<5000;
  return {mode,connected,connecting,supported,samples,count,invalid,error,latest,online,connect,disconnect,useWifi};
}
export type UsbConnection=ReturnType<typeof useUsbSerial>;
