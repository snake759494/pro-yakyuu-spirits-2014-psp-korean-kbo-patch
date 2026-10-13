"""달력 빠른 진행의 두 순위 열을 하나의 10팀 순위로 채운다."""
import struct
from league_code import Asm
BASE=0x8d95b24

def code():
 a=Asm(BASE);a.mv(24,29);a.i(9,29,29,-0x240)
 for r,o in [(16,0x200),(17,0x204),(18,0x208),(19,0x20c),(20,0x210),(21,0x214),(22,0x218),(23,0x21c),(31,0x220)]:a.i(43,r,29,o)
 a.mv(16,4);a.i(35,17,24,0x3c);a.i(35,18,24,0x44);a.i(9,19,29,0x20);a.li(20,0);a.li(21,0)
 a.label('source');a.li(22,0)
 a.label('team');a.i(35,8,17,24);a.i(11,9,8,10);a.branch(4,9,0,'next');a.emit(0)
 for off in range(0,28,4):a.i(35,8,17,off);a.i(43,8,19,off)
 a.i(43,0,19,16);a.i(9,19,19,28);a.i(9,20,20,1)
 a.label('next');a.i(9,22,22,1);a.i(10,8,22,6);a.branch(5,8,0,'team');a.i(9,17,17,28)
 a.branch(5,21,0,'rank');a.mv(17,18);a.branch(4,0,0,'source');a.li(21,1)
 a.label('rank');a.i(9,4,29,0x20);a.li(5,1);a.li(6,10);a.jal(0x8c61520);a.li(7,0)
 # Pick the least (rank, team ID) remaining record for each display position.
 a.li(17,0);a.li(18,0);a.li(19,0)
 a.label('row');a.li(8,0);a.i(9,9,29,0x20);a.li(10,0xffff);a.li(11,0xffff);a.li(20,0)
 a.label('scan');a.i(35,12,9,20);a.i(35,13,9,24);a.i(35,14,9,16);a.branch(5,14,0,'skip');a.emit(0)
 a.r(0x2a,14,12,10);a.branch(5,14,0,'choose');a.emit(0);a.branch(5,12,10,'skip');a.emit(0);a.r(0x2a,14,13,11);a.branch(4,14,0,'skip');a.emit(0)
 a.label('choose');a.mv(10,12);a.mv(11,13);a.mv(20,9)
 a.label('skip');a.i(9,8,8,1);a.i(10,14,8,10);a.branch(5,14,0,'scan');a.i(9,9,9,28)
 # Record +16 is scratch in the temporary copy; clear it before the first scan below.
 a.li(8,1);a.i(43,8,20,16);a.i(10,8,17,5);a.branch(4,8,0,'right');a.i(9,21,16,0xa4);a.mv(8,17);a.branch(4,0,0,'dest');a.emit(0)
 a.label('right');a.i(9,21,16,0x104);a.i(9,8,17,-5)
 a.label('dest');a.r(0,8,0,8,4);a.r(0x21,21,21,8);a.i(43,10,21,0);a.i(43,11,21,4);a.i(36,8,20,8);a.i(36,9,20,9)
 a.branch(5,17,0,'gap');a.emit(0);a.mv(18,8);a.mv(19,9)
 a.label('gap');a.r(0x23,8,18,8);a.r(0x23,9,9,19);a.r(0x21,8,8,9);a.emit(0x44886000);a.emit(0x46806320);a.i(15,8,0,0x3f00);a.emit(0x44886800);a.emit(0x460d6302);a.i(57,12,21,8);a.li(8,255);a.i(40,8,21,12)
 a.branch(5,17,0,'advance');a.emit(0);a.i(15,8,0,0x437f);a.i(43,8,21,8)
 a.label('advance');a.i(9,17,17,1);a.i(10,8,17,10);a.branch(5,8,0,'row');a.emit(0)
 a.mv(4,16);a.li(5,1)
 for r,o in [(16,0x200),(17,0x204),(18,0x208),(19,0x20c),(20,0x210),(21,0x214),(22,0x218),(23,0x21c),(31,0x220)]:a.i(35,r,29,o)
 a.emit(0x03e00008);a.i(9,29,29,0x240)
 result=a.done();assert len(result)<=0x598;return result

def patches():
 return [('com_pena.elf',BASE,code(),'빠른 진행 양쪽 열에 하나의 10팀 순위를 5팀씩 표시'),('com_pena.elf',0x8d0b31c,struct.pack('<2I',0x0c000000|(BASE>>2),0x8fa40034),'빠른 진행 순위 갱신 뒤 통합 순위 재계산'),('com_pena.elf',0x8d0a474,struct.pack('<I',0x2ac50005),'빠른 진행 각 열의 마지막 비참가 행 숨김')]


def layout(data):
 from analyze import chunks
 cs={n:(o,b) for n,o,b in chunks(data)};o,b=cs['TXC02'];p=struct.unpack_from('<I',b,32)[0];out=bytearray(data);report=[]
 for node in [14,20,28,34]:
  at=o+p+node*8;new=struct.pack('<h',1000);old=data[at:at+2];out[at:at+2]=new;report.append(dict(file='PNAUTOADV.CHK',offset=at,size=2,original=old.hex(),patched=new.hex(),reason='통합 순위 5+5 배치에서 남는 행 숨김'))
 return bytes(out),report
