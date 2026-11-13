// Web Serial is exposed only in supporting browsers on secure origins.
export type Pressure = {heel_pressure:number;ball_pressure:number;toe_pressure:number};
export type UsbSample = Pressure & {id:number;timestamp:string;received_at:string};
export interface SerialPort {
  readable: ReadableStream<Uint8Array>|null;
  open(options:{baudRate:number}):Promise<void>;
  close():Promise<void>;
}
export interface SerialAccess {requestPort():Promise<SerialPort>}
export const serialAccess=()=> (navigator as Navigator & {serial?:SerialAccess}).serial;

export function parseUsbLine(line:string):Pressure|null {
  if(line.length>1024)return null;
  try {
    const data=JSON.parse(line);
    if(!data||data.type!=='osteocare_reading'||data.protocol!==1)return null;
    const values=[data.heel_pressure,data.ball_pressure,data.toe_pressure];
    if(!values.every(v=>Number.isInteger(v)&&v>=0&&v<=4095))return null;
    return {heel_pressure:data.heel_pressure,ball_pressure:data.ball_pressure,toe_pressure:data.toe_pressure};
  } catch {return null}
}

// Bound untrusted serial input, including incomplete and oversized lines.
export class UsbLineDecoder {
  private buffer='';
  private discarding=false;
  push(text:string):string[] {
    const lines:string[]=[];
    for(const character of text){
      if(character==='\n'){
        if(!this.discarding&&this.buffer.trim())lines.push(this.buffer.trim());
        this.buffer='';this.discarding=false;
      }else if(!this.discarding){
        this.buffer+=character;
        if(this.buffer.length>1024){this.buffer='';this.discarding=true;}
      }
    }
    return lines;
  }
}
