"""전체 빌드와 같은 로고 생성기로 기존 DEV의 로고 영역만 재생성한다."""
import json
from inventory import ROOT,ISO
from build import OUT,sha
from kbo_logos import FILES,apply

def main():
 report=json.loads((ROOT/'build/build_report.json').read_text('utf8'))
 assert sha(OUT)==report['sha256'] and sha(ISO)==report['original_sha256']
 entries={e['name']:e for e in json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd']}
 outputs=[];regions=[]
 with ISO.open('rb') as original,OUT.open('rb') as current:
  for name in sorted(FILES):
   e=entries[name];original.seek(e['offset']);base=original.read(e['size'])
   _,rs=apply(name,base,True);regions+=rs
   current.seek(e['offset']);old=current.read(e['size']);new=bytearray(old)
   for r in rs:new[r['offset']:r['offset']+r['size']]=bytes.fromhex(r['patched'])
   assert len(new)==len(old)
   if new!=old:outputs.append((e,new))
 with OUT.open('r+b') as f:
  for e,data in outputs:f.seek(e['offset']);f.write(data)
 with OUT.open('rb') as f:
  for e,data in outputs:f.seek(e['offset']);assert f.read(e['size'])==data
 report['kbo_logos']=regions;report['sha256']=sha(OUT);report['readback']=True
 (ROOT/'build/build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
 print(json.dumps(dict(sha256=report['sha256'],updated_files=[e['name'] for e,_ in outputs],installation_data_rebuilt=False),ensure_ascii=False))
if __name__=='__main__':main()
