"""2026 시즌 종료 기준 신원 필드가 최종 PLAYERDATA에 그대로 들어갔는지 619명 전수 검사."""
import json,struct,unittest
from pathlib import Path
from analyze import chunks
from player_fields import get,jersey_code
from kbo_rosters import apply
ROOT=Path(__file__).resolve().parents[1]
class SeasonEnd2026(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  o=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();out,_=apply(o,o)
  cls.pd={n:b for n,a,b in chunks(out)}['PDN'];cls.ident=json.loads((ROOT/'work/ratings_review/identities.json').read_text('utf8'))
  cls.specs={c:{r['index']:r for r in json.loads((ROOT/('translation/hanwha_2026.json' if c=='HH' else f'translation/kbo_2026/{c}.json')).read_text('utf8'))['records']} for c in cls.ident}
 def test_identity_fields(self):
  n=0
  for code,ps in self.ident.items():
   for p in ps:
    r=self.pd[p['index']*192:(p['index']+1)*192];who=(code,p['name'])
    y,m,d=map(int,p['birth'].split('-'));v=struct.unpack_from('<H',r,104)[0]
    self.assertEqual((v&127,(v>>7)&15,v>>11),(y-1900,m,d),who)
    if p.get('hands'):
     self.assertEqual(get(r,'throw_hand'),1 if p['hands'].startswith('좌') else 0,who)
     self.assertEqual(get(r,'bat_hand'),2 if '양타' in p['hands'] else 1 if p['hands'].endswith('좌타') else 0,who)
    self.assertEqual(bool(r[155]&0x80),bool(p['foreign']),who)
    self.assertEqual(r[92:104].rstrip(b'\0').decode(),self.specs[code][p['index']]['back_name'],who)
    if p.get('number'):self.assertEqual(get(r,'jersey'),jersey_code(str(p['number'])),who)
    n+=1
  self.assertEqual(n,619)
 def test_skin_palette(self):
  app=json.loads((ROOT/'translation/kbo_2026/appearance.json').read_text('utf8'))
  for p in app:
   v=struct.unpack_from('<I',self.pd,p['index']*192+152)[0]
   self.assertEqual((v>>23)&7,p['skin_type'],p['name']);self.assertEqual(p['skin_reference_head'],p['skin_type']+1)
 def test_unique_display_names(self):
  for code,ps in self.ident.items():
   names=[''.join(p['name'].split()) for p in ps];self.assertEqual(len(names),len(set(names)),code)
if __name__=='__main__':unittest.main()
