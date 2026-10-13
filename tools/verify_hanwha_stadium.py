"""완성 ISO에서 구장 충돌·모델·다른 구장 보존을 독립 확인한다."""
import json,struct,hashlib
from inventory import ROOT,ISO
from build import OUT
from analyze import chunks

def main():
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'));es={e['name']:e for e in inv['fbd']}
 archive=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
 with ISO.open('rb') as src,OUT.open('rb') as dst:
  def read(f,n):
   e=es[n];f.seek(e['offset']);return f.read(e['capacity'] if n=='CMIYAGI.CHK' else e['size'])
  target=read(dst,'CMIYAGI.CHK');donor=read(src,'CHIROSHIMA.CHK')
  assert target==donor
  geometry=0
  for prefix in ('D','N'):
   original=read(src,prefix+'HIROSHIMA.CHK');patched=read(dst,prefix+'MIYAGI.CHK')
   a={n:b for n,o,b in chunks(original)};b={n:b for n,o,b in chunks(patched)}
   assert a.keys()==b.keys()
   for name,data in a.items():
    if data[:4] in (b'PGOX',b'SINF'):assert b[name]==data;geometry+=1
   assert read(dst,prefix+'HIROSHIMA.CHK')==original
   assert read(dst,prefix+'HIROSHIMAM.CHK')==read(src,prefix+'HIROSHIMAM.CHK')
  assert read(dst,'CHIROSHIMA.CHK')==donor
  e=es['CMIYAGI.CHK'];dst.seek(archive['offset']+22+e['index']*268+256)
  lba,size,capacity=struct.unpack('<3I',dst.read(12))
  assert lba*2048+archive['offset']==e['offset'] and size==112640 and size==capacity==e['capacity']
  boot=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/SYSDIR/EBOOT.BIN')
  dst.seek(boot['offset']+0x2cdcc4);record=dst.read(228)
  assert struct.unpack_from('<I',record)[0]==12
  assert struct.unpack_from('<4f',record,32)==(122.0,101.0,100.0,2.5)
  assert record[19]==0
  schedule=dict((n,b) for n,o,b in chunks(read(dst,'SCHEDULE.CHK')))['OFFICIAL'];home=0
  for day in range(241):
   for slot in range(6):
    r=schedule[day*60+slot*5:day*60+slot*5+5]
    if r[0]==6:assert r[2]==12;home+=1
  assert home==72
 with OUT.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 result=dict(passed=True,iso_sha256=digest,geometry_chunks_preserved=geometry,collision_matches_model=True,other_stadium_assets_preserved=True,hanwha_home_games=home,stadium_slot=12,dimensions=dict(center=122,left=101,right=100,fence=2.5),natural_grass=True,archive_entry_growth_inside_original_capacity=True)
 (ROOT/'build/face_stadium/stadium_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
