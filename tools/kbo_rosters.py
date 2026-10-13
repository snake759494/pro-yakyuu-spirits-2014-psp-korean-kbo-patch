"""2026 KBO 전체 선수단과 게임의 선수/코칭 슬롯을 연결한다."""
import json,struct,hashlib
from pathlib import Path
from analyze import chunks
from player_fields import put,jersey_code,POSITIONS
ROOT=Path(__file__).resolve().parents[1];DIR=ROOT/'translation/kbo_2026'
TEAMS=['LG','SS','HT','WO','KT','LT','HH','OB','SK','NC']

def set_position_category(record, category):
    """Remove inherited Japanese role flags and write the official KBO group."""
    fielding={
      'P':{'P':55},
      'C':{'C':55},
      'IF':{'1B':45,'2B':45,'3B':45,'SS':45},
      'OF':{'LF':45,'CF':45,'RF':45},
    }
    assert category in fielding,category
    for name in POSITIONS:put(record,name,0)
    for name,value in fielding[category].items():put(record,name,value)

def specs():
    result={t:json.loads((DIR/f'{t}.json').read_text('utf8')) for t in TEAMS}
    path=ROOT/'translation/lg_2026/details.json'
    if path.exists():
        details={p['index']:p for p in json.loads(path.read_text('utf8'))}
        for p in result['LG']['records']:
            d=details[p['index']];assert d['name']==p['name']
            p.update({k:v for k,v in d.items() if k not in ('name','index')});p.update(d.get('ratings',{}))
    return result
def filter_rows(rows):
    selected={int(p['index']) for c,s in specs().items() if c!='HH' for p in s['records']}
    selected.update(int(p['index']) for p in json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))['records'])
    def keep(r):
        if r.get('file')!='PLAYERDATA.CHK':return True
        o=r['offset']
        for base,stride in ((5120,192),(486816,84)):
            i,within=divmod(o-base,stride)
            if i in selected and 0<=within<84:return False
        return True
    return [r for r in rows if keep(r)]

def override_names(rows):
    maps={int(p['index']):p['name'] for c,s in specs().items() if c!='HH' for p in s['records']}
    han=json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))
    maps.update({int(p['index']):p['name'] for p in han['records']})
    out=[];seen=set()
    for r in rows:
        if r.get('chunk')=='PDN' and r.get('index') in maps:
            r=dict(r,ko=[maps[r['index']],'']);seen.add(r['index'])
        out.append(r)
    for i,name in maps.items():
        if i not in seen:out.append(dict(file='PLAYERDATA.CHK',chunk='PDN',index=i,offset=5120+i*192+110,ja=[],ko=[name,'']))
    return out

def apply(original,translated):
    out=bytearray(translated);cs={n:(o,b) for n,o,b in chunks(original)};pd=cs['PDN'][0];wd=cs['PDW'][0];reports=[];total=0
    total_players=0;total_staff=0;vacated=0;borrowed=0;team_counts={}
    for code,spec in specs().items():
        if code=='HH':continue
        for p in spec['records']:
            i=p['index'];base=pd+i*192;old=original[base:base+192];r=bytearray(old)
            assert old[90]&63 in (spec['team_id'],31 if p.get('borrowed') else spec['team_id']), (code,i,old[90]&63)
            if p.get('birth'):
                y,m,d=map(int,p['birth'].split('-'));struct.pack_into('<H',r,104,(y-1900)|(m<<7)|(d<<11))
            if p.get('height'):put(r,'height',min(255,p['height']))
            if p.get('hands'):
                put(r,'throw_hand',1 if p['hands'].startswith('좌') else 0);put(r,'bat_hand',2 if '양타' in p['hands'] else 1 if p['hands'].endswith('좌타') else 0)
            if p.get('number') is not None:
                number=str(p['number']);put(r,'jersey',jersey_code(number) if number.isdigit() else 0)
            r[161]&=0x1f
            if p['kind']=='player':r[155]&=0x7f
            if p['kind']=='player' and p.get('foreign'):
                r[155]|=0x80
            if p.get('borrowed'):r[90]=(r[90]&0xc0)|spec['team_id'];out[base+90]=r[90];borrowed+=1
            if code=='LG' and p['kind']=='player':
                r[155]=(r[155]&0x7f)|(0x80 if p['foreign'] else 0)
            if code=='LG' and p.get('back_name'):
                latin=p['back_name'].encode('ascii');assert len(latin)<=11
                r[92:104]=latin.ljust(12,b'\0')
                v=struct.unpack_from('<I',r,152)[0];struct.pack_into('<I',r,152,(v&~0x03800000)|(p['skin_type']<<23))
                v=struct.unpack_from('<I',r,156)[0];struct.pack_into('<I',r,156,(v&0x07ffffff)|(p['body_type']<<27))
                out[base+156:base+160]=r[156:160]
            # Keep the fixed Latin back-name field unless a verified romanization exists.
            for start,end,label in ((92,104,'KBO 영문 등 이름 기본값'),(104,106,'생년월일'),(152,156,'키·투타'),(155,156,'외국인 여부'),(160,162,'등번호')):
                if start==104 and not p.get('birth'):continue
                if start==152 and not (p.get('height') or p.get('hands')):continue
                if start==160 and p.get('number') is None:continue
                if start==155 and p['kind']!='player':continue
                off=base+start;new=bytes(r[start:end]);out[off:off+len(new)]=new
            # The upper three bits of byte 161 select the Japanese surname/given-name
            # registration variant. Full-roster and coach rows often have no KBO
            # number; their selector still must be committed even when jersey bytes
            # 160:162 are intentionally preserved.
            out[base+161]=r[161]
            assert r[84:90]==old[84:90] and (r[90]&63)==(spec['team_id'] if p.get('borrowed') else old[90]&63)
            if p['kind']=='player':total_players+=1
            else:total_staff+=1
        for i in spec.get('vacated_indices',[]):
            base=pd+i*192;old=original[base:base+192];new=(old[90]&0xc0)|31
            out[base+90]=new;vacated+=1
        team_counts[code]={'players':spec['assigned_players'],'staff':spec['assigned_staff'],'vacated_to_pool':len(spec.get('vacated_indices',[])),'borrowed':len(spec.get('borrowed_indices',[]))}
    from hanwha_roster import apply as apply_hanwha
    out,hanreport=apply_hanwha(original,bytes(out))
    from kbo_ratings_review import apply as apply_review
    out=apply_review(out)
    # 전 선수 외형 명세는 KBO 고유 ID로 대조한 사진과 같은 index에 적용한다.
    appearance_path=DIR/'appearance.json'
    if appearance_path.exists():
        for p in json.loads(appearance_path.read_text('utf8')):
            base=pd+p['index']*192;r=bytearray(out[base:base+192])
            put(r,'height',p['height'])
            v=struct.unpack_from('<I',r,152)[0]
            struct.pack_into('<I',r,152,(v&~0x03800000)|(p['skin_type']<<23))
            v=struct.unpack_from('<I',r,156)[0]
            struct.pack_into('<I',r,156,(v&0x07ffffff)|(p['body_type']<<27))
            out[base+152:base+160]=r[152:160]
    # 2026 시즌 종료 기준 전 구단 등 이름(KBO 공식 영문명 기반, tools/backnames.py).
    backs={p['index']:p['back_name'] for c,s in specs().items() for p in s['records'] if p.get('back_name')}
    backs.update({p['index']:p['back_name'] for p in json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))['records'] if p.get('back_name')})
    for i,name in backs.items():
        latin=name.encode('ascii');assert len(latin)<=11,(i,name)
        out[pd+i*192+92:pd+i*192+104]=latin.ljust(12,bytes(1))
    from kbo_team_layout import apply_playerdata
    out=apply_playerdata(out)
    # Record every changed byte span, including translated names, for independent ISO audit.
    regions=[];i=0
    while i<len(original):
        if original[i]==out[i]:i+=1;continue
        start=i;i+=1
        while i<len(original) and original[i]!=out[i]:i+=1
        regions.append(dict(file='PLAYERDATA.CHK',offset=start,size=i-start,original=original[start:i].hex(),patched=bytes(out[start:i]).hex(),reason='KBO 선수 데이터/공식 한글 이름'))
    return out,dict(assigned_players=total_players+hanreport['players'],assigned_staff=total_staff+hanreport['coaches'],teams={c:(dict(players=hanreport['players'],staff=hanreport['coaches']) if c=='HH' else team_counts[c]) for c in specs()},statistics=total_players+hanreport['players'],ratings_manifest_sha256=hashlib.sha256((DIR/'ratings_review.json').read_bytes()).hexdigest(),preserved_player_ids=True,preserved_team_ids=(borrowed+vacated)==0,vacated_to_free_pool=vacated,borrowed_from_free_pool=borrowed,hanwha_spec_sha256=hanreport['spec_sha256'],regions=regions)
