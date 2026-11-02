"""KBO 시험판의 고정 주소 MIPS 수정. 추출 원본과 각 수정 영역을 대조한다."""
import struct
from pathlib import Path
from inventory import WORK

class Asm:
 def __init__(self,base):self.base=base;self.words=[];self.labels={};self.fix=[]
 def emit(self,w):self.words.append(w)
 def i(self,op,rt,rs,imm):self.emit(op<<26|rs<<21|rt<<16|(imm&65535))
 def r(self,fun,rd,rs,rt=0,shift=0):self.emit(rs<<21|rt<<16|rd<<11|shift<<6|fun)
 def mv(self,rd,rs):self.r(0x21,rd,rs)
 def li(self,rt,n):self.i(13,rt,0,n)
 def jal(self,a):self.emit(0x0c000000|(a>>2&0x3ffffff))
 def j(self,a):self.emit(0x08000000|(a>>2&0x3ffffff))
 def label(self,s):self.labels[s]=len(self.words)
 def branch(self,op,rs,rt,s):self.fix.append((len(self.words),s));self.i(op,rt,rs,0)
 def done(self):
  for at,s in self.fix:self.words[at]|=(self.labels[s]-at-1)&65535
  return struct.pack('<%dI'%len(self.words),*self.words)

def rank_code():
 # Original stack layout is retained for the existing sort and epilogue.
 a=Asm(0x8c61790);a.i(9,29,29,-0x1a0)
 for reg,off in [(19,0x180),(16,0x174),(17,0x178),(18,0x17c),(20,0x184),(21,0x188),(22,0x18c),(23,0x190),(30,0x194),(31,0x198)]:a.i(43,reg,29,off)
 a.mv(19,4);a.mv(20,5);a.mv(21,6);a.li(17,0)
 a.label('team');a.mv(4,19);a.jal(0x89d09a4);a.mv(5,17);a.mv(16,2)
 a.jal(0x89d0700);a.mv(4,16)
 a.i(41,0,16,12);a.i(40,17,16,14);a.i(43,0,16,16);a.i(43,0,16,20);a.i(43,17,16,24)
 a.i(10,8,17,6);a.branch(4,8,0,'pac');a.mv(18,20);a.mv(8,17);a.branch(4,0,0,'base');a.emit(0)
 a.label('pac');a.mv(18,21);a.i(9,8,17,-6)
 a.label('base');a.r(0,9,0,8,7);a.r(0,8,0,8,4);a.r(0x21,18,18,9);a.r(0x21,18,18,8);a.li(22,0)
 a.label('opp');a.mv(4,16);a.jal(0x89d076c);a.mv(5,18);a.i(9,22,22,1);a.i(10,8,22,10);a.branch(5,8,0,'opp');a.i(9,18,18,12)
 a.i(9,17,17,1);a.i(10,8,17,10);a.branch(5,8,0,'team');a.emit(0)
 a.j(0x8c61a20);a.emit(0)
 code=a.done();assert len(code)<=0x180
 h=Asm(0x8c61910)
 h.i(35,8,20,0x4c);h.branch(4,8,21,'original');h.emit(0)
 h.r(0x21,9,20,23);h.li(8,0)
 h.label('fill');h.i(43,8,9,-0x5bec);h.i(9,8,8,1);h.i(10,10,8,10);h.branch(5,10,0,'fill');h.i(9,9,9,4)
 h.j(0x8ce38dc);h.emit(0)
 h.label('original');h.jal(0x88351e4);h.li(4,0x7dd);h.j(0x8ce3840);h.emit(0)
 helper=h.done();assert len(helper)<=0x60
 # Keep the original 12-row presentation allocation, but feed only 10 records.
 r=Asm(0x8c61970);r.i(9,29,29,-16);r.i(43,31,29,0);r.jal(0x8b63dc8);r.emit(0)
 r.branch(4,2,0,'done');r.emit(0);r.i(35,8,2,0);r.i(10,8,8,10);r.branch(5,8,0,'done');r.emit(0);r.mv(2,0)
 r.label('done');r.i(35,31,29,0);r.emit(0x03e00008);r.i(9,29,29,16)
 n=Asm(0x8c619b0);n.i(9,29,29,-32)
 for reg,off in [(31,0),(16,4),(17,8)]:n.i(43,reg,29,off)
 n.mv(16,4);n.i(35,17,4,0x34);n.i(35,25,17,0);n.i(43,25,29,12);n.i(35,25,16,0x70);n.i(43,25,29,16)
 n.li(25,10);n.i(43,25,17,0);n.jal(0x8b63e54);n.i(43,25,16,0x70)
 n.i(35,25,29,12);n.i(43,25,17,0);n.i(35,25,29,16);n.i(43,25,16,0x70)
 for reg,off in [(31,0),(16,4),(17,8)]:n.i(35,reg,29,off)
 n.emit(0x03e00008);n.i(9,29,29,32)
 result=(code.ljust(0x180,b'\0')+helper.ljust(0x60,b'\0')+r.done()).ljust(0x220,b'\0')+n.done()
 assert len(result)<=0x290
 return result.ljust(0x290,b'\0')

def patches():
 from league_feats import patches as feat_patches
 from league_titles import patches as title_patches
 from league_surfaces import patches as surface_patches
 from league_records import patches as record_patches
 from league_arrange import patches as arrange_patches
 from league_team_records import patches as team_record_patches
 from league_calendar import patches as calendar_patches
 from hanwha_age import patches as age_patches
 from hanwha_visual_code import patches as visual_patches
 from kbo_team_layout import patches as roster_patches
 from lg_fresh_code import patches as lg_fresh_patches
 from kbo_identity_code import patches as identity_patches
 from stadium_anim_code import patches as stadium_anim_patches
 return [
 *feat_patches(),
 *title_patches(),
 *surface_patches(),
 *record_patches(),
 *arrange_patches(),
 *team_record_patches(),
 *calendar_patches(),
 *age_patches(),
 *visual_patches(),
 *roster_patches(),
 *lg_fresh_patches(),
 *identity_patches(),
 *stadium_anim_patches(),
 ('com_sel.elf',0x8ce37f4,struct.pack('<I',0x34040005),'일반 팀 선택을 5열로 구성'),
 ('com_sel.elf',0x8ce3814,struct.pack('<I',0x3412000a),'일반 팀 선택 10개로 제한'),
 ('com_sel.elf',0x8ce3838,struct.pack('<2I',0x08000000|(0x8c61910>>2),0),'팀 선택 목록을 참가 ID 0~9로 구성'),
 ('BOOT.BIN',0x8a2dfe4,struct.pack('<2I',0x03e00008,0x00001021),'경기 일정의 DH 규칙을 항상 사용으로 반환'),
 *[('pnteam.elf',addr,struct.pack('<I',(reg<<11)|0x21),'일정 없는 날의 타순 준비도 DH 사용') for addr,reg in [(0x8dd518c,23),(0x8dd55a8,18),(0x8dd5d40,20)]],
 ('com_sel.elf',0x8c61790,rank_code(),'10개 참가팀의 모든 상대전적을 합산'),
 ('com_sel.elf',0x8c61a28,struct.pack('<I',0x3406000a),'통합 순위 비교 대상 10팀'),
 *[('com_sel.elf',p,struct.pack('<I',(0x28040000|(reg<<21)|10)),'통합 순위 정렬 범위 10팀') for p,reg in [(0x8c61a9c,17),(0x8c61b38,18),(0x8c61b4c,17)]],
 ('com_pena.elf',0x8d241b4,struct.pack('<I',0x2a85000a),'홈 순위의 마지막 두 팀 숨김'),
 ('com_pena.elf',0x8d24318,struct.pack('<I',0x2a85000a),'홈 순위의 비참가 팀 승차 표시 숨김'),
 ('com_pena.elf',0x8d24834,struct.pack('<I',0),'항상 통합 순위 표시'),
 ('com_pena.elf',0x8d97308,struct.pack('<I',0x0c000000|(0x8c61970>>2)),'통합 순위표 갱신을 참가 10개 기록으로 제한'),
 ('com_pena.elf',0x8d97764,struct.pack('<I',0x0c000000|(0x8c619b0>>2)),'수치 표시는 10행만 생성하고 원본 순위 글자 배치는 보존'),
 ('com_pena.elf',0x8d960c4,struct.pack('<2I',0x08000000|(0x8d9761c>>2),0),'기본 순위표도 통합 순위 화면 사용'),
 ('com_pena.elf',0x8d95b1c,struct.pack('<2I',0x08000000|(0x8d9720c>>2),0),'기존 순위 갱신 콜백도 통합 순위만 갱신'),
 ('com_pena.elf',0x8d977fc,struct.pack('<I',0),'통합 순위 화면 갱신 경로 유지'),
 ('com_pena.elf',0x8d972d4,struct.pack('<I',0x34130090),'통합 순위표 시즌 경기 수 144'),
 ]

def apply_code(sources,patched):
 report=[]
 for file,va,new,reason in patches():
  original=next((WORK/'iso').rglob(file)).read_bytes();ph=struct.unpack_from('<I',original,28)[0];off,base,_,size=struct.unpack_from('<4I',original,ph+4);pos=off+va-base
  assert 0<=pos and pos+len(new)<=len(original)
  assert sources[file][pos:pos+len(new)]==original[pos:pos+len(new)]
  assert patched[file][pos:pos+len(new)]==original[pos:pos+len(new)],'번역 영역과 실행 코드 겹침'
  patched[file][pos:pos+len(new)]=new
  report.append(dict(file=file,address=hex(va),offset=pos,size=len(new),original=original[pos:pos+len(new)].hex(),patched=new.hex(),reason=reason))
 return report

def apply_layout(sources,patched):
 from analyze import chunks
 file='PNSTATS.CHK';original=sources[file];patched[file]=bytearray(patched[file]);cs={n:(o,b) for n,o,b in chunks(original)};regions=[]
 # Keep original node indices, but put the unused 11th/12th rows outside the viewport.
 off,b=cs['TCP03'];data=struct.unpack_from('<I',b,20)[0]
 for i in (10,11,22,23,34,35):regions.append((off+data+i*60,struct.pack('<f',1000.0),'비참가 행의 배경 및 장식 숨김'))
 off,b=cs['TXC03'];positions=struct.unpack_from('<I',b,32)[0]
 for i in (10,11,22,23):regions.append((off+positions+i*8,struct.pack('<h',1000),'비참가 행의 이름 및 아이콘 숨김'))
 off,b=cs['TCP06'];data=struct.unpack_from('<I',b,20)[0]
 # Preserve all 84 nodes because the original numeric formatter indexes them.
 for i in range(70,84):regions.append((off+data+i*60,struct.pack('<f',1000.0),'비참가 두 행의 수치 배경 숨김'))
 report=[]
 for pos,new,reason in regions:
  old=original[pos:pos+len(new)];assert patched[file][pos:pos+len(new)]==old
  patched[file][pos:pos+len(new)]=new
  report.append(dict(file=file,offset=pos,size=len(new),original=old.hex(),patched=new.hex(),reason=reason))
 return report
