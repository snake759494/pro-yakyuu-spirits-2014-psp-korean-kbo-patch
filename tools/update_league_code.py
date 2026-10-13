"""검증된 빌드의 ELF 변경 영역만 다시 적용한다. 원본 ISO 및 PGD는 보존한다."""
import json,struct,hashlib
from pathlib import Path
from inventory import ROOT,WORK
from league_code import patches

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 rp=ROOT/'build/build_report.json';r=json.loads(rp.read_text('utf8'));out=ROOT/r['iso'];assert digest(out)==r['sha256']
 inv=json.loads((WORK/'inventory.json').read_text('utf8'));entries={Path(e['name']).name:e for e in inv['iso'] if '/UPDATE/' not in e['name']}
 old=r['league_code'];new=[];buffers={};originals={}
 with out.open('rb') as f:
  for name in {x[0] for x in patches()}|{x['file'] for x in old}:
   entry=entries['EBOOT.BIN' if name=='BOOT.BIN' else name];f.seek(entry['offset']);buffers[name]=bytearray(f.read(entry['size']));originals[name]=next((WORK/'iso').rglob(name)).read_bytes()
 for x in old:
  b=buffers[x['file']];p=x['offset'];n=x['size'];assert b[p:p+n]==bytes.fromhex(x['patched']);b[p:p+n]=bytes.fromhex(x['original'])
 for name,va,data,reason in patches():
  raw=originals[name];ph=struct.unpack_from('<I',raw,28)[0];off,base=struct.unpack_from('<2I',raw,ph+4);p=off+va-base;before=raw[p:p+len(data)];assert buffers[name][p:p+len(data)]==before
  buffers[name][p:p+len(data)]=data;new.append(dict(file=name,address=hex(va),offset=p,size=len(data),original=before.hex(),patched=data.hex(),reason=reason))
 previous=r['sha256']
 with out.open('r+b') as f:
  for name,b in buffers.items():
   e=entries['EBOOT.BIN' if name=='BOOT.BIN' else name];assert len(b)==e['size'];f.seek(e['offset']);f.write(b)
  for name,b in buffers.items():
   e=entries['EBOOT.BIN' if name=='BOOT.BIN' else name];f.seek(e['offset']);assert f.read(len(b))==b
 r['league_code']=new;r['sha256']=digest(out);r['incremental_code_update']=dict(base_sha256=previous,source='tools/league_code.py',readback=True)
 rp.write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8');(ROOT/'build/league_code.json').write_text(json.dumps(new,ensure_ascii=False,indent=2),'utf8');print(r['sha256'])
if __name__=='__main__':main()
