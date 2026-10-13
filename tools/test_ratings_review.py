"""실제 원본 MIPS getter로 전 선수의 능력치와 구종을 검증한다."""
import json,struct,unittest,hashlib
from pathlib import Path
from test_hanwha_roster import RosterTests
from kbo_ratings_review import manifest,ROOT
from kbo_rosters import apply
from kbo_team_layout import layouts,patches
from player_fields import get,POSITIONS,PITCHES
from analyze import chunks
class CompleteRatingsTests(RosterTests):
 # 상속된 한화 과거 명세 테스트는 이 전수 검증과 별도 실행한다.
 test_scope_roster_and_identity=None
 test_age_correction_and_dh_cave=None
 test_registered_names_with_original_formatter=None
 def test_complete_manifest_and_original_getters(self):
  original=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();out,_=apply(original,original)
  cs={n:(o,b) for n,o,b in chunks(out)};oldcs={n:b for n,o,b in chunks(original)};count=0
  getters={'power':0x88ec6f4,'contact_r':0x88ec7fc,'speed':0x88ec9ac,'arm':0x88ecaa8,'catching':0x88ecc9c,'throwing':0x88ecba0,'recovery':0x88ecd98}
  for code,t in manifest()['teams'].items():
   for p in t['players']:
    i=p['index'];r=cs['PDN'][1][i*192:(i+1)*192]
    for k,a in getters.items():self.assertEqual(self.run_getter(a,r,0,0),p['abilities'][k],(code,p['name'],k))
    self.assertEqual(self.run_getter(0x88ec7fc,r,0,1),p['abilities']['contact_l'])
    for j,k in enumerate(POSITIONS):self.assertEqual(self.run_getter(0x88ec5b0,r,j),p['fielding'].get(k,0),(code,p['name'],k))
    self.assertEqual(self.run_getter(0x88ecfc0,r,0),p['velocity'])
    kinds=[self.run_getter(0x88ed5f8,r,j) for j in range(12)]
    self.assertEqual(sorted(x for x in kinds if x!=37),sorted(PITCHES[q['name']][0] for q in p['pitches']),(code,p['name']))
    self.assertEqual(cs['PDW'][1][i*84:(i+1)*84],r[:84]);self.assertEqual(r[84:90],oldcs['PDN'][i*192+84:i*192+90])
    self.assertEqual((r[168]&0x78)>>3,p['primary_position']);count+=1
  self.assertEqual(count,619)
 def test_official_opening_290_ids(self):
  official=json.loads((ROOT/'work/ratings_review/opening.json').read_text('utf8'))
  for code,t in layouts().items():
   self.assertEqual({p['player_id'] for p in t['active']},{p['player_id'] for p in official[code]},code)
   self.assertEqual(len(t['active']),29)
   self.assertFalse({p['index'] for p in t['players']} & {p['index'] for p in t['coaches']})
   # 編成の先発/救援スロットIDが29人の投手と完全一致。
   b=next(b for f,a,b,label in patches() if f=='BOOT.BIN' and a==0x8a936d8+t['team_id']*136)
   ids=[struct.unpack_from('<I',b,j*8)[0] for j in range(17) if struct.unpack_from('<I',b,j*8)[0]]
   self.assertEqual(set(ids),{p['game_id'] for p in t['pitchers']});self.assertEqual(len(ids),len(set(ids)))
if __name__=='__main__':unittest.main()
