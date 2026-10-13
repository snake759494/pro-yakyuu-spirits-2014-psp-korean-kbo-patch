"""페넌트 개인 기록: 참가 10팀의 통합 리그 필터."""
import struct
from league_code import Asm

def selection(start,end,array,current,own):
 a=Asm(start);a.li(8,0);a.i(9,9,16,array)
 a.label('fill');a.i(43,8,9,0);a.i(9,8,8,1);a.i(10,10,8,10);a.branch(5,10,0,'fill');a.i(9,9,9,4)
 a.li(8,12);a.i(43,8,9,0);a.li(8,10);a.i(43,8,16,current);a.i(43,17,16,own);a.j(end);a.emit(0)
 code=a.done();assert len(code)<=end-start;return code

def filtering(start,end,record,stride,pointers,count,filtered,qualified,excluded,pitch=False):
 a=Asm(start)
 if pitch:a.mv(7,4);a.mv(4,16)
 # a0 object, a3 selection ID. Only caller-saved registers are changed.
 a.i(15,9,0,pointers>>16);a.i(13,9,9,pointers&65535);a.r(0x21,9,4,9)
 a.i(15,15,0,count>>16);a.i(13,15,15,count&65535);a.r(0x21,15,4,15);a.i(35,6,15,0)
 a.i(9,8,4,record);a.li(2,0);a.li(10,0)
 a.label('loop');a.r(0x2a,11,10,6);a.branch(4,11,0,'done');a.emit(0)
 a.i(35,11,8,8);a.i(11,12,11,10);a.branch(4,12,0,'next');a.emit(0)
 a.i(11,12,7,12);a.branch(4,12,0,'league');a.emit(0)
 a.branch(5,11,7,'next');a.emit(0);a.branch(4,0,0,'include');a.emit(0)
 a.label('league');a.i(36,12,8,excluded);a.branch(5,12,0,'next');a.emit(0)
 a.i(36,12,4,qualified);a.branch(4,12,0,'include');a.emit(0)
 a.i(36,12,8,0x14);a.branch(4,12,0,'next');a.emit(0)
 a.label('include');a.i(43,8,9,0);a.i(9,9,9,4);a.i(9,2,2,1)
 a.label('next');a.i(9,10,10,1);a.branch(4,0,0,'loop');a.i(9,8,8,stride)
 a.label('done');a.i(43,2,15,filtered-count)
 if pitch:a.j(end);a.emit(0)
 else:a.emit(0x03e00008);a.emit(0)
 code=a.done();assert len(code)<=end-start,(hex(start),len(code),end-start)
 return code.ljust(end-start,b'\0')

def career_filter():
 a=Asm(0x8cfc23c);a.i(35,7,4,0xa0);a.r(0,7,0,7,2);a.r(0x21,7,4,7);a.i(35,7,7,0x64)
 a.i(15,15,0,3);a.r(0x21,15,4,15);a.i(35,6,15,-0x1330);a.i(9,9,15,-0x2050);a.i(9,8,4,0xb0);a.li(2,0);a.li(10,0)
 a.label('loop');a.r(0x2a,11,10,6);a.branch(4,11,0,'done');a.emit(0)
 a.i(35,11,8,8);a.i(11,12,11,10);a.branch(4,12,0,'next');a.emit(0)
 a.i(11,12,7,12);a.branch(4,12,0,'league');a.emit(0);a.branch(5,11,7,'next');a.emit(0);a.branch(4,0,0,'include');a.emit(0)
 a.label('league');a.branch(5,5,0,'pitch');a.emit(0);a.i(35,12,8,0x14);a.i(11,12,12,4000);a.branch(5,12,0,'next');a.emit(0)
 a.label('pitch');a.li(12,7);a.branch(4,5,12,'innings');a.li(12,9);a.branch(5,5,12,'include');a.emit(0)
 a.label('innings');a.i(35,12,8,0x38);a.i(15,13,0,0x45bb);a.i(13,13,13,0x8000);a.r(0x2a,12,12,13);a.branch(5,12,0,'next');a.emit(0)
 a.label('include');a.i(43,8,9,0);a.i(9,9,9,4);a.i(9,2,2,1)
 a.label('next');a.i(9,10,10,1);a.branch(4,0,0,'loop');a.i(9,8,8,0xe0)
 a.label('done');a.i(43,2,15,-0x132c);a.emit(0x03e00008);a.emit(0)
 return a.done()

def patches():
 out=[]
 def add(va,data,why):out.append(('com_pena.elf',va,data,why))
 a=bytearray(selection(0x8cfbc70,0x8cfbd80,0x64,0xa0,0xa4))
 # Own-team selector uses the constructor's stored actual team ID.
 struct.pack_into('<I',a,0,0x8e110060)
 # Restore loop counter initialization before the array setup.
 a=bytearray(struct.pack('<I',0x8e110060)+selection(0x8cfbc74,0x8cfbd80,0x64,0xa0,0xa4))
 add(0x8cfbc70,bytes(a),'통산 기록 10개 구단과 통합 리그 선택')
 add(0x8cfbd84,bytes(4),'기존 은퇴 선수 별도 선택 항목 저장 제거')
 add(0x8cfc23c,career_filter(),'통산 기록 참가 10팀 통합과 원본 규정 성적 조건 보존')
 for va,w in [(0x8cfcd80,0x3405000b),(0x8cfcdbc,0x3405000b),(0x8cfcdc0,0x2484000a)]:add(va,struct.pack('<I',w),'통산 기록 선택 순환 11항목')
 add(0x8d174ac,selection(0x8d174ac,0x8d17590,0x60,0x98,0x9c),'수비 기록 선택: 10개 구단과 통합 리그 하나')
 for va,w in [(0x8d18438,0x8d4c00b4),(0x8d18448,0x8d4c00b4),(0x8d1844c,0x2d8d000a),(0x8d18450,0x11a00005),(0x8d199d0,0x3407000b),(0x8d19a38,0x2484000a),(0x8d19a3c,0x3407000b)]:add(va,struct.pack('<I',w),'수비 기록 통합 리그 참가 10팀 필터와 선택 범위')
 add(0x8d12d08,selection(0x8d12d08,0x8d12dec,0x48,0x80,0x84),'타자 기록 선택: 10개 구단과 통합 리그 하나')
 add(0x8d1a12c,selection(0x8d1a12c,0x8d1a210,0x60,0x98,0x9c),'투수 기록 선택: 10개 구단과 통합 리그 하나')
 add(0x8d140d4,filtering(0x8d140d4,0x8d141b8,0x94,0xc4,0x283b4,0x290d4,0x290d8,0x8e,0x15),'타자 리그 기록을 참가 10팀 전체에서 필터')
 add(0x8d1b414,filtering(0x8d1b414,0x8d1b51c,0xac,0xa8,0x227ec,0x2350c,0x23510,0xa6,0x16,True),'투수 리그 기록을 참가 10팀 전체에서 필터')
 for va,word in [(0x8d15764,0x3407000b),(0x8d157cc,0x2484000a),(0x8d157d0,0x3407000b),(0x8d15820,0x3406000a),(0x8d1cb38,0x3407000b),(0x8d1cba0,0x2484000a),(0x8d1cba4,0x3407000b),(0x8d1cbf4,0x3406000a)]:add(va,struct.pack('<I',word),'개인 기록 L/R 및 리그 바로가기 범위 11항목')
 return out
