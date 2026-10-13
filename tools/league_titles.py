"""타이틀 전체 구단 집계: 기존 두 리그용 작업 공간을 하나의 700명 표로 사용."""
import struct
from inventory import WORK
from league_code import Asm
BASE=0x8d95f20

def lookup():
 a=Asm(BASE);a.i(35,8,29,0x20);a.i(15,9,0,2);a.r(0x21,8,8,9);a.li(9,0)
 a.label('league');a.r(0,10,0,9,2);a.r(0x21,10,8,10);a.i(35,11,10,-0x4d04);a.i(9,12,11,0x57ac);a.li(16,0)
 a.label('team');a.i(35,2,12,0);a.i(15,13,0,1);a.r(0x21,13,2,13);a.i(35,13,13,-0x13d0);a.i(35,14,29,0x10);a.branch(4,13,14,'found');a.emit(0)
 a.i(9,16,16,1);a.i(10,13,16,6);a.branch(5,13,0,'team');a.i(9,12,12,4);a.branch(4,9,0,'league');a.li(9,1)
 a.label('found');a.i(9,11,11,4);a.emit(0x03e00008);a.i(43,11,29,0x14)
 result=a.done();assert len(result)<0x190;return result

def patches():
 raw=next((WORK/'iso').rglob('com_pena.elf')).read_bytes();ph=struct.unpack_from('<I',raw,28)[0];off,base,_,size=struct.unpack_from('<4I',raw,ph+4);out=[]
 def word(va,w,why):out.append(('com_pena.elf',va,struct.pack('<I',w),why))
 out.append(('com_pena.elf',BASE,lookup(),'타이틀 집계용 양 리그 실제 구단 ID 조회'))
 for va in range(0x8d1d738,0x8d1e794,4):
  w=struct.unpack_from('<I',raw,off+va-base)[0];op=w>>26;imm=w&65535
  if 0xd200<=imm<=0xd954 and op in [9,35,36,37,40,41,43,49,57]:word(va,(w&0xffff0000)|((imm+(0x9060 if imm>=0xd890 else 0x8c00))&65535),'타이틀 700명 기록·포인터·최상위 목록 공간 확장')
 word(0x8d1e1a0,0x34045e00,'700명 정렬 포인터의 하위 주소');word(0x8d1e1ac,0x00c42021,'700명 정렬 포인터의 상위 주소')
 word(0x8d1e26c,0x3407000a,'10개 구단 선수 집계')
 word(0x8d1e2f4,0x0c000000|(BASE>>2),'실제 구단 ID로 원본 선수와 성적 조회')
 word(0x8d1ebcc,0,'두 번째 리그 작업 표 생성 생략')
 for va in [0x8d1ebac,0x8d1e000,0x8d1e054]:
  w=struct.unpack_from('<I',raw,off+va-base)[0];word(va,w&~(31<<16),'타이틀 화면 리그 탭 하나로 고정')
 return out
