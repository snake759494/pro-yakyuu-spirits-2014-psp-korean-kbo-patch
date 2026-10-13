"""실행 중 RAM을 읽기만 하여 한화 선수단의 원본/페넌트 복사본을 대조한다."""
import json,hashlib
from pathlib import Path
from ppsspp_rpc import Debugger,readmem
from hanwha_roster import ROOT,load

def main():
 report=json.loads((ROOT/'build/build_report.json').read_text('utf8'))
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'))
 entry=next(e for e in inv['fbd'] if e['name']=='PLAYERDATA.CHK')
 with (ROOT/report['iso']).open('rb') as f:
  f.seek(entry['offset']);data=f.read(entry['size'])
 d=Debugger()
 try:
  d.call('cpu.stepping')
  try:ram=readmem(d,0x08800000,0x01800000)
  finally:d.call('cpu.resume')
 finally:d.close()
 rows=[]
 for p in load()['records']:
  o=5120+p['index']*192;r=data[o:o+192];needle=r[110:152];at=0;copies=[]
  while (at:=ram.find(needle,at))>=0:
   base=at-110;actual=ram[base:base+192]
   if actual[84:92]==r[84:92]:
    differences=[i for i in range(192) if actual[i]!=r[i]]
    auto_duplicate=(p['name']=='박준영' and differences==[161] and actual[161]^r[161]==0x20)
    copies.append(dict(address=hex(0x08800000+base),differences=differences,expected_duplicate_name_adjustment=auto_duplicate,roster_fields_match=not differences or auto_duplicate,registered_name_selector=(actual[161]>>5)&7,jersey_raw=actual[160:162].hex()))
   at+=len(needle)
  rows.append(dict(name=p['name'],index=p['index'],copies=copies))
 result=dict(iso_sha256=report['sha256'],read_only=True,state='한화 선수단 확인; 실행 모드는 runtime_validation.json 참고',records=rows,
  records_found=sum(bool(r['copies']) for r in rows),all_copies_match=all(r['copies'] and all(not c['differences'] for c in r['copies']) for r in rows),
  all_roster_fields_match=all(r['copies'] and all(c['roster_fields_match'] for c in r['copies']) for r in rows))
 (ROOT/'build/hanwha_live_records.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
 print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))
 print([(r['name'],r['copies']) for r in rows if any(c['differences'] for c in r['copies'])])
if __name__=='__main__':main()
