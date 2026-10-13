"""팀 기록표 메모리 확장: 6행에서 10행으로 확장하고 통합 집계한다."""
import struct
from pathlib import Path
from inventory import WORK
from league_code import Asm

def fielding_patches():
 raw=next((WORK/'iso').rglob('com_pena.elf')).read_bytes();base=0x8cf1818;offset=0x54;out=[]
 def add(va,b,why):out.append(('com_pena.elf',va,b,why))
 def word(v,w,why):add(v,struct.pack('<I',w),why)
 # Four additional records (4*0x38), then four additional pointers (4*4).
 for va in range(0x8d9b848,0x8d9cdc0,4):
  if 0x8d9bec8<=va<0x8d9c068:continue
  w=struct.unpack_from('<I',raw,offset+va-base)[0];op=w>>26;rs=w>>21&31;imm=w&65535
  if 0x1b0<=imm<=0x248 and rs!=29 and (op in [9,32,33,35,36,37,40,41,43,49,57] or va==0x8d9b9dc):
   delta=0xe0 if imm<0x1c8 else 0xf0
   word(va,(w&0xffff0000)|(imm+delta),'팀 수비 기록 메모리와 포인터 배열을 10팀 크기로 확장')
 for va in [0x8d9be04,0x8d9beb8,0x8d9c458]:
  w=struct.unpack_from('<I',raw,offset+va-base)[0];assert w&65535==6;word(va,(w&0xffff0000)|10,'팀 수비 기록의 처리 및 선택 범위 10팀')
 # Total rows grow to ten; six visible rows and the existing scrollbar are retained.
 # Descriptor retains six visible rows; the runtime total is ten.
 # Eliminate league cycling in both directions.
 for va in [0x8d9c744,0x8d9c77c]:word(va,0x00002021,'팀 수비 기록의 리그 선택은 통합 리그 하나')
 a=Asm(0x8d9bec8);a.i(9,8,17,0x290);a.li(9,0);a.li(10,0);a.li(11,0)
 a.label('loop');a.i(35,12,8,0);a.r(0x21,13,12,19);a.i(35,13,13,12)
 a.branch(4,9,0,'first');a.emit(0);a.branch(4,13,11,'same');a.emit(0);a.mv(10,9)
 a.label('first');a.label('same');a.i(43,10,12,0);a.mv(11,13);a.i(9,9,9,1);a.i(10,14,9,10);a.branch(5,14,0,'loop');a.i(9,8,8,4);a.j(0x8d9c068);a.emit(0)
 rank=a.done();assert len(rank)<=0xd8
 # Find the actual participant ID in either original league without assuming roster order.
 h=Asm(0x8d9bfa0);h.li(8,0);h.i(35,17,16,0x44)
 h.label('league');h.li(21,0);h.i(9,9,17,0x57ac)
 h.label('team');h.i(35,2,9,0);h.i(15,10,0,1);h.r(0x21,10,2,10);h.i(35,10,10,-0x13d0);h.branch(4,10,18,'found');h.emit(0)
 h.i(9,21,21,1);h.i(10,10,21,6);h.branch(5,10,0,'team');h.i(9,9,9,4)
 h.i(35,17,16,0x48);h.branch(4,8,0,'league');h.li(8,1)
 h.label('found');h.i(15,10,0,1);h.i(13,10,10,0x1f20);h.r(0x21,2,2,10);h.j(0x8d9c18c);h.emit(0)
 helper=h.done();assert 0x8d9bfa0+len(helper)<=0x8d9c068
 add(0x8d9bec8,rank.ljust(0xd8,b'\0')+helper.ljust(0xc8,b'\0'),'10팀 동률 순위와 양쪽 리그 참가팀 조회')
 word(0x8d9c17c,0x08000000|(0x8d9bfa0>>2),'팀 기록을 실제 참가 ID로 조회');word(0x8d9c180,0,'조회 분기 지연 슬롯')
 return out

def patches():return fielding_patches()

def other_team_patches(kind):
 raw=next((WORK/'iso').rglob('com_pena.elf')).read_bytes();out=[]
 if kind=='bat':
  start,end,tail,total,stride=0x8d99858,0x8d9b5fc,0x480,0x608,0xb0
  rankstart,rankend,hook,resume=0x8d99f4c,0x8d9a0ec,0x8d9a21c,0x8d9a230
  counts=[0x8d99e7c,0x8d99f3c,0x8d9ac90];desc=0x8d9b80c;cycle=[0x8d9af80,0x8d9afb8];stackleague,stackstats=0x10,0x18
 else:
  start,end,tail,total,stride=0x8d9cf30,0x8d9eb60,0x408,0x568,0x9c
  rankstart,rankend,hook,resume=0x8d9d664,0x8d9d804,0x8d9d934,0x8d9d948
  counts=[0x8d9d590,0x8d9d654,0x8d9e1fc];desc=0x8d9ed94;cycle=[0x8d9e4ec,0x8d9e524];stackleague,stackstats=0xc,0x14
 def add(v,b,why):out.append(('com_pena.elf',v,b,why))
 def word(v,w,why):add(v,struct.pack('<I',w),why)
 def original(v):return struct.unpack_from('<I',raw,0x54+v-0x8cf1818)[0]
 delta=4*stride;newptr=tail+delta
 for va in range(start,end,4):
  if rankstart<=va<rankend:continue
  w=original(va);op=w>>26;rs=w>>21&31;imm=w&65535
  if tail<=imm<=total and rs!=29 and op in [9,13,32,33,35,36,37,40,41,43,49,57]:word(va,(w&0xffff0000)|(imm+delta+(16 if imm>=tail+24 else 0)),'팀 '+kind+' 기록의 10팀 메모리 확장')
 for va in counts:
  w=original(va);assert w&65535==6;word(va,(w&0xffff0000)|10,'팀 '+kind+' 기록 처리 범위 10팀')
 assert original(desc)==6  # Preserve six visible rows and matching resource descriptors.
 for va in cycle:word(va,0x00002021,'팀 기록의 리그 선택은 통합 리그 하나')
 a=Asm(rankstart);a.i(9,8,17,newptr);a.li(9,0);a.li(10,0);a.li(11,0)
 a.label('loop');a.i(35,12,8,0);a.r(0x21,13,12,19);a.i(35,13,13,12);a.branch(4,9,0,'same');a.emit(0);a.branch(4,13,11,'same');a.emit(0);a.mv(10,9)
 a.label('same');a.i(43,10,12,0);a.mv(11,13);a.i(9,9,9,1);a.i(10,14,9,10);a.branch(5,14,0,'loop');a.i(9,8,8,4);a.j(rankend);a.emit(0)
 helperbase=rankstart+0xd8;h=Asm(helperbase);h.li(8,0);h.i(35,17,22,0x44)
 h.label('league');h.li(18,0);h.i(9,9,17,0x57ac)
 h.label('team');h.i(35,2,9,0);h.i(15,10,0,1);h.r(0x21,10,2,10);h.i(35,10,10,-0x13d0);h.branch(4,10,23,'found');h.emit(0);h.i(9,18,18,1);h.i(10,10,18,6);h.branch(5,10,0,'team');h.i(9,9,9,4);h.i(35,17,22,0x48);h.branch(4,8,0,'league');h.li(8,1)
 h.label('found');h.i(43,17,29,stackleague);h.i(9,10,17,4);h.i(43,10,29,stackstats);h.i(15,10,0,1);h.i(13,10,10,0x1f20);h.r(0x21,2,2,10);h.j(resume);h.emit(0)
 body=a.done().ljust(0xd8,b'\0')+h.done();assert len(body)<=rankend-rankstart;add(rankstart,body.ljust(rankend-rankstart,b'\0'),'10팀 순위와 실제 팀 ID 조회')
 word(hook,0x08000000|(helperbase>>2),'양쪽 리그의 실제 참가팀 조회');word(hook+4,0,'분기 지연 슬롯')
 return out

def patches():
 out=fielding_patches()+other_team_patches('bat')+other_team_patches('pit')
 raw=next((WORK/'iso').rglob('com_pena.elf')).read_bytes()
 for desc,rankop,secondop,lo,hi in [(0x8d9b80c,0x8d9b2ac,0x8d9b2b4,0x8d99858,0x8d9b848),(0x8d9cef4,0x8d9ca70,0x8d9ca78,0x8d9b848,0x8d9cf30),(0x8d9ed94,0x8d9e818,0x8d9e820,0x8d9cf30,0x8d9ee00)]:
  for off,value in [(0,10),(8,10),(12,6),(40,12)]:out.append(('com_pena.elf',desc+off,struct.pack('<I',value),'12행 리소스에서 참가 10팀 고정 표시'))
  for va,value in [(rankop,24),(secondop,12)]:
   old=struct.unpack_from('<I',raw,0x54+va-0x8cf1818)[0];out.append(('com_pena.elf',va,struct.pack('<I',(old&0xffff0000)|value),'12행 리소스의 순위 숫자 노드 번호'))
  for old,new in [(b'PE_record_A_06',b'PE_record_A_12'),(b'PE_record_B_g06',b'PE_record_B_f12')]:
   pos=raw.find(old,0x54+lo-0x8cf1818,0x54+hi-0x8cf1818);assert pos>=0
   out.append(('com_pena.elf',pos-0x54+0x8cf1818,new,'기존 12행 공용 리소스로 팀 표 표시'))
 # The 12-row panel uses small emblem mode (2), not the 6-row flag mode (0).
 helper=Asm(0x8d95d40);helper.li(25,2);helper.i(43,25,5,0);helper.j(0x8b63300);helper.emit(0)
 out.append(('com_pena.elf',0x8d95d40,helper.done(),'12행 표의 실제 팀 ID 작은 로고 모드'))
 for va in range(0x8d99858,0x8d9eb60,4):
  if struct.unpack_from('<I',raw,0x54+va-0x8cf1818)[0]==0x0c000000|(0x8b63300>>2):out.append(('com_pena.elf',va,struct.pack('<I',0x0c000000|(0x8d95d40>>2)),'10팀 표 로고 종류에 맞게 설정'))
 return out
