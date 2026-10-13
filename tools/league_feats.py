"""투수/야수 최고 기록과 공동 1위, 과거 기록을 두 원본 저장소에서 통합."""
import struct
from league_code import Asm
from league_records import selection,career_filter
from league_surfaces import home_record
from league_titles import lookup


def best(base):
 a=Asm(base)
 a.label('cat');a.i(35,8,4,0);a.i(35,9,5,0);a.branch(4,9,0,'next');a.emit(0);a.branch(4,8,0,'copy');a.emit(0)
 a.i(35,10,4,4);a.i(35,11,5,4);a.r(0x21,10,10,7);a.r(0x21,11,11,7);a.i(35,10,10,0);a.i(35,11,11,0);a.r(0x2a,12,10,11);a.branch(5,12,0,'copy');a.emit(0);a.branch(5,10,11,'next');a.emit(0)
 a.r(0x21,10,8,9);a.i(43,10,4,0);a.li(10,0)
 a.label('append');a.i(11,11,8,3);a.branch(4,11,0,'next');a.emit(0);a.r(0x2b,11,10,9);a.branch(4,11,0,'next');a.emit(0)
 a.r(0,11,0,10,2);a.r(0x21,11,5,11);a.i(35,12,11,4);a.r(0,11,0,8,2);a.r(0x21,11,4,11);a.i(43,12,11,4);a.i(9,10,10,1);a.branch(4,0,0,'append');a.i(9,8,8,1)
 a.label('copy')
 for o in range(0,16,4):a.i(35,10,5,o);a.i(43,10,4,o)
 a.label('next');a.i(9,4,4,16);a.i(9,5,5,16);a.i(9,6,6,-1);a.branch(5,6,0,'cat');a.i(9,7,7,4);a.emit(0x03e00008);a.emit(0)
 return a.done()


def history(base):
 a=Asm(base);a.i(9,29,29,-32)
 a.label('cat');a.i(35,8,4,0);a.i(35,9,5,0);a.r(0x21,10,8,9);a.i(43,10,4,0)
 for i in range(3):
  a.i(35,10,4,4+i*4);a.i(43,10,29,i*4);a.i(35,10,5,4+i*4);a.i(43,10,29,12+i*4)
 a.li(10,3);a.r(0x2b,11,8,10);a.r(0xa,8,10,11);a.r(0x2b,11,9,10);a.r(0xa,9,10,11);a.li(10,0);a.li(11,0);a.li(12,0)
 a.label('pick');a.r(0x2b,13,10,8);a.branch(4,13,0,'right');a.emit(0);a.r(0,13,0,10,2);a.r(0x21,13,29,13);a.i(35,14,13,0)
 a.r(0x2b,13,11,9);a.branch(4,13,0,'left');a.emit(0);a.r(0,13,0,11,2);a.r(0x21,13,29,13);a.i(35,15,13,12);a.i(36,13,14,12);a.i(36,24,15,12);a.r(0x2b,13,13,24);a.branch(4,13,0,'left');a.emit(0)
 a.label('right');a.r(0x2b,13,11,9);a.branch(4,13,0,'next');a.emit(0);a.r(0,13,0,11,2);a.r(0x21,13,29,13);a.i(35,14,13,12);a.branch(4,0,0,'store');a.i(9,11,11,1)
 a.label('left');a.i(9,10,10,1)
 a.label('store');a.r(0,13,0,12,2);a.r(0x21,13,4,13);a.i(43,14,13,4);a.i(9,12,12,1);a.i(11,13,12,3);a.branch(5,13,0,'pick');a.emit(0)
 a.label('next');a.i(9,4,4,16);a.i(9,5,5,16);a.i(9,6,6,-1);a.branch(5,6,0,'cat');a.emit(0);a.emit(0x03e00008);a.i(9,29,29,32)
 return a.done()


def triple(base):
 a=Asm(base);a.mv(8,4);a.i(43,0,4,0x7730)
 for reg,ptr,off in [(11,0x7664,0x18),(12,0x7674,0x1c),(13,0x7684,0x20)]:a.i(35,reg,4,ptr);a.i(35,reg,reg,off)
 a.li(15,0)
 a.label('block');a.i(35,9,4,0x7740);a.mv(10,4)
 a.label('row');a.branch(4,9,0,'blockend');a.emit(0)
 for reg,off in [(11,0x18),(12,0x1c),(13,0x20)]:a.i(35,14,10,off);a.branch(5,14,reg,'next');a.emit(0)
 a.i(35,14,8,0x7730);a.i(11,24,14,3);a.branch(4,24,0,'count');a.r(0,24,0,14,2);a.r(0x21,24,8,24);a.i(43,10,24,0x7734)
 a.label('count');a.i(9,14,14,1);a.i(43,14,8,0x7730)
 a.label('next');a.i(9,9,9,-1);a.branch(4,0,0,'row');a.i(9,10,10,0x44)
 a.label('blockend');a.branch(5,15,0,'done');a.mv(4,5);a.branch(4,0,0,'block');a.li(15,1)
 a.label('done');a.emit(0x03e00008);a.emit(0)
 return a.done()


def wrapper(base,field,bestva,histva,tripleva):
 a=Asm(base);a.i(9,29,29,-16);a.i(43,31,29,0);a.i(43,16,29,4);a.i(43,17,29,8);a.i(9,16,4,0x54);a.i(9,17,4,0x7798 if field else 0x3558)
 if field:a.i(15,8,0,1);a.r(0x21,8,4,8);a.i(43,0,8,-0x1118)
 else:a.i(43,0,4,0x6a68)
 off=0x7620 if field else 0x3480;a.i(9,4,16,off);a.i(9,5,17,off);a.li(6,7 if field else 2);a.jal(bestva);a.li(7,8)
 off=0x7690 if field else 0x34a0;a.i(9,4,16,off);a.i(9,5,17,off);a.jal(histva);a.li(6,10 if field else 6)
 if field:a.mv(4,16);a.jal(tripleva);a.mv(5,17)
 a.li(4,0);a.li(5,0x7744 if field else 0x3504);a.i(35,31,29,0);a.i(35,16,29,4);a.i(35,17,29,8);a.emit(0x03e00008);a.i(9,29,29,16)
 return a.done()


def count(base,field):
 a=Asm(base);a.i(35,5,21 if field else 20,-0x1820);a.i(11,8,23 if field else 22,10);a.r(0xa,5,0,8);a.emit(0x03e00008);a.emit(0);return a.done()


def patches():
 # Every cave is behind an unconditional return/jump in a replaced function.
 from inventory import WORK
 raw=next((WORK/'iso').rglob('com_pena.elf')).read_bytes();ph=struct.unpack_from('<I',raw,28)[0];off,base=struct.unpack_from('<2I',raw,ph+4)
 caves=[[0x8d960cc,0x8d96284],[0x8d95f20+len(lookup()),0x8d960c4],[0x8d95d60+len(home_record()),0x8d95f00],[0x8cfc23c+len(career_filter()),0x8cfc44c]]
 for start,end,ar,cur,own in [(0x8cfbc74,0x8cfbd80,0x64,0xa0,0xa4),(0x8d174ac,0x8d17590,0x60,0x98,0x9c),(0x8d12d08,0x8d12dec,0x48,0x80,0x84),(0x8d1a12c,0x8d1a210,0x60,0x98,0x9c)]:caves.append([start+len(selection(start,end,ar,cur,own)),end])
 out=[]
 def allocate(fn,label):
  for cave in caves:
   lo,hi=cave;b=fn(lo)
   if len(b)<=hi-lo:
    out.append(('com_pena.elf',lo,b,label));cave[0]+=len(b);return lo
  raise ValueError((label,len(fn(0)),caves))
 b=allocate(best,'최고 기록과 공동 1위 통합');h=allocate(history,'양 리그 과거 기록을 하나의 목록으로 병합');t=allocate(triple,'통합 타율·홈런·타점 1위 교집합으로 삼관왕 재계산')
 f=allocate(lambda v:wrapper(v,True,b,h,t),'야수 기록 통합 초기화');p=allocate(lambda v:wrapper(v,False,b,h,t),'투수 기록 통합 초기화')
 def word(va,w,label):out.append(('com_pena.elf',va,struct.pack('<I',w),label))
 for va,helper in [(0x8d009b4,f),(0x8d1272c,p)]:word(va,0x0c000000|(helper>>2),'통합 기록 초기화 호출');word(va+4,0x02002021,'전체 객체 전달')
 for va,field in [(0x8d001e8,True),(0x8d120fc,False)]:
  helper=allocate(lambda v:count(v,field),'10개 참가 구단의 선수만 집계');word(va,0x0c000000|(helper>>2),'비참가 구단 선수 제외')
 # Disable only league switching; keep scrolling, detail screens, and exits.
 for va in [0x8cffb70,0x8cffbc4,0x8d11b94,0x8d11be0]:
  w=struct.unpack_from('<I',raw,off+va-base)[0]
  assert w>>26 in [4,20],(hex(va),hex(w))
  word(va,w&~(31<<21),'두 번째 리그 탭 이동 제거')
 return out
