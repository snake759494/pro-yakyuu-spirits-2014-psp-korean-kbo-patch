"""최종 ISO의 LG 홈 모델 연결, 이름, 약칭, 물리 데이터와 자원 누락 검사."""
import json,struct,hashlib
from inventory import ROOT,ISO
from build import OUT
from analyze import chunks
from kbo_identity import TEAMS,texture_short
def main():
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'));es={e['name']:e for e in inv['fbd']};boot=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/SYSDIR/EBOOT.BIN')
 cm={x['hangul']:bytes.fromhex(x['code']) for x in json.loads((ROOT/'build/charmap.json').read_text('utf8')) if 'hangul' in x}
 def enc(s):return b''.join(cm[c] if c in cm else c.encode('cp932') for c in s)
 with ISO.open('rb') as src,OUT.open('rb') as dst:
  def read(f,n):e=es[n];f.seek(e['offset']);return f.read(e['size'])
  original=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();dst.seek(boot['offset']);patched=dst.read(boot['size'])
  a=0x2cd214+7*228
  assert struct.unpack_from('<I',patched,0x2846a0)[0]==7
  assert patched[a:a+228]==original[a:a+228]
  for j,pointer in enumerate(struct.unpack_from('<2I',patched,a+8)):
   off=pointer-0x8804000+0x1018;expected='서울 잠실야구장' if j==0 else '잠실'
   assert patched[off:off+len(enc(expected))+1]==enc(expected)+b'\0'
  geometry=0
  for file in ('DCHIBA.CHK','NCHIBA.CHK'):
   old={n:b for n,o,b in chunks(read(src,file))};new={n:b for n,o,b in chunks(read(dst,file))}
   for n,raw in old.items():
    if raw[:4] in (b'SINF',b'PGOX'):assert raw==new[n];geometry+=1
  assert read(src,'CCHIBA.CHK')==read(dst,'CCHIBA.CHK')
  assert read(src,'DTOKYO.CHK')==read(dst,'DTOKYO.CHK')
  locations=json.loads((ROOT/'translation/kbo_names.json').read_text('utf8'))['locations'];shorts=[]
  for i,(code,asset,short) in enumerate(TEAMS):
   for loc in locations[i*2:i*2+2]:
    assert loc['ko']==short
    assert patched[loc['offset']:loc['offset']+len(enc(short))+1]==enc(short)+b'\0'
   for side in ('H','V'):assert texture_short(f'TEAM{asset}_{side}.CHK')==short
   shorts.append(short)
  changed=[]
  for name in es:
   if 'N00G_' in name or name in ('TMSEL.CHK','TMSELUNIG.CHK','SOLHBGG.CHK','TEAMG_H.CHK','TEAMG_V.CHK'):
    assert read(src,name)!=read(dst,name),name;changed.append(name)
  schedule={n:b for n,o,b in chunks(read(dst,'SCHEDULE.CHK'))}['OFFICIAL'];home=0
  for day in range(241):
   for slot in range(6):
    row=schedule[day*60+slot*5:day*60+slot*5+5]
    if row[0]==0:assert row[2]==7;home+=1
  assert home==72
 with OUT.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 r=dict(passed=True,iso_sha256=digest,lg_home_games=home,home_slot=7,resource_model='CHIBA',collision_preserved=True,geometry_chunks_preserved=geometry,model_dimensions=dict(left=99.5,right=99.5,center=122),one_character_labels=shorts,lg_resource_files_changed=changed)
 (ROOT/'build/lg_brand/static_validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8');print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
