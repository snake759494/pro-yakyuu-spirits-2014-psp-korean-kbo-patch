"""기존 검증 빌드의 외형 영역만 재생성한다. 전체 build.py와 동일한 소스를 사용한다."""
import json,hashlib,sys
from inventory import ROOT,ISO
from build import OUT
from hanwha_visual import files,apply
from install import update_install
from pgd import PGD

def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 report=json.loads((ROOT/'build/build_report.json').read_text('utf8'));assert digest(OUT)==report['sha256']
 with_install='--with-install-data' in sys.argv
 if with_install and not report.get('installation_data_patched',False):
  raise RuntimeError('설치 데이터가 동기화되지 않은 빌드입니다. build.py --league-trial --with-install-data로 전체 빌드하세요.')
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'));entries={e['name']:e for e in inv['fbd']}
 archive=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
 install=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/INSDIR/BASEBALL.FBD')
 replacements=[];outputs=[];regions=[]
 with ISO.open('rb') as original,OUT.open('rb') as src:
  for name in sorted(files()):
   e=entries[name];original.seek(e['offset']);base=original.read(e['size']);_,rs=apply(name,base,True)
   src.seek(e['offset']);current=src.read(e['size']);patched=bytearray(current)
   for r in rs:patched[r['offset']:r['offset']+r['size']]=bytes.fromhex(r['patched'])
   regions+=rs
   if current!=patched:replacements.append((e['offset']-archive['offset'],current,patched));outputs.append((e,patched))
 with OUT.open('rb') as src,OUT.open('r+b') as dst:
  delta=update_install(src,dst,install,archive,replacements) if with_install else dict(skipped=True)
  for e,data in outputs:dst.seek(e['offset']);dst.write(data)
  dst.flush()
 with OUT.open('rb') as dst,ISO.open('rb') as original:
  for e,data in outputs:dst.seek(e['offset']);assert dst.read(e['size'])==data
  if with_install:
   dst.seek(install['offset']);pgd=PGD(dst.read(144));n=(pgd.data_size+pgd.block_size-1)//pgd.block_size
   tableoff=install['offset']+pgd.data_offset+((pgd.data_size+15)&~15)
   dst.seek(tableoff);a=dst.read(n*16);original.seek(tableoff);b=original.read(n*16)
   changed=sum(a[i:i+16]!=b[i:i+16] for i in range(0,len(a),16))
  else:
   dst.seek(install['offset']);h=hashlib.sha256();left=install['size']
   while left:
    part=dst.read(min(left,4*1024*1024));assert part;h.update(part);left-=len(part)
   report['installation_archive_sha256']=h.hexdigest()
 report['hanwha_visual']=regions;report['sha256']=digest(OUT);assert digest(ISO)==report['original_sha256']
 report['installation_data_patched']=with_install
 if with_install:report['installation_validation']['changed_blocks']=changed
 else:
  report.pop('installation_validation',None)
  report['installation_status']='기존 설치 데이터 유지; 최신 직접 읽기 데이터와 동기화하지 않음; 설치 없이 실행'
 (ROOT/'build/build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
 (ROOT/'build/hanwha_visual.json').write_text(json.dumps(regions,ensure_ascii=False,indent=2),'utf8')
 print(json.dumps(dict(sha256=report['sha256'],updated_files=[e['name'] for e,d in outputs],installation_delta=delta),ensure_ascii=False))
if __name__=='__main__':main()
