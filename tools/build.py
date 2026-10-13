"""현재 검수된 번역으로 고정 크기 개발 ISO를 재현한다."""
from pathlib import Path
import json,struct,hashlib,shutil,re,sys
import numpy as np
from inventory import ROOT,WORK,ISO
from analyze import chunks
from install import update_install
from menu_texture import apply as patch_menu_texture
from ui_textures import apply as patch_ui_textures,definitions as texture_definitions
from compact import split_phrases
import gamecodec
import script16
import save_icons
from font_render import render as render_glyph
OUT=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 league_trial='--league-trial' in sys.argv
 audit_prefix='preflight_' if '--check' in sys.argv else ''
 inv=json.loads((WORK/'inventory.json').read_text(encoding='utf8'));rows=json.loads((WORK/'strings.json').read_text(encoding='utf8'));players=json.loads((ROOT/'translation/players.json').read_text(encoding='utf8'));ui=json.loads((ROOT/'translation/reference_matches.json').read_text(encoding='utf8'))
 for line in (ROOT/'translation/new_ui.txt').read_text(encoding='utf-8-sig').splitlines():
  if '|' in line:j,k=line.split('|',1);ui[j]=k
 ui.update(json.loads((ROOT/'translation/new_ui.json').read_text(encoding='utf8')))
 league_ui={(r['file'],r['offset']):r['ko'] for r in json.loads((ROOT/'translation/kbo_ui.json').read_text('utf8'))} if league_trial else {}
 league_names=json.loads((ROOT/'translation/kbo_names.json').read_text('utf8'))['strings'] if league_trial else {}
 ui.update(league_names)
 if league_trial:
  for ja,ko in list(ui.items()):
   if '巨人' in ja or 'ジャイアンツ' in ja or '読売' in ja:
    ui[ja]=ko.replace('요미우리자이언츠','LG 트윈스').replace('자이언츠','LG 트윈스').replace('요미우리','LG 트윈스')
 if league_trial:
  from kbo_rosters import override_names,filter_rows
  players=override_names(players)
  rows=filter_rows(rows)
 league_locations=json.loads((ROOT/'translation/kbo_names.json').read_text('utf8')).get('locations',[]) if league_trial else []
 ui.update({r['original_hex']:r['ko'] for r in league_locations})
 if league_trial:
  # Fixed-size official stadium name fields; retain pointers and the original model IDs.
  stadium_names={'明治神宮野球場':'잠실야구장','神宮':'잠실','ＭＡＺＤＡ　スタジアム':'광주기아챔피언스필드','マツダ　スタジアム':'광주 챔필','東京ドーム':'잠실야구장','横浜スタジアム':'대구삼성라이온즈파크','横浜':'대구','ナゴヤドーム':'광주기아챔피언스필드','阪神甲子園球場':'고척스카이돔','甲子園':'고척','ほっともっとフィールド神戸':'수원KT위즈파크','ほっと神戸':'수원','ＱＶＣマリンフィールド':'사직야구장','ＱＶＣマリン':'사직','西武ドーム':'인천SSG랜더스필드','福岡 ヤフオク！ドーム':'창원NC파크','ヤフオクドーム':'창원NC파크','京セラドーム大阪':'잠실야구장','京セラドーム':'잠실','札幌ドーム':'대전한화생명볼파크','楽天Ｋｏｂｏスタジアム宮城':'대전한화생명볼파크','コボスタ宮城':'대전한화생명볼파크'}
  for x in json.loads((ROOT/'work/strings.json').read_text('utf8')):
   if x['file']=='BOOT.BIN' and x['ja'] in stadium_names and x['ja'] not in ui:
    league_locations.append(dict(file='BOOT.BIN',offset=x['offset'],original_hex=x['ja'].encode('cp932').hex()+'00',ja=x['ja'],ko=stadium_names[x['ja']]))
  by_offset={0x285570:'고척스카이돔',0x285580:'고척',0x2855b4:'광주기아챔피언스필드',0x2855e4:'광주 챔필',0x285620:'도쿄돔',0x285644:'대구삼성라이온즈파크',0x285654:'대구',0x285678:'대구삼성파크',0x28569c:'사직야구장',0x2856ac:'사직',0x2856d4:'창원NC파크',0x2856f0:'창원',0x285750:'인천SSG필드',0x2857bc:'창원NC파크',0x2857d0:'창원',0x2857fc:'잠실야구장',0x285820:'대전한화생명볼파크',0x28583c:'대전볼파크'}
  from club_brand import configs
  original_boot=(WORK/'iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
  for c in configs().values():
   at=0x2cd214+c['stadium_slot']*228
   full,short=struct.unpack_from('<2I',original_boot,at+8)
   by_offset[full-0x8804000+0x1018]=c.get('stadium_display_name',c['stadium_name'])
   if short!=full:by_offset[short-0x8804000+0x1018]=c['stadium_short']
  league_ui.update({(r['file'],r['offset']):by_offset[r['offset']] for r in rows if r['file']=='BOOT.BIN' and r['offset'] in by_offset})
 scriptui=dict(ui);scriptpath=ROOT/'translation/script_direct.json'
 if scriptpath.exists():scriptui.update(json.loads(scriptpath.read_text('utf8')))
 chars=sorted({c for s in list(ui.values())+list(scriptui.values())+[r['ko'] for r in rows if 'ko' in r]+[''.join(p['ko']) for p in players if p['ko']] for c in s if '가'<=c<='힣'})
 slots=json.loads((WORK/'font_slots.json').read_text(encoding='utf8'));assert len(chars)<=len(slots)
 assigned=[dict(s,hangul=c) for s,c in zip(slots,chars)];cm={s['hangul']:bytes.fromhex(s['code']) for s in assigned}
 phrases=json.loads((ROOT/'translation/compact_phrases.json').read_text('utf8'));phrase_codes={}
 splits=split_phrases(phrases);tokens=sorted({t for ts in splits.values() for t in ts if len(t)>1});token_codes={}
 assert len(chars)+len(tokens)<=len(slots),'한글 및 복합 글리프 슬롯 부족'
 for token in tokens:
  row=dict(slots[len(assigned)],phrase=token,cell=0,cells=1);assigned.append(row);token_codes[token]=bytes.fromhex(row['code'])
 for phrase,parts in splits.items():
  phrase_codes[phrase]=b''.join(token_codes[t] if len(t)>1 else cm[t] if t in cm else t.encode('cp932') for t in parts)
 def encode(s):
  raw=phrase_codes[s] if s in phrase_codes else b''.join(cm[c] if c in cm else ('・' if c=='·' else c).encode('cp932') for c in s)
  for code,tag in gamecodec.SPECIAL.items():raw=raw.replace(tag.encode('ascii'),code)
  return raw
 sources={};locations={}
 texture_files={s['file'] for s in texture_definitions()}
 if league_trial:
  from kbo_logos import FILES as logo_files
  texture_files.update(logo_files)
  from hanwha_visual import files as hanwha_visual_files
  texture_files.update(n for n in hanwha_visual_files() if n.endswith('.CHK'))
  from hanwha_stadium import FILES as stadium_files
  texture_files.update(stadium_files)
  from lg_stadium import FILES as lg_stadium_files
  texture_files.update(lg_stadium_files)
  from ss_stadium import FILES as ss_stadium_files
  texture_files.update(ss_stadium_files)
  from club_stadium import files as club_stadium_files
  texture_files.update(club_stadium_files())
 with ISO.open('rb') as f:
  for e in inv['fbd']:
   if any(r['file']==e['name'] for r in rows) or e['name'] in texture_files or e['name'] in save_icons.FILES or (league_trial and e['name'] in ('SCHEDULE.CHK','SELECT.CHK','ARR_TOP.CHK','TMFLAG.CHK','COMFACE.BIN')) or e['name'] in ('PLAYERDATA.CHK','BBFONT.CHK','BBFONTG.CHK','KFONT.CHK','MENU2D.CHK'):
    if league_trial and e['name']=='CMIYAGI.CHK':e=dict(e,size=e['capacity'])
    f.seek(e['offset']);sources[e['name']]=f.read(e['size']);locations[e['name']]=e
  for e in inv['iso']:
   name=Path(e['name']).name
   if name.endswith('.elf') or e['name']=='/PSP_GAME/SYSDIR/EBOOT.BIN':
    src=WORK/'iso'/e['name'].lstrip('/')
    if name=='EBOOT.BIN':src=src.with_name('BOOT.BIN');name='BOOT.BIN'
    sources[name]=src.read_bytes();locations[name]=e
 patched={k:bytearray(v) for k,v in sources.items()};changes=[];skipped=[];occupied={}
 for r in rows:
  j=r['ja']
  is_script=r.get('encoding')=='script16';mapping=scriptui if is_script else ui
  if j not in mapping and 'ko' not in r:continue
  k=league_ui.get((r['file'],r['offset']),league_names.get(j,r.get('ko',mapping.get(j))));label=r['file'];o=r['offset'];raw=script16.encode(j,gamecodec.encode) if is_script else (j.encode('utf8') if r.get('encoding')=='utf-8' else gamecodec.encode(j))+b'\0';src=sources[label]
  if league_trial and is_script and k=='KIA':k='기아'
  if src[o:o+len(raw)]!=raw:
   # CP932의 NEC/IBM 확장 영역에는 같은 글자의 복수 바이트 표현이 있다.
   try:equivalent=src[o:o+len(raw)].decode(r.get('encoding','cp932'))==j+'\0'
   except (UnicodeDecodeError,LookupError):equivalent=False
   if not equivalent:skipped.append(dict(r,reason='source_encoding'));continue
  if re.findall(r'<[^>]+>',j)!=re.findall(r'<[^>]+>',k) or re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',j)!=re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',k):skipped.append(dict(r,reason='control_mismatch'));continue
  try:dst=script16.encode_text(k,encode) if is_script else (k.encode('utf8') if r.get('encoding')=='utf-8' else encode(k))+b'\0'
  except UnicodeEncodeError:skipped.append(dict(r,reason='unsupported_character'));continue
  cap=len(raw)
  # ELF의 4바이트 정렬 패딩만 확인 후 사용한다. CHK의 고정 레코드는 확장하지 않는다.
  if label.endswith('.elf') or label=='BOOT.BIN':
   end=(o+cap+3)&~3
   if src[o+cap:end]==b'\0'*(end-o-cap) and not any(x['file']==label and o+cap<=x['offset']<end for x in rows):cap=end-o
  if len(dst)>cap:skipped.append(dict(r,ko=k,reason='capacity',needed=len(dst),capacity=cap));continue
  used=occupied.setdefault(label,set())
  if any(p in used for p in range(o,o+cap)):
   if patched[label][o:o+len(dst)]==dst:
    changes.append(dict(r,ko=k,size=len(dst),shared_suffix=True));continue
   skipped.append(dict(r,reason='overlap'));continue
  padded=dst+b'\x40\x81'*((cap-len(dst))//2) if is_script else dst.ljust(cap,b'\0')
  patched[label][o:o+cap]=padded;used.update(range(o,o+cap));changes.append(dict(r,ko=k,size=cap))
 for r in league_locations:
  o=r['offset'];old=bytes.fromhex(r['original_hex']);label=r['file'];dst=encode(r['ko'])+b'\0'
  assert sources[label][o:o+len(old)]==old and len(dst)<=len(old),r
  assert patched[label][o:o+len(old)]==old,'추가 구단 이름 영역 겹침'
  patched[label][o:o+len(old)]=dst.ljust(len(old),b'\0')
  changes.append(dict(file=label,offset=o,ja=r.get('ja',''),ko=r['ko'],size=len(old)))
 for p in players:
  if not p['ko']:continue
  raw=b'\0'.join(encode(s) for s in p['ko'])+b'\0'
  if len(raw)>42:skipped.append(dict(p,reason='player_capacity'));continue
  o=p['offset'];patched['PLAYERDATA.CHK'][o:o+42]=raw.ljust(42,b'\0');changes.append(dict(file='PLAYERDATA.CHK',offset=o,ja=p['ja'],ko=p['ko'],size=42))
 if skipped:
  (ROOT/'build'/(audit_prefix+'skipped.json')).write_text(json.dumps(skipped,ensure_ascii=False,indent=2),'utf8')
  raise RuntimeError(f'적용 제외 {len(skipped)}건: build/{audit_prefix}skipped.json 확인')
 from font_slots import linear
 aliases=json.loads((ROOT/'translation/glyph_aliases.json').read_text('utf8'))
 for jp,ko in aliases.items():
  code=jp.encode('cp932');i=linear(code)-linear(b'\x88\x9f');assert 0<=i<2965
  assigned.append(dict(original=jp,code=code.hex(),index=611+i,split_index=376+i,display_alias=ko))
 fonts=[]
 for file in ('BBFONT.CHK','MENU2D.CHK','BBFONTG.CHK','KFONT.CHK'):
  for name,off,b in chunks(sources[file]):
   if not b.startswith(b'PS2 FONT'):continue
   n,w,h=struct.unpack_from('<3I',b,16)
   if n not in (3698,3401,3397):continue
   stride=((w+1)//2)*h;assert len(b)==28+n*stride and w%2==0
   for row in assigned:
    idx=row['index'] if n==3698 else row['split_index'];assert idx<n
    im=render_glyph(row,w,h)
    a=(np.asarray(im).astype(np.uint16)+8)//17;assert a.max()>0
    raw=(a[:,::2]|(a[:,1::2]<<4)).astype(np.uint8).tobytes();o=off+28+idx*stride
    patched[file][o:o+stride]=raw
   fonts.append(dict(file=file,chunk=name,count=n,width=w,height=h,changed=len(assigned)))
 patched['MAINMENU.CHK'],texture_report=patch_menu_texture(patched['MAINMENU.CHK'],True)
 texture_reports=[]
 for file in sorted(texture_files):
  patched[file],reports=patch_ui_textures(file,patched[file],True,league_trial=league_trial);texture_reports+=reports
 for file in save_icons.FILES:patched[file]=save_icons.apply(file,sources[file],True)
 report=dict(menu_texture=texture_report,status='한글 패치 빌드; 실행 검증 범위는 runtime_validation.json 참고',translation_locations=len(changes),fonts=fonts,skipped=len(skipped),untranslated_candidates=sum('ko' not in r and r['ja'] not in (scriptui if r.get('encoding')=='script16' else ui) for r in rows),runtime_verified=False,installation_data_patched=False)
 report['ui_textures']=texture_reports
 report['save_icons']=list(save_icons.FILES)
 if league_trial:
  from kbo_rosters import apply as apply_kbo_rosters
  patched['PLAYERDATA.CHK'],report['kbo_rosters']=apply_kbo_rosters(sources['PLAYERDATA.CHK'],patched['PLAYERDATA.CHK'])
  (ROOT/'build'/(audit_prefix+'kbo_rosters.json')).write_text(json.dumps(report['kbo_rosters'],ensure_ascii=False,indent=2),'utf8')
  from league_trial import apply as patch_league
  from league_code import apply_code,apply_layout
  report['league_code']=apply_code(sources,patched)
  report['league_layout']=apply_layout(sources,patched)
  from league_arrange import layout as arrange_layout
  from kbo_logos import apply as logo_apply, FILES as logo_files
  patched['ARR_TOP.CHK'],arrange_report=arrange_layout(patched['ARR_TOP.CHK'])
  report['league_layout']+=arrange_report
  from league_calendar import layout as calendar_layout
  patched['PNAUTOADV.CHK'],calendar_report=calendar_layout(patched['PNAUTOADV.CHK'])
  report['league_layout']+=calendar_report
  from league_surfaces import home_texture
  patched['PNMAIN.CHK'],home_report=home_texture(patched['PNMAIN.CHK'])
  for r in home_report:r['original']=sources['PNMAIN.CHK'][r['offset']:r['offset']+r['size']].hex()
  report['league_layout']+=home_report
  from hanwha_stadium import apply as stadium_apply,index_patch
  report['hanwha_stadium']=stadium_apply(sources,patched,True)
  report['stadium_index']=index_patch(inv)
  from lg_stadium import apply as lg_stadium_apply
  report['lg_stadium']=lg_stadium_apply(sources,patched,True)
  from ss_stadium import apply as ss_stadium_apply
  report['ss_stadium']=ss_stadium_apply(sources,patched,True)
  from club_stadium import apply as club_stadium_apply
  report['club_stadium']=club_stadium_apply(sources,patched,True)
  report['kbo_logos']=[]
  from hanwha_visual import apply as apply_hanwha_visual
  report['hanwha_visual']=[]
  for visual_file in sorted(hanwha_visual_files()):
   patched[visual_file],visual_report=apply_hanwha_visual(visual_file,patched[visual_file],True)
   report['hanwha_visual']+=visual_report
  (ROOT/'build'/(audit_prefix+'hanwha_visual.json')).write_text(json.dumps(report['hanwha_visual'],ensure_ascii=False,indent=2),'utf8')
  for logo_file in sorted(logo_files):
   patched[logo_file],logo_report=logo_apply(logo_file,patched[logo_file],True)
   report['kbo_logos']+=logo_report
  (ROOT/'build'/(audit_prefix+'league_code.json')).write_text(json.dumps(report['league_code'],ensure_ascii=False,indent=2),'utf8')
  patched['SCHEDULE.CHK'],league_report=patch_league(sources['SCHEDULE.CHK'])
  league_report.update(version='KBO-10team-DH-alpha4',unified_standings=True,kbo_team_names=True,forced_dh=True,selection_team_count=10,single_league_postseason=False,
   kbo_rosters=True,kbo_roster_players=report['kbo_rosters']['assigned_players'],game_staff_slots=report['kbo_rosters']['assigned_staff'],
   status='10팀 정규시즌 일정·통합 순위·DH·KBO 전체 선수단; 포스트시즌은 원본 로직')
  report['league_trial']={k:v for k,v in league_report.items() if k!='games'}
  (ROOT/'build'/(audit_prefix+'league_trial.json')).write_text(json.dumps(league_report,ensure_ascii=False,indent=2),'utf8')
 for name,data in patched.items():assert len(data)==len(sources[name])
 (ROOT/'build'/(audit_prefix+'charmap.json')).write_text(json.dumps(assigned,ensure_ascii=False,indent=2),encoding='utf8')
 (ROOT/'build'/(audit_prefix+'applied.json')).write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf8')
 (ROOT/'build'/(audit_prefix+'skipped.json')).write_text(json.dumps(skipped,ensure_ascii=False,indent=2),encoding='utf8')
 if skipped:raise RuntimeError(f'적용 제외 {len(skipped)}건: build/{audit_prefix}skipped.json 확인')
 if '--check' not in sys.argv:
  shutil.copyfile(ISO,OUT)
  with OUT.open('r+b') as f, ISO.open('rb') as original:
   archive=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
   install=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/INSDIR/BASEBALL.FBD')
   replacements=[(locations[name]['offset']-archive['offset'],sources[name],data) for name,data in patched.items() if (name.endswith('.CHK') or name=='COMFACE.BIN' or name in save_icons.FILES) and data!=sources[name]]
   if league_trial:
    r=report['stadium_index'];replacements.append((r['offset']-archive['offset'],bytes.fromhex(r['original']),bytes.fromhex(r['patched'])))
   if '--with-install-data' in sys.argv:
    report['installation_validation']=update_install(original,f,install,archive,replacements)
    report['installation_data_patched']=True
   else:
    report['installation_status']='원본 설치 데이터 보존; 설치 없이 ISO 직접 읽기로 실행'
   if league_trial:
    r=report['stadium_index'];f.seek(r['offset']);f.write(bytes.fromhex(r['patched']))
   for name,data in patched.items():
    if data==sources[name] and name!='BOOT.BIN':continue
    e=locations[name];assert len(data)<=e['size'];f.seek(e['offset']);f.write(data)
    if name=='BOOT.BIN':f.write(b'\0'*(e['size']-len(data)))
  with OUT.open('rb') as f:
   for name,data in patched.items():
    if data==sources[name] and name!='BOOT.BIN':continue
    f.seek(locations[name]['offset']);assert f.read(len(data))==data,name
  report.update(iso=OUT.name,size=OUT.stat().st_size,sha256=sha(OUT),original_sha256=sha(ISO),readback=True)
 (ROOT/'build'/(audit_prefix+'build_report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
