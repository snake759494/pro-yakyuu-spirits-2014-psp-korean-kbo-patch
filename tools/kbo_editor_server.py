"""KBO 편집기의 로컬 저장소/API 서버. 외부 네트워크 연결 없이 127.0.0.1에서 실행."""
from __future__ import annotations
import base64, hashlib, json, mimetypes, re, shutil, sys, zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT=Path(__file__).resolve().parents[1]
EDITOR=ROOT/'editor_data'; ASSETS=EDITOR/'assets'; EXPORTS=EDITOR/'exports'
DRAFT=EDITOR/'draft.json'; BASE=EDITOR/'baseline.json'
TEAMS=['HH','LG','SS','HT','WO','KT','LT','OB','NC','SK']
TEAM_NAMES={'HH':'한화 이글스','LG':'LG 트윈스','SS':'삼성 라이온즈','HT':'KIA 타이거즈','WO':'키움 히어로즈','KT':'KT 위즈','LT':'롯데 자이언츠','OB':'두산 베어스','NC':'NC 다이노스','SK':'SSG 랜더스'}
ABBR={'HH':'한','LG':'L','SS':'삼','HT':'기','WO':'키','KT':'K','LT':'롯','OB':'두','NC':'N','SK':'S'}
TEAM_IDS={'HH':6,'LG':0,'SS':1,'HT':2,'WO':3,'KT':4,'LT':5,'OB':7,'NC':9,'SK':8}
PITCHES=['포심','투심','슬라이더','커터','커브','너클커브','포크','체인지업','스플리터','싱커','서클체인지','슈트']
POSITIONS=['P','C','1B','2B','3B','SS','LF','CF','RF','DH']
ABILITY_LIMITS={'trajectory':[0,7],'contact_r':[0,127],'contact_l':[0,127],'power':[0,127],'speed':[0,127],'arm':[0,127],'catching':[0,127],'throwing':[0,127],'recovery':[0,127],'stamina':[0,127],'starter':[0,7],'reliever':[0,7],'closer':[0,7]}
BRAND_PATH=ROOT/'translation/club_brand.json'
SOURCE_PATHS=['translation/kbo_2026/ratings_review.json','translation/kbo_2026/appearance.json','translation/club_brand.json','tools/kbo_team_layout.py']

def read(path): return json.loads(path.read_text('utf-8'))
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def initial_state():
    ratings=read(ROOT/'translation/kbo_2026/ratings_review.json'); appearances={x['index']:x for x in read(ROOT/'translation/kbo_2026/appearance.json')}
    brands=read(BRAND_PATH); players=[]; staff=[]; teams={}
    from kbo_team_layout import STARTERS,ROTATIONS,CLOSERS
    for code in TEAMS:
        specpath=ROOT/('translation/hanwha_2026.json' if code=='HH' else f'translation/kbo_2026/{code}.json')
        spec=read(specpath); spec.setdefault('name',TEAM_NAMES[code]); rt=ratings['teams'][code]
        ratings_by_index={p['index']:p for p in rt['players']}
        brand=brands.get(code,{})
        if code=='HH':
            brand.update({'team_id':6,'asset':'E','name':spec['name'],'city':'대전','uniform':'N06E','stadium_slot':12,'stadium_model':'MAZDA','stadium_name':'대전 한화생명 볼파크','stadium_short':'대전 볼파크','stadium_display_name':'대전 볼파크','stadium_english':'DAEJEON EAGLES','asset_dir':'translation/hanwha_visual','cap_color':[232,91,24],'home_color':[238,239,241],'away_color':[177,182,189],'alternate_color':[245,92,18]})
        elif code=='LG':
            brand.update({'team_id':0,'asset':'G','name':spec['name'],'city':'서울','uniform':'N00G','stadium_slot':7,'stadium_model':'CHIBA','stadium_name':'잠실야구장','stadium_short':'서울 잠실','stadium_display_name':'잠실야구장','stadium_english':'SEOUL TWINS','asset_dir':'translation/lg_brand','cap_color':[194,0,49],'home_color':[238,238,234],'away_color':[24,24,27],'alternate_color':[178,183,188]})
        else: brand['name']=spec['name']
        asset_dir=ROOT/brand.get('asset_dir','')
        known={}
        if asset_dir.is_dir():
            files=sorted(p.name for p in asset_dir.iterdir() if p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.webp') and not re.match(r'^(face|player)_\d+',p.stem))
            for slot,terms in {'logo':['emblem.png','wordmark.png','ci_initial_orange.png','logo04.png'],'cap':['cap.png','logo01.png'],'home_word':['home_word.png','ci_wordmark_home_white.png'],'away_word':['away_word.png','ci_wordmark_away_white.png'],'uniform_reference':['uniform_reference.png']}.items():
                match=next((f for f in terms if f in files),None)
                if match:known[slot]=f"{brand.get('asset_dir')}/{match}"
            known['_available']=files
        player_names={re.sub(r'\s+','',r['name']):r['name'] for r in spec['records'] if r.get('kind')=='player'}
        canonical=lambda name:player_names.get(re.sub(r'\s+','',name),name)
        teams[code]={'code':code,'name':spec['name'],'short_name':spec['name'],'abbreviation':ABBR[code], 'branding':brand,'art_assets':known,'lineup':{'starters':[{'name':canonical(n),'position':p} for n,p in STARTERS[code]],'rotation':[canonical(n) for n in ROTATIONS[code]],'closer':canonical(CLOSERS[code])},'staff':[]}
        for rec in spec['records']:
            if rec.get('kind')=='player':
                idx=rec['index'];rating=ratings_by_index[idx]
                ap=appearances.get(idx)
                if ap is None: raise ValueError(f'외형 입력 누락: {code}/{idx}')
                ident=dict(rec);ident['player_id']=rating['player_id'];ident['category']={'PC':'P','CC':'C'}.get(ident.get('category'),ident.get('category'));ident['primary_position']=rating['primary_position'];ident['opening_entry']=rating['opening_entry']
                players.append({'team_code':code,'identity':ident,'ratings':dict(rating),'appearance':dict(ap),'back_name':rec.get('back_name','')})
            else:teams[code]['staff'].append(dict(rec))
    all_sources=SOURCE_PATHS+['translation/hanwha_2026.json' if c=='HH' else f'translation/kbo_2026/{c}.json' for c in TEAMS]
    for t in teams.values():
        for path in t['art_assets'].values():
            if isinstance(path,str) and path not in all_sources:all_sources.append(path)
    hashes={p:sha(ROOT/p) for p in all_sources if (ROOT/p).is_file()}
    state={'schema':1,'created_from':hashes,'teams':teams,'players':players}
    validate_state(state,strict=False)
    return state

def validate_state(s,strict=True):
    errors=[]; seen=set(); count_by_team={t:0 for t in TEAMS}; opening={t:0 for t in TEAMS}
    if s.get('schema')!=1:errors.append('지원하지 않는 편집 데이터 버전입니다.')
    if set(s.get('teams',{}))!=set(TEAMS):errors.append('10개 KBO 구단 설정이 모두 있어야 합니다.')
    for p in s.get('players',[]):
        ident=p.get('identity',{});r=p.get('ratings',{});a=p.get('appearance',{});key=(ident.get('index'),ident.get('player_id'))
        idx=ident.get('index');code=p.get('team_code')
        if idx in seen:errors.append(f'게임 슬롯 중복: {idx}')
        seen.add(idx)
        if code not in count_by_team:errors.append(f'선수 구단 코드 오류: {code}');continue
        count_by_team[code]+=1
        if ident.get('index')!=r.get('index') or ident.get('index')!=a.get('index'):errors.append(f'슬롯 연결 불일치: {key}')
        if str(ident.get('player_id'))!=str(r.get('player_id')) or str(ident.get('player_id'))!=str(a.get('player_id')):errors.append(f'선수 ID 연결 불일치: {key}')
        if not ident.get('name'):errors.append(f'선수 이름 누락: {key}')
        category=ident.get('category')
        if category not in ('P','C','IF','OF'):errors.append(f'보직 분류 오류: {ident.get("name")} / {category}')
        primary=r.get('primary_position')
        if not isinstance(primary,int) or not 0<=primary<=8:errors.append(f'주 포지션 오류: {ident.get("name")}')
        expected={'P':{0},'C':{1},'IF':{2,3,4,5},'OF':{6,7,8}}.get(category,set())
        if primary not in expected:errors.append(f'보직과 주 포지션 불일치: {ident.get("name")} / {category} / {primary}')
        if bool(r.get('opening_entry')):opening[code]+=1
        abilities=r.get('abilities',{})
        for field,(lo,hi) in ABILITY_LIMITS.items():
            v=abilities.get(field)
            if not isinstance(v,(int,float)) or not lo<=v<=hi:errors.append(f'능력치 범위 오류: {ident.get("name")} {field}={v}')
        for pos,v in r.get('fielding',{}).items():
            if pos not in ('P','C','1B','2B','3B','SS','LF','CF','RF') or not isinstance(v,(int,float)) or not 0<=v<=127:errors.append(f'수비 능력치 오류: {ident.get("name")} {pos}={v}')
        if category=='P':
            if not 120<=r.get('velocity',0)<=180:errors.append(f'구속 범위 오류: {ident.get("name")}')
            if len(r.get('pitches',[]))<2:errors.append(f'투수 구종이 2개 미만: {ident.get("name")}')
        slots={}
        for pitch in r.get('pitches',[]):
            if pitch.get('name') not in PITCHES:errors.append(f'지원하지 않는 구종: {pitch.get("name")}');continue
            for field in ('break','stuff','control'):
                if not isinstance(pitch.get(field),int) or not 0<=pitch[field]<=7:errors.append(f'구종 등급 오류: {ident.get("name")} {pitch.get("name")} {field}')
            slots[pitch['name']]=slots.get(pitch['name'],0)+1
        if any(v>2 for v in slots.values()):errors.append(f'같은 구종 2개 초과: {ident.get("name")}')
        if not 0<=a.get('skin_type',0)<=7:errors.append(f'피부 톤 팔레트 ID 범위 오류: {ident.get("name")}')
        if not 0<=a.get('body_type',0)<=15:errors.append(f'체형 슬롯 범위 오류: {ident.get("name")}')
        if not 0<=a.get('face_id',0)<=65535:errors.append(f'얼굴 리소스 ID 오류: {ident.get("name")}')
        if not 130<=a.get('height',ident.get('height',170))<=220:errors.append(f'키 범위 오류: {ident.get("name")}')
        if not 45<=a.get('weight',ident.get('weight',75))<=180:errors.append(f'몸무게 범위 오류: {ident.get("name")}')
    if strict:
        if len(s.get('players',[]))!=619:errors.append(f'선수 전체 슬롯 수 불일치: {len(s.get("players",[]))}/619; 신인/이적/삭제는 편성 재구성이 필요합니다.')
        if len(seen)!=len(s.get('players',[])):errors.append('선수 게임 슬롯은 유일해야 합니다.')
        compact=lambda x:re.sub(r'\s+','',str(x or ''))
        for code in TEAMS:
            if count_by_team[code]<1:errors.append(f'{code} 선수 명단이 비었습니다.')
            if opening[code]!=29:errors.append(f'{code} 개막 1군은 29명이어야 합니다. 현재 {opening[code]}명')
            if len(s.get('teams',{}).get(code,{}).get('staff',[]))!=5:errors.append(f'{code} 감독·코치 슬롯은 5명이어야 합니다.')
            t=s.get('teams',{}).get(code,{})
            if t.get('branding',{}).get('team_id')!=TEAM_IDS[code]:errors.append(f'{code} 게임 구단 ID는 {TEAM_IDS[code]}로 고정합니다.')
            if t.get('branding',{}).get('uniform')!=f'N{TEAM_IDS[code]:02d}'+{'HH':'E','LG':'G','SS':'D','HT':'C','WO':'S','KT':'B','LT':'T','OB':'F','NC':'B','SK':'L'}[code]:errors.append(f'{code} 유니폼 자원 ID가 KBO 대응표와 다릅니다.')
        for code,value in ABBR.items():
            if s.get('teams',{}).get(code,{}).get('abbreviation')!=value:errors.append(f'{code} 한 글자 약칭은 {value}로 고정합니다.')
        for code,t in s.get('teams',{}).items():
            names={p['identity'].get('name') for p in s.get('players',[]) if p.get('team_code')==code}
            names_normalized={compact(n) for n in names}
            records={compact(p['identity'].get('name')):p for p in s.get('players',[]) if p.get('team_code')==code}
            lineup=t.get('lineup',{});starters=lineup.get('starters',[])
            if len(starters)!=9:errors.append(f'{code} 선발 타순은 9명이어야 합니다.')
            compact=lambda x:re.sub(r'\s+','',str(x or ''))
            if len({compact(e.get('name')) for e in starters})!=len(starters):errors.append(f'{code} 선발 타순에 같은 선수가 중복됩니다.')
            if len({e.get('position') for e in starters})!=len(starters):errors.append(f'{code} 선발 수비 위치가 중복됩니다.')
            for entry in starters:
                if compact(entry.get('name')) not in names_normalized:errors.append(f'{code} 선발 명단에 없는 선수: {entry.get("name")}')
                elif not records[compact(entry.get('name'))]['ratings'].get('opening_entry'):errors.append(f'{code} 선발 타순 선수가 1군이 아닙니다: {entry.get("name")}')
                elif records[compact(entry.get('name'))]['identity'].get('category')=='P':errors.append(f'{code} 투수가 선발 타순에 있습니다: {entry.get("name")}')
                if entry.get('position') not in ('C','1B','2B','3B','SS','LF','CF','RF','DH'):errors.append(f'{code} 선발 수비 위치 오류: {entry.get("position")}')
            for name in lineup.get('rotation',[]):
                if compact(name) not in names_normalized:errors.append(f'{code} 선발 로테이션에 없는 선수: {name}')
                elif records[compact(name)]['identity'].get('category')!='P':errors.append(f'{code} 투수가 아닌 선수가 선발 로테이션에 있습니다: {name}')
            if len({compact(n) for n in lineup.get('rotation',[])})!=len(lineup.get('rotation',[])):errors.append(f'{code} 선발 로테이션에 중복 선수가 있습니다.')
            if compact(lineup.get('closer')) not in names_normalized:errors.append(f'{code} 마무리 선수가 명단에 없습니다.')
            elif records[compact(lineup.get('closer'))]['identity'].get('category')!='P':errors.append(f'{code} 마무리 보직에 투수가 아닌 선수가 있습니다.')
    return errors

def make_export(state):
    errors=validate_state(state,strict=True)
    if errors:raise ValueError(errors[:100])
    before=read(BASE)
    oldp={(x['identity']['index'],str(x['identity']['player_id'])):x for x in before['players']}
    changed=[]
    for x in state['players']:
        key=(x['identity']['index'],str(x['identity']['player_id']))
        if key not in oldp:raise ValueError(f'기준 자료에 없는 선수 슬롯: {key}')
        if x!=oldp[key]:changed.append(x)
    brand_changes={c:t for c,t in state['teams'].items() if t!=before['teams'][c]}
    current_staff={c:t['staff'] for c,t in state['teams'].items()}
    original_staff={c:t['staff'] for c,t in before['teams'].items()}
    payload={'format':'prospi2014-kbo-editor-input','format_version':1,'created_at':datetime.now().astimezone().isoformat(),'base_sha256':state['created_from'],'summary':{'players_total':len(state['players']),'players_changed':len(changed),'teams_changed':len(brand_changes),'staff_count':sum(len(x) for x in current_staff.values())},'players':state['players'],'teams':state['teams']}
    diff={'format':payload['format'],'format_version':1,'base_sha256':state['created_from'],'player_changes':changed,'team_changes':brand_changes,'staff_before':original_staff,'staff_after':current_staff,'codex_next_steps':['codex_input.json를 canonical roster/ratings/appearance/club-brand 입력으로 반영한다.','players[].team_code와 opening_entry를 기준으로 구단 roster JSON, ratings_review.json 개막 편성을 함께 갱신한다.','외형 사진은 assets/의 경로와 SHA-256을 대조해 appearance.json source photo로 반영한다.','teams의 branding, art_assets, lineup, staff를 구단 자원 명세에 맞춘다.','정적 전수 검사 후 --league-trial 빌드와 새 페넌트 확인을 수행한다.']}
    return payload,diff

class Handler(BaseHTTPRequestHandler):
    server_version='KBOEditor/1.0'
    def log_message(self,*args):pass
    def send_json(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def body_json(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>100*1024*1024:raise ValueError('요청 크기 제한(100MB)을 넘었습니다.')
        return json.loads(self.rfile.read(n).decode('utf-8'))
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/state':
            if DRAFT.exists():state=read(DRAFT)
            else:
                state=initial_state();EDITOR.mkdir(exist_ok=True);BASE.write_text(json.dumps(state,ensure_ascii=False,indent=2),'utf-8')
            self.send_json({'state':state,'errors':validate_state(state,False),'saved':DRAFT.exists()});return
        if path=='/api/status':self.send_json({'draft_exists':DRAFT.exists(),'export':str(EXPORTS/'KBO_editor_input_latest.zip'),'root':str(ROOT)});return
        if path.startswith('/api/resource'):
            from urllib.parse import parse_qs
            rel=unquote(parse_qs(urlparse(self.path).query).get('path',[''])[0]);target=(ROOT/rel).resolve()
            allowed=[(ROOT/'translation').resolve(),(ROOT/'work/identity_audit/photos').resolve(),ASSETS.resolve()]
            if not target.is_file() or not any(base==target or base in target.parents for base in allowed):
                self.send_error(404);return
            data=target.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(target.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data);return
        if path=='/' or path=='/index.html':
            data=(ROOT/'tools/kbo_editor.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        self.send_error(404)
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            if path=='/api/save':
                state=self.body_json();errors=validate_state(state,False)
                if errors: self.send_json({'ok':False,'errors':errors[:100]},422);return
                EDITOR.mkdir(exist_ok=True);DRAFT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
                self.send_json({'ok':True,'saved_at':datetime.now().astimezone().isoformat(),'players':len(state['players'])});return
            if path=='/api/upload':
                obj=self.body_json();raw=base64.b64decode(obj.get('data',''),validate=True);name=Path(obj.get('filename','asset.png')).name
                if len(raw)>25*1024*1024:raise ValueError('이미지 하나는 25MB 이하여야 합니다.')
                ext=Path(name).suffix.lower()
                if ext not in ('.png','.jpg','.jpeg','.webp'):raise ValueError('PNG/JPG/WEBP 이미지만 업로드할 수 있습니다.')
                if not raw.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff',b'RIFF')):raise ValueError('이미지 파일 형식을 확인할 수 없습니다.')
                scope=re.sub(r'[^A-Za-z0-9_-]','_',str(obj.get('scope','asset')))[:40];key=re.sub(r'[^A-Za-z0-9_-]','_',str(obj.get('key','item')))[:60];slot=re.sub(r'[^A-Za-z0-9_-]','_',str(obj.get('slot','image')))[:40]
                folder=ASSETS/scope/key;folder.mkdir(parents=True,exist_ok=True);target=folder/(slot+ext);target.write_bytes(raw)
                self.send_json({'path':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw),'url':'/api/resource?path='+target.relative_to(ROOT).as_posix()});return
            if path=='/api/export':
                state=self.body_json();payload,diff=make_export(state);EXPORTS.mkdir(parents=True,exist_ok=True)
                stamp=datetime.now().strftime('%Y%m%d_%H%M%S');latest=EXPORTS/'KBO_editor_input_latest.zip';temp=EXPORTS/f'.KBO_editor_input_{stamp}.tmp'
                with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                    z.writestr('codex_input.json',json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
                    z.writestr('diff.json',json.dumps(diff,ensure_ascii=False,indent=2)+'\n')
                    z.writestr('README_FOR_CODEX.md','# Codex용 KBO 편집 결과\n\n`codex_input.json`은 편집기 입력 자료 전체, `diff.json`은 기준 대비 변경 선수/구단 및 적용 지침입니다. `base_sha256`가 현재 작업 파일과 일치하는지 확인하고 해당 canonical 파일로 반영한 뒤, 선수 슬롯·KBO player_id·PDN/PDW 구조를 유지하여 검증 및 빌드를 진행하세요. 업로드 이미지는 `assets/`에 있으며 편집 데이터의 `appearance.photo` 또는 `teams[코드].art_assets`가 ZIP 내부 상대 경로를 가리킵니다. 이미지 변경은 도구별 사진 합성/텍스처 빌드 단계가 필요합니다. 이 패키지 자체가 ISO 패치나 완성된 바이너리 자산은 아닙니다.\n')
                    for p in state['players']:
                        for item in (p.get('appearance',{}).get('photo'),):
                            if item and str(item).startswith('editor_data/assets/'):
                                f=(ROOT/item).resolve()
                                if f.is_file() and ASSETS.resolve() in f.parents:z.write(f,'assets/'+f.relative_to(ASSETS.resolve()).as_posix())
                    for team in state['teams'].values():
                        for item in team.get('art_assets',{}).values():
                            if isinstance(item,dict):item=item.get('path')
                            if item and str(item).startswith('editor_data/assets/'):
                                f=(ROOT/item).resolve()
                            if f.is_file() and ASSETS.resolve() in f.parents:z.write(f,'assets/'+f.relative_to(ASSETS.resolve()).as_posix())
                temp.replace(latest);self.send_json({'ok':True,'path':str(latest),'filename':latest.name,'players_changed':payload['summary']['players_changed'],'teams_changed':payload['summary']['teams_changed'],'download':'/api/download'});return
            self.send_error(404)
        except Exception as e:self.send_json({'ok':False,'error':str(e)},400)
    def do_GET_download(self):pass

class DownloadHandler(Handler):
    def do_GET(self):
        if urlparse(self.path).path=='/api/download' and (EXPORTS/'KBO_editor_input_latest.zip').exists():
            p=EXPORTS/'KBO_editor_input_latest.zip';data=p.read_bytes();self.send_response(200);self.send_header('Content-Type','application/zip');self.send_header('Content-Disposition','attachment; filename="KBO_editor_input.zip"');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        super().do_GET()

def main():
    host='127.0.0.1';port=int(sys.argv[1]) if len(sys.argv)>1 else 8765
    print(f'KBO 편집기: http://{host}:{port}/  (종료: Ctrl+C)',flush=True)
    ThreadingHTTPServer((host,port),DownloadHandler).serve_forever()
if __name__=='__main__':main()
