"""팀 편성의 화면 슬롯은 유지하되 참가 10팀만 선택하고 표시한다."""
import struct
from league_code import Asm

def patches():
 a=Asm(0x8b35164);a.i(12,8,4,7);a.i(10,9,8,5);a.branch(4,9,0,'inactive');a.emit(0);a.r(3,9,0,4,3);a.r(0,2,0,9,2);a.r(0x21,2,2,9);a.emit(0x03e00008);a.r(0x21,2,2,8);a.label('inactive');a.emit(0x03e00008);a.li(2,31)
 out=[('com_sel.elf',0x8b35164,a.done().ljust(0x88,b'\0'),'편성 슬롯을 참가 10팀에 연결')]
 for start,end,left in [(0x8b373e0,0x8b37404,True),(0x8b37410,0x8b37450,False)]:
  a=Asm(start);a.i(9,20,19,4 if left else 1);a.li(8,5);a.emit((20<<21)|(8<<16)|0x1a);a.emit((20<<11)|0x10);a.j(0x8b374cc);a.r(0,4,0,21,3)
  out.append(('com_sel.elf',start,a.done().ljust(end-start,b'\0'),'편성 좌우 이동은 5열에서 순환'))
 return out

def layout(data):
 from analyze import chunks
 out=bytearray(data);cs={n:(o,b) for n,o,b in chunks(data)};o,b=cs['TXC03'];p=struct.unpack_from('<I',b,32)[0];report=[]
 for slot in range(15):
  col=slot%8;active=col<5;x=58+col*48 if active else 1000
  for node,dx in [(6+slot,0),(21+slot,1)]:
   at=o+p+node*8;new=struct.pack('<h',x+dx);old=data[at:at+2];out[at:at+2]=new;report.append(dict(file='ARR_TOP.CHK',offset=at,size=2,original=old.hex(),patched=new.hex(),reason='편성 10개 아이콘과 인원수 배치; 비참가 슬롯 숨김'))
 # Cursor positions use the separate seven-point coordinate table.
 points=struct.unpack_from('<I',b,24)[0]
 for point,x in [(4,57),(5,105),(6,57)]:
  at=o+points+point*4;new=struct.pack('<h',x);old=data[at:at+2];out[at:at+2]=new;report.append(dict(file='ARR_TOP.CHK',offset=at,size=2,original=old.hex(),patched=new.hex(),reason='5열 아이콘 위치에 커서 기준점과 간격 정렬'))
 at=o+p+36*8;new=struct.pack('<h',1000);old=data[at:at+2];out[at:at+2]=new;report.append(dict(file='ARR_TOP.CHK',offset=at,size=2,original=old.hex(),patched=new.hex(),reason='비참가 FREE 안내 숨김'))
 return bytes(out),report
