"""현재 검증 ISO의 대형 엠블럼과 같은 PGD 블록만 갱신한다."""
import json,hashlib
from inventory import ROOT,ISO,WORK
from kbo_logos import BIG,apply
from install import update_install
from ui_textures import apply as apply_text

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
 p=ROOT/'build/build_report.json';r=json.loads(p.read_text('utf8'));out=ROOT/r['iso'];assert sha(out)==r['sha256']
 inv=json.loads((WORK/'inventory.json').read_text('utf8'));entries={e['name']:e for e in inv['fbd']}
 archive=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
 install=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/INSDIR/BASEBALL.FBD')
 edits=[];reports=[]
 with ISO.open('rb') as original,out.open('rb') as current:
  for name in sorted(set(BIG)|{'PRETITCEN.CHK','PRETITPAC.CHK','PRETIT_IL.CHK'}):
   e=entries[name];original.seek(e['offset']);raw=original.read(e['size'])
   if name in BIG:new,report=apply(name,raw,True)
   else:new,_=apply_text(name,raw,True,league_trial=True);report=[]
   current.seek(e['offset']);old=current.read(e['size'])
   for q in r['kbo_logos']:
    if q['file']==name:assert old[q['offset']:q['offset']+q['size']]==bytes.fromhex(q['patched'])
   edits.append((e,old,new));reports+=report
 previous=r['sha256']
 with out.open('r+b') as f:
  audit=update_install(f,f,install,archive,[(e['offset']-archive['offset'],old,new) for e,old,new in edits])
  for e,old,new in edits:f.seek(e['offset']);f.write(new)
  for e,old,new in edits:f.seek(e['offset']);assert f.read(len(new))==new
 r['kbo_logos']=[q for q in r['kbo_logos'] if q['file'] not in BIG]+reports
 r['sha256']=sha(out);r['incremental_logo_update']=dict(base_sha256=previous,installation_validation=audit,readback=True)
 p.write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8');print(r['sha256'])
if __name__=='__main__':main()
