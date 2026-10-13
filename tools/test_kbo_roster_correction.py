"""KBO 포지션 분류와 감독/코치 원본 슬롯을 전수 검증한다."""
import json
import unittest
from pathlib import Path

from analyze import chunks
from kbo_roster_slots import STAFF_SLOTS
from kbo_rosters import apply, set_position_category
from player_fields import POSITIONS, get

ROOT = Path(__file__).resolve().parents[1]
TEAM_CODES = ('LG', 'SS', 'HT', 'WO', 'KT', 'LT', 'HH', 'OB', 'SK', 'NC')
TEAM_IDS = {'LG':0,'SS':1,'HT':2,'WO':3,'KT':4,'LT':5,'HH':6,'OB':7,'SK':8,'NC':9}
MANAGER_NAMES_JA = {
    'LG':'原辰徳','SS':'谷繁元信','HT':'野村謙二郎','WO':'小川淳司',
    'KT':'中畑清','LT':'和田豊','HH':'星野仙一','OB':'栗山英樹',
    'SK':'伊原春樹','NC':'森脇浩司',
}
EXPECTED_FIELDING = {
    'P':{'P':55}, 'C':{'C':55},
    'IF':{'1B':45,'2B':45,'3B':45,'SS':45},
    'OF':{'LF':45,'CF':45,'RF':45},
}

def grouped_fielding(row):
    if get(row,'P'):
        return 'P'
    if get(row,'C'):
        return 'C'
    if max(get(row,k) for k in ('LF','CF','RF')):
        return 'OF'
    return 'IF'


class KboRosterCorrectionTests(unittest.TestCase):
    def test_position_writer_clears_every_incompatible_old_flag(self):
        for category, expected in EXPECTED_FIELDING.items():
            row = bytearray(192)
            for field in POSITIONS:
                from player_fields import put
                put(row, field, 90)
            set_position_category(row, category)
            self.assertEqual({k:get(row,k) for k in POSITIONS},
                             {k:expected.get(k,0) for k in POSITIONS}, category)

    def test_every_team_has_the_correct_manager_and_four_coach_slots(self):
        source = json.loads((ROOT/'translation/players.json').read_text('utf8'))
        japanese = {r['index']:''.join(r.get('ja',[])) for r in source if r.get('chunk')=='PDN'}
        original = (ROOT/'work/assets/PLAYERDATA.CHK').read_bytes()
        pdn = {n:b for n,o,b in chunks(original)}['PDN']
        for code in TEAM_CODES:
            manager, coaches = STAFF_SLOTS[code]
            self.assertEqual(japanese[manager], MANAGER_NAMES_JA[code], code)
            self.assertEqual(pdn[manager*192+90]&63, TEAM_IDS[code], code)
            self.assertEqual(len(coaches), 4, code)
            self.assertEqual(len(set((manager,*coaches))), 5, code)
            for index in coaches:
                self.assertEqual(pdn[index*192+90]&63, TEAM_IDS[code], (code,index))
            spec=json.loads((ROOT/f'translation/kbo_2026/{code}.json').read_text('utf8')) if code!='HH' else json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))
            rows=[r for r in spec['records'] if r['kind']=='coach']
            self.assertEqual(len(rows),5,code)
            self.assertEqual(sum(r.get('role')=='감독' for r in rows),1,code)
            if code=='LG' and spec.get('fresh_layout'):
                self.assertEqual(next(r['index'] for r in rows if r['role']=='감독'),manager)
                self.assertEqual([r['index'] for r in rows if r['role']!='감독'],list(coaches))
                self.assertEqual([r['name'] for r in rows],['염경엽','김광삼','모창민','김일경','송지만'])
            elif code!='HH':
                self.assertEqual(spec['manager_index'],manager,code)
                self.assertEqual(spec['coach_only_indices'],list(coaches),code)
                self.assertEqual(next(r['name'] for r in rows if r.get('role')=='감독'),spec['all_official_staff'][0]['name'],code)
                self.assertEqual(len({r['name'] for r in rows}),5,code)
                player_rows=[r for r in spec['records'] if r['kind']=='player']
                duplicate_names={name for name in (r['name'] for r in player_rows) if sum(x['name']==name for x in player_rows)>1}
                self.assertTrue(all(sum(x['name']==name for x in player_rows)==2 for name in duplicate_names),code)
                self.assertEqual({r['category'] for r in player_rows}, {'P','C','IF','OF'},code)
        han=json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))
        han_staff=[r for r in han['records'] if r['kind']=='coach']
        self.assertEqual(sum(r['role']=='감독' for r in han_staff),1)
        self.assertEqual(next(r['name'] for r in han_staff if r['role']=='감독'),'김경문')

    def test_patched_player_positions_match_all_nine_kbo_groups(self):
        original=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes()
        patched,report=apply(original,original)
        chunks_by_name={n:o for n,o,b in chunks(original)}
        pd=chunks_by_name['PDN']; wd=chunks_by_name['PDW']
        specs={c:json.loads((ROOT/f'translation/kbo_2026/{c}.json').read_text('utf8'))
               for c in TEAM_CODES if c!='HH'}
        specs['HH']=json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))
        for code,spec in specs.items():
            for p in spec['records']:
                if p['kind']!='player' or (code=='HH' and p.get('kind')!='player'):
                    continue
                row=patched[pd+p['index']*192:pd+p['index']*192+192]
                from kbo_ratings_review import manifest
                expected=next(q['fielding'] for q in manifest()['teams'][code]['players'] if q['index']==p['index'])
                self.assertEqual({k:get(row,k) for k in POSITIONS},
                                 {k:expected.get(k,0) for k in POSITIONS},
                                 (code,p['index'],p['name'],p['category']))
                self.assertEqual(row[84:90],original[pd+p['index']*192+84:pd+p['index']*192+90])
                self.assertEqual(patched[wd+p['index']*84:wd+p['index']*84+84],row[:84],
                                 (code,p['index'],'PDN/PDW mismatch'))
        self.assertEqual(report['assigned_staff'],50)


if __name__=='__main__':
    unittest.main()
