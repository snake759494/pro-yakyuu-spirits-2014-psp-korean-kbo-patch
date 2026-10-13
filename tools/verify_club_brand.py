"""구단별 모델/홈 연결/자원 적용 및 승인된 한화·LG 회귀 검사."""
import json,hashlib,struct
from inventory import ROOT,ISO
from build import OUT
from analyze import chunks
from club_brand import configs,find
from club_stadium import resources

def main():
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'));es={e['name']:e for e in inv['fbd']};boot=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/SYSDIR/EBOOT.BIN')
 results=[]
 with ISO.open('rb') as src,OUT.open('rb') as dst:
  def read(f,n):e=es[n];f.seek(e['offset']);return f.read(e['size'])
  dst.seek(boot['offset']);exe=dst.read(boot['size']);original=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
  for code,c in configs().items():
   slot=c['stadium_slot'];tid=c['team_id'];assert struct.unpack_from('<I',exe,0x2846a0+tid*4)[0]==slot
   at=0x2cd214+slot*228;donor_at=0x2cd214+c.get('donor_slot',slot)*228
   assert exe[at:at+16]==original[at:at+16]
   assert exe[at+16:at+228]==original[donor_at+16:donor_at+228]
   if c.get('resource_labels'):
    for i,label in enumerate(c['resource_labels']*2):
     ptr=struct.unpack_from('<I',exe,0x3130b8+slot*16+i*4)[0];off=ptr-0x8804000+0x1018
     assert exe[off:off+len(label)+1]==label.encode()+b'\0'
   geometry=0
   for n,donor in resources(c).items():
    if n.startswith('C'):
     raw=read(src,donor);assert read(dst,n)==raw+bytes(es[n]['size']-len(raw));continue
    old={n:b for n,o,b in chunks(read(src,donor))};new={n:b for n,o,b in chunks(read(dst,n))}
    if n.endswith('M.CHK'):
     from club_scoreboard import apply as scoreboard
     expected,_=scoreboard(n,read(src,donor));wanted={n:b for n,o,b in chunks(expected)}
     for key in ('T_TMMK1','P_TMMK1','T_TMMK2','P_TMMK2'):
      if key in wanted:assert new[key]==wanted[key],(code,n,key)
     if n in c.get('aux_light_sources',{}):
      night={n:b for n,o,b in chunks(read(src,c['aux_light_sources'][n]))};assert new['LIGHTS']==night['LIGHTS']
    for key,b in old.items():
     if b[:4] in (b'SINF',b'PGOX'):assert new[key]==b;geometry+=1
   changed=[]
   for n in es:
    if find(n)==code:assert read(src,n)!=read(dst,n),n;changed.append(n)
   schedule=next(b for n,o,b in chunks(read(dst,'SCHEDULE.CHK')) if n=='OFFICIAL');home=0
   for day in range(241):
    for match in range(6):
     r=schedule[day*60+match*5:day*60+match*5+5]
     if r[0]==tid:assert r[2]==slot;home+=1
   assert home==72
   results.append(dict(code=code,home_games=home,home_slot=slot,model=c['stadium_model'],geometry_chunks_preserved=geometry,collision_preserved=True,uniform_files_changed=changed))
  baseline=json.loads((ROOT/'build/ss_brand/approved_resource_hashes.json').read_text('utf8'))
  for n,h in baseline['resources'].items():assert hashlib.sha256(read(dst,n)).hexdigest()==h,('승인된 한화/LG 자원이 변경됨',n)
 with OUT.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 r=dict(passed=True,iso_sha256=digest,teams=results,approved_hh_lg_resources_unchanged=len(baseline['resources']))
 (ROOT/'build/club_brand/static_validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8');print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
