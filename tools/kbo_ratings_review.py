"""全619명 명세를 PDN/PDW에 함께 적용. 불완전 명세는 빌드를 중단한다."""
import json
from pathlib import Path
from functools import lru_cache
from analyze import chunks
from player_fields import apply_abilities,POSITIONS,PITCHES
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={'trajectory','contact_r','contact_l','power','speed','arm','catching','throwing','recovery','stamina','starter','reliever','closer'}
@lru_cache(None)
def manifest():
 d=json.loads((ROOT/'translation/kbo_2026/ratings_review.json').read_text('utf8'));seen=set()
 for code,t in d['teams'].items():
  assert len(t['opening_indices'])==29 and len(set(t['opening_indices']))==29
  for p in t['players']:
   assert REQUIRED==p['abilities'].keys(),(code,p['name'],'불완전 능력치')
   assert p['index'] not in seen;seen.add(p['index'])
   assert p['fielding'] and set(p['fielding'])<=POSITIONS.keys()
   if p['category']=='P':
    assert p['velocity']>125 and len(p['pitches'])>=2,(code,p['name'],'구속/구종 누락')
    assert any(PITCHES[q['name']][1]!=5 for q in p['pitches']),(code,p['name'],'변화구 없음')
   else:
    assert not p['pitches'] and all(p['abilities'][k]==0 for k in ('stamina','starter','reliever','closer'))
    assert min(p['abilities'][k] for k in ('contact_r','contact_l','power','arm','catching','throwing'))>=25
 assert len(seen)==619
 return d
def apply(data):
 out=bytearray(data);cs={n:o for n,o,b in chunks(out)}
 for code,t in manifest()['teams'].items():
  for p in t['players']:
   at=cs['PDN']+p['index']*192;old=out[at:at+192];r=apply_abilities(old,p)
   out[at:at+84]=r[:84];wa=cs['PDW']+p['index']*84;out[wa:wa+84]=r[:84]
   out[at+168]=(old[168]&0x87)|(p['primary_position']<<3)
   assert out[at+84:at+168]==old[84:168]
 return out
