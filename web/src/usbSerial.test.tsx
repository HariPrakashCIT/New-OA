import {describe,it,expect} from 'vitest';
import {parseUsbLine,UsbLineDecoder} from './usbSerial';
const valid={type:'osteocare_reading',protocol:1,heel_pressure:120,ball_pressure:300,toe_pressure:0};
describe('ESP32 USB protocol',()=>{
 it('accepts measured integer ADC values including zero',()=>{expect(parseUsbLine(JSON.stringify(valid))).toEqual({heel_pressure:120,ball_pressure:300,toe_pressure:0})});
 it('rejects boot noise, wrong firmware, missing or invalid readings',()=>{
  for(const value of [null,{}, {...valid,type:'noise'}, {...valid,protocol:2}, {...valid,heel_pressure:-1}, {...valid,toe_pressure:4096}, {...valid,ball_pressure:1.2}, {...valid,toe_pressure:'300'}, {...valid,toe_pressure:null}, {...valid,toe_pressure:true}])expect(parseUsbLine(JSON.stringify(value))).toBeNull();
  expect(parseUsbLine('rst:0x1 (POWERON_RESET)')).toBeNull();
 });
 it('reassembles split messages and separates multiple messages',()=>{
  const decoder=new UsbLineDecoder(),line=JSON.stringify(valid);
  expect(decoder.push(line.slice(0,24))).toEqual([]);
  expect(decoder.push(line.slice(24)+'\r\n'+line+'\n')).toEqual([line,line]);
 });
 it('drops oversized lines and recovers at the next newline',()=>{
  const decoder=new UsbLineDecoder(),line=JSON.stringify(valid);
  expect(decoder.push('x'.repeat(20000))).toEqual([]);
  expect(decoder.push(line+'\n'+line+'\n')).toEqual([line]);
 });
});
