"""외형 변경의 텍스처 왕복, 레코드 범위, 실제 MIPS 체형 getter 검증."""
import json,struct,unittest
from test_hanwha_roster import RosterTests
from hanwha_visual import ROOT,files,spec,decode,encode,apply
from hanwha_visual_code import patches
from hanwha_roster import apply as roster_apply
from inventory import ISO
from analyze import chunks

class VisualTests(RosterTests):
 def test_body_getter_and_preserved_abilities(self):
  original=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes()
  baseline=(ROOT/'build/baseline_before_hanwha_visual/PLAYERDATA.CHK').read_bytes()
  output,_=roster_apply(original,original)
  backups=[]
  for _,a,b,_ in patches():
   backups.append((a,bytes(self.u.mem_read(a,len(b)))));self.u.mem_write(a,b)
  try:
   for p in spec():
    o=5120+p['index']*192;r=output[o:o+192]
    # 코치 슬롯의 구종 문자열 번역은 전체 빌드에서 수행한다.
    if p['index']!=108:self.assertEqual(r[:92],baseline[o:o+92],p['name'])
    else:self.assertEqual(r[84:92],baseline[o+84:o+92],p['name'])
    self.assertEqual(r[92:104].split(b'\0')[0].decode(),p['back_name'])
    self.assertEqual(r[152],p['height'])
    self.assertEqual(self.run_getter(0x8998398,r),p['body_type'],p['name'])
    self.assertEqual(struct.unpack_from('<I',r,156)[0]&0x07ffffff,struct.unpack_from('<I',baseline,o+156)[0]&0x07ffffff)
  finally:
   for a,b in backups:self.u.mem_write(a,b)
 def test_texture_roundtrip_and_region_scope(self):
  selected=files();inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd'];count=0
  with ISO.open('rb') as f:
   for e in inv:
    if e['name'] not in selected:continue
    f.seek(e['offset']);d=f.read(e['size'])
    for _,_,b in (chunks(d) if e['name'].endswith('.CHK') else []):
     if b[:4]==b'PTXI':self.assertEqual(encode(decode(b),b),b[16:])
    out,regions=apply(e['name'],d,True);self.assertEqual(len(d),len(out))
    restored=bytearray(out)
    for r in regions:restored[r['offset']:r['offset']+r['size']]=bytes.fromhex(r['original'])
    self.assertEqual(restored,d,e['name']);count+=1
  self.assertEqual(count,94)

if __name__=='__main__':unittest.main()
