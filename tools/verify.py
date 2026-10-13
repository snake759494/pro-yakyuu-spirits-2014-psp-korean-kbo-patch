"""원본과 개발 ISO의 전체 파일, 문자열, PGD 설치 경로를 독립 검증한다."""
from pathlib import Path
import json,hashlib,struct,collections
from inventory import ROOT,WORK,ISO
from build import OUT
from analyze import chunks
from menu_texture import apply as patch_menu_texture
from ui_textures import apply as patch_ui_textures,definitions as texture_definitions
from compact import split_phrases
import gamecodec
import script16
import save_icons
from pgd import PGD,Kirk,MacKey,bbmac_update,bbmac_final

def main():
 inv=json.loads((WORK/'inventory.json').read_text(encoding='utf8'));applied=json.loads((ROOT/'build/applied.json').read_text(encoding='utf8'));assigned=json.loads((ROOT/'build/charmap.json').read_text(encoding='utf8'));cm={r['hangul']:bytes.fromhex(r['code']) for r in assigned if 'hangul' in r}
 token_codes={r['phrase']:bytes.fromhex(r['code']) for r in assigned if 'phrase' in r}
 splits=split_phrases(json.loads((ROOT/'translation/compact_phrases.json').read_text('utf8')))
 phrase_codes={k:b''.join(token_codes[t] if len(t)>1 else cm[t] if t in cm else t.encode('cp932') for t in ts) for k,ts in splits.items()}
 def encode(s):
  raw=phrase_codes[s] if s in phrase_codes else b''.join(cm[c] if c in cm else ('・' if c=='·' else c).encode('cp932') for c in s)
  for code,tag in gamecodec.SPECIAL.items():raw=raw.replace(tag.encode('ascii'),code)
  return raw
 changed_files=[];changed_fbd=[];changed_blocks=[];unchanged_files=0;locs={e['name']:e for e in inv['fbd']};locs.update({Path(e['name']).name:e for e in inv['iso'] if e['name'].endswith('.elf')});locs['BOOT.BIN']=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/SYSDIR/EBOOT.BIN')
 assert OUT.stat().st_size==ISO.stat().st_size
 texture_files={s['file'] for s in texture_definitions()}
 build_report=json.loads((ROOT/'build/build_report.json').read_text('utf8'))
 league_code=build_report.get('league_code',[])
 if build_report.get('hanwha_stadium'):locs['CMIYAGI.CHK']=dict(locs['CMIYAGI.CHK'],size=locs['CMIYAGI.CHK']['capacity'])
 with ISO.open('rb') as src,OUT.open('rb') as dst:
  for e in inv['iso']:
   src.seek(e['offset']);dst.seek(e['offset']);left=e['size'];same=True
   while left:
    n=min(left,4*1024*1024);same &= src.read(n)==dst.read(n);left-=n
   if same:unchanged_files+=1
   else:changed_files.append(e['name'])
  for e in inv['fbd']:
   src.seek(e['offset']);dst.seek(e['offset']);a=src.read(e['size']);b=dst.read(e['size'])
   if a!=b:changed_fbd.append(e['name'])
  # 승인된 문자열·이름·글리프 영역 이외의 바이트는 원본 그대로여야 한다.
  labels=set(r['file'] for r in applied)|set(changed_fbd)
  for label in labels:
   e=locs[label]
   if label=='BOOT.BIN':a=(WORK/'iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
   else:src.seek(e['offset']);a=src.read(e['size'])
   dst.seek(e['offset']);b=dst.read(len(a));allowed=bytearray(len(a))
   for r in applied:
    if r['file']==label:allowed[r['offset']:r['offset']+r['size']]=b'\1'*r['size']
   for r in league_code+build_report.get('league_layout',[])+build_report.get('kbo_logos',[])+build_report.get('kbo_rosters',{}).get('regions',[])+build_report.get('hanwha_roster',{}).get('regions',[])+build_report.get('hanwha_visual',[])+build_report.get('hanwha_stadium',[])+build_report.get('lg_stadium',[])+build_report.get('ss_stadium',[])+build_report.get('club_stadium',[]):
    if r['file']==label:
     o=r['offset'];n=r['size'];assert a[o:o+n]==bytes.fromhex(r['original']);assert b[o:o+n]==bytes.fromhex(r['patched']);allowed[o:o+n]=b'\1'*n
   if label in ('BBFONT.CHK','MENU2D.CHK','BBFONTG.CHK','KFONT.CHK'):
    for name,off,data in chunks(a):
     if not data.startswith(b'PS2 FONT'):continue
     n,w,h=struct.unpack_from('<3I',data,16)
     if n not in (3698,3401,3397):continue
     stride=((w+1)//2)*h
     for row in assigned:
      idx=row['index'] if n==3698 else row['split_index'];o=off+28+idx*stride;allowed[o:o+stride]=b'\1'*stride
   if label=='MAINMENU.CHK':
    expected,texture=patch_menu_texture(a);o=texture['offset'];n=texture['size'];assert b[o:o+n]==expected[o:o+n];allowed[o:o+n]=b'\1'*n
   if label in texture_files:
    expected,textures=patch_ui_textures(label,a,league_trial=bool(build_report.get('league_trial')))
    if label=='PNMAIN.CHK' and build_report.get('league_trial'):
     from league_surfaces import home_texture
     expected,_=home_texture(expected)
    for texture in textures:
     o=texture['offset'];n=texture['size'];assert b[o:o+n]==expected[o:o+n];allowed[o:o+n]=b'\1'*n
   if label in save_icons.FILES:
    assert b==save_icons.apply(label,a);allowed[:]=b'\1'*len(a)
   if label=='SCHEDULE.CHK':
    from league_trial import apply as patch_league, audit as audit_league
    expected,league=patch_league(a);assert b==expected;audit_league(b,a)
    for day in range(241):
     o=league['offset']+day*60;allowed[o:o+30]=b'\1'*30
   assert all(x==y or ok for x,y,ok in zip(a,b,allowed)),label
  for r in applied:
   e=locs[r['file']];dst.seek(e['offset']+r['offset']);actual=dst.read(r['size'])
   if r.get('encoding')=='script16':
    expected=script16.encode_text(r['ko'],encode);expected+=b'\x40\x81'*((r['size']-len(expected))//2)
   else:expected=((b'\0'.join(encode(s) for s in r['ko']) if isinstance(r['ko'],list) else r['ko'].encode('utf8') if r.get('encoding')=='utf-8' else encode(r['ko']))+b'\0').ljust(r['size'],b'\0')
   assert actual==expected,r
  install=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/INSDIR/BASEBALL.FBD');archive=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
  if build_report.get('stadium_index'):
   r=build_report['stadium_index'];src.seek(r['offset']);dst.seek(r['offset'])
   assert src.read(4)==bytes.fromhex(r['original']) and dst.read(4)==bytes.fromhex(r['patched'])
   table_size=22+268*len(inv['fbd']);src.seek(archive['offset']);dst.seek(archive['offset'])
   a=src.read(table_size);b=bytearray(dst.read(table_size));o=r['offset']-archive['offset'];b[o:o+4]=bytes.fromhex(r['original']);assert a==b
  install_synced=build_report.get('installation_data_patched',False)
  if install_synced:
   src.seek(install['offset']);oldhead=src.read(144);dst.seek(install['offset']);head=dst.read(144);pgd=PGD(head);original=PGD(oldhead)
   assert pgd.vkey==original.vkey and pgd.dkey==original.dkey
   count=pgd.data_size//pgd.block_size;tableoff=install['offset']+pgd.data_offset+pgd.data_size
   src.seek(tableoff);oldtable=src.read(count*16);dst.seek(tableoff);table=dst.read(count*16)
   def mac(data):
    k=Kirk();m=MacKey(pgd.mac_type);bbmac_update(k,m,data);return bbmac_final(k,m,pgd.vkey)
   assert mac(table)==head[0x60:0x70]
   for i in range(count):
    if oldtable[i*16:i*16+16]==table[i*16:i*16+16]:continue
    dst.seek(install['offset']+pgd.data_offset+i*pgd.block_size);raw=dst.read(pgd.block_size)
    assert mac(raw)==table[i*16:i*16+16]
    plain=pgd.decrypt_block(i,raw);dst.seek(archive['offset']+i*pgd.block_size);assert plain==dst.read(pgd.block_size)
    changed_blocks.append(i)
  else:
   dst.seek(install['offset']);src.seek(install['offset']);h=hashlib.sha256();left=install['size']
   expected=build_report.get('installation_archive_sha256')
   while left:
    n=min(left,4*1024*1024);part=dst.read(n);assert len(part)==n;h.update(part)
    if expected is None:assert part==src.read(n),'원본 설치 데이터 변경'
    left-=n
   if expected is not None:assert h.hexdigest()==expected,'보존된 설치 데이터 변경'
  # 변경 가능 파일 이외의 ISO 영역도 전부 불변이어야 한다.
  ranges=sorted((e['offset'],e['offset']+e['size']) for e in inv['iso'] if e['name'] in changed_files);cursor=0
  for lo,hi in ranges+[(ISO.stat().st_size,ISO.stat().st_size)]:
   src.seek(cursor);dst.seek(cursor);left=lo-cursor
   while left:
    n=min(left,4*1024*1024);assert src.read(n)==dst.read(n);left-=n
   cursor=max(cursor,hi)
 with OUT.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 report=dict(status='정적 검사 통과; 실행 검증은 별도 runtime_validation.json 참고',iso=OUT.name,sha256=digest,iso_size_preserved=True,iso_layout_preserved=True,nontranslation_bytes_preserved=True,unchanged_iso_files=unchanged_files,changed_iso_files=changed_files,total_fbd_entries=len(inv['fbd']),changed_fbd_entries=changed_fbd,verified_translation_locations=len(applied),verified_install_blocks=len(changed_blocks),installation_data_patched=install_synced,install_block_table_header_macs=True if install_synced else None,install_plaintext_matches_direct_archive=True if install_synced else None,installation_archive_preserved=not install_synced,runtime_gameplay_verified=False)
 if 'SCHEDULE.CHK' in changed_fbd:
  report['nontranslation_bytes_preserved']=False
  report['outside_approved_patch_regions_preserved']=True
  report['league_schedule_verified']=True
  report['intentional_nontranslation_change']='1군 일정과 명시된 실행 코드 수정; 2군 일정과 레코드 크기 보존'
  report['league_code_regions_verified']=len(league_code)
  report['league_layout_regions_verified']=len(build_report.get('league_layout',[]))
 if build_report.get('hanwha_roster'):
  report['hanwha_roster_regions_verified']=len(build_report['hanwha_roster']['regions'])
  report['hanwha_visual_regions_verified']=len(build_report.get('hanwha_visual',[]))
  report['intentional_nontranslation_change']+='; 한화 2026 개막 선수단/능력 변경'
 (ROOT/'build/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ('changed_iso_files','changed_fbd_entries')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
