"""새 데이터가 두 능력 테이블 및 고정 신원 필드와 모순되지 않는지 검사."""
import json,struct,unittest
from inventory import ROOT
from analyze import chunks
from kbo_rosters import apply,specs
from player_fields import get,jersey_code
class LGDetailsTests(unittest.TestCase):
 def test_lg_records(self):
  original=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();out,_=apply(original,original)
  cs={n:o for n,o,b in chunks(original)};rows=specs()['LG']['records']
  self.assertEqual(len(rows),68)
  for p in rows:
   at=cs['PDN']+p['index']*192;r=out[at:at+192]
   self.assertEqual(r[84:90],original[at+84:at+90],p['name'])
   self.assertEqual(r[92:104].split(b'\0')[0].decode(),p['back_name'])
   self.assertEqual(get(r,'height'),p['height'])
   self.assertEqual(get(r,'jersey'),jersey_code(p['number']))
   self.assertEqual(struct.unpack_from('<I',r,156)[0]>>27,p['body_type'])
   self.assertEqual((struct.unpack_from('<I',r,152)[0]>>23)&7,p['skin_type'])
   if p['kind']=='player':
    self.assertEqual(r[:84],out[cs['PDW']+p['index']*84:cs['PDW']+(p['index']+1)*84])
    for k,v in p['ratings'].items():
     if k not in ('pitches','velocity'):self.assertEqual(get(r,k),v,(p['name'],k))
    if p['category']=='P':self.assertGreaterEqual(get(r,'velocity_raw')+80,140)
    else:self.assertEqual(get(r,'P'),0)
if __name__=='__main__':unittest.main()
