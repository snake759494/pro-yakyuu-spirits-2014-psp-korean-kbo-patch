"""페넌트 홈의 모든 순위 표시를 동일한 10팀 집계에서 가져온다."""
import struct
from league_code import Asm
BASE=0x8d95d60

def home_record():
 a=Asm(BASE);a.i(9,29,29,-0x180)
 for r,o in [(16,0x160),(17,0x164),(31,0x168)]:a.i(43,r,29,o)
 a.mv(16,4);a.mv(17,5)
 a.i(15,8,0,0x17);a.r(0x21,8,16,8);a.i(35,8,8,-0x7ef8);a.i(9,9,8,336);a.mv(10,29);a.li(11,0)
 a.label('league');a.li(12,0)
 a.label('row');a.i(35,13,8,24);a.i(11,13,13,10);a.branch(4,13,0,'next');a.emit(0)
 for o in range(0,28,4):a.i(35,13,8,o);a.i(43,13,10,o)
 a.i(9,10,10,28)
 a.label('next');a.i(9,12,12,1);a.i(10,13,12,6);a.branch(5,13,0,'row');a.i(9,8,8,28)
 a.branch(5,11,0,'rank');a.mv(8,9);a.branch(4,0,0,'league');a.li(11,1)
 a.label('rank');a.mv(4,29);a.li(5,1);a.li(6,10);a.jal(0x8c61520);a.li(7,0)
 a.mv(4,29);a.jal(0x89d0b4c);a.mv(5,17)
 a.i(15,8,0,0x8d9);a.i(13,8,8,0x5f00)
 for o in range(0,28,4):a.i(35,9,2,o);a.i(43,9,8,o)
 a.mv(2,8)
 for r,o in [(16,0x160),(17,0x164),(31,0x168)]:a.i(35,r,29,o)
 a.emit(0x03e00008);a.i(9,29,29,0x180)
 result=a.done();assert len(result)<=0x1a0;return result

def rank_glyph(start,end):
 a=Asm(start);a.i(9,29,29,-32);a.i(43,31,29,16)
 a.i(35,4,4,0);a.i(35,4,4,4);a.branch(4,4,0,'done');a.emit(0)
 a.i(11,8,5,10);a.branch(4,8,0,'done');a.emit(0)
 a.li(8,5);a.emit((5<<21)|(8<<16)|0x1b);a.emit((9<<11)|0x12);a.emit((10<<11)|0x10)
 # column=rank%5, row=rank//5; 44 x 20 pixels with 50 x 22 pitch.
 a.r(0,11,0,10,5);a.r(0,12,0,10,4);a.r(0x21,11,11,12);a.r(0,12,0,10,1);a.r(0x21,11,11,12)
 a.r(0,12,0,9,4);a.r(0,13,0,9,2);a.r(0x21,12,12,13);a.r(0,13,0,9,1);a.r(0x21,12,12,13);a.i(9,12,12,22)
 a.i(41,11,29,0);a.i(41,12,29,2);a.i(9,11,11,44);a.i(9,12,12,20);a.i(41,11,29,4);a.i(41,12,29,6);a.i(43,0,29,8)
 a.mv(5,29);a.li(6,0);a.li(7,4);a.jal(0x8945904);a.li(8,0)
 a.label('done');a.i(35,31,29,16);a.emit(0x03e00008);a.i(9,29,29,32)
 result=a.done();assert len(result)<=end-start,(len(result),end-start);return result.ljust(end-start,b'\0')

def common_rank():
 a=Asm(0x8c79ae0);a.i(9,29,29,-0x170);a.i(43,31,29,0x160);a.i(43,16,29,0x164);a.mv(16,5)
 a.i(11,8,5,10);a.branch(4,8,0,'done');a.li(2,12)
 a.i(15,5,0,0x16);a.i(13,5,5,0x2274);a.r(0x21,5,4,5);a.i(15,6,0,0x16);a.i(13,6,6,0x7a1c);a.r(0x21,6,4,6)
 a.mv(4,29);a.jal(0x8c61790);a.mv(7,0);a.mv(4,29);a.jal(0x89d0b4c);a.mv(5,16);a.i(35,2,2,0x14)
 a.label('done');a.i(35,31,29,0x160);a.i(35,16,29,0x164);a.emit(0x03e00008);a.i(9,29,29,0x170)
 b=a.done();assert len(b)<=0x78;return b.ljust(0x78,b'\0')

def patches():
 out=[('com_sel.elf',0x8c79ae0,common_rank(),'경기 대진 카드와 공통 구단 순위를 참가 10팀 기준으로 계산')]
 def word(va,w,why):out.append(('com_pena.elf',va,struct.pack('<I',w),why))
 word(0x8d966d4,0x1000000a,'통합 순위에서 원래 6팀 승패·교류전 페이지로 넘어가지 않음')
 for va in [0x8d96650,0x8d96688]:word(va,0xae000a38,'상세 순위의 중복 리그 탭을 하나로 고정')
 for va,w in [(0x8e20c60,0x0c000000|(0x8c79ae0>>2)),(0x8e20c64,0x8e450004),(0x8e20c68,0),(0x8e20c6c,0),(0x8e20c70,0),(0x8e20c74,0x00402021)]:out.append(('pnteam.elf',va,struct.pack('<I',w),'페넌트 홈 실제 대진 카드의 두 팀 순위를 통합 계산'))
 out.append(('com_sel.elf',0x8b78948,struct.pack('<I',0x02602821),'통합 순위 정수의 후속 판정에서 이전 포인터 역참조 제거'))
 for va,w in [(0x8b788d0,0x0c000000|(0x8c79ae0>>2)),(0x8b788d4,0x02402821),(0x8b788d8,0),(0x8b788dc,0),(0x8b788e0,0),(0x8b78910,0x02602821)]:out.append(('com_sel.elf',va,struct.pack('<I',w),'대진 팀 카드에 저장하는 순위 값도 10팀 통합 순위 사용'))
 out.append(('com_pena.elf',BASE,home_record(),'홈 순위 표시용 10팀 통합 성적 조회'))
 word(0x8d25700,0x0c000000|(BASE>>2),'대진 카드 순위 통합 집계');word(0x8d25704,0x02602821,'대진 팀 ID 전달')
 for va in [0x8d25708,0x8d2570c,0x8d25710]:word(va,0,'기존 6팀 순위 조회 제거')
 word(0x8d289ec,0x0c000000|(BASE>>2),'하단 구단 순위 통합 집계');word(0x8d289f0,0x02402021,'페넌트 전체 데이터 전달')
 word(0x8d289fc,0x08000000|(0x8d28a4c>>2),'정규시즌 순위 1~10위를 그대로 표시');word(0x8d28a00,0,'6위 제한 및 원래 리그 우승 표기 우회')
 for lo,hi in [(0x8d28760,0x8d28818),(0x8d28818,0x8d288d0)]:out.append(('com_pena.elf',lo,rank_glyph(lo,hi),'하단 순위 그림의 1~10위 좌표 계산'))
 word(0x8dbffe8,0,'경기 시작 데이터도 항상 10팀 통합 성적 구성')
 for va,w in [(0x8da9664,0x3405000c),(0x8da7ff0,0x34150090),(0x8da8108,0x2a64000a),(0x8da8354,0x2a44000a)]:out.append(('dm_gmopg.elf',va,struct.pack('<I',w),'경기 시작 순위표 10팀 표시와 144경기 잔여 계산'))
 return out

def home_texture(data):
 import numpy as np
 from PIL import Image
 from analyze import chunks
 from menu_texture import decode_indices,encode_indices
 cs={n:(o,b) for n,o,b in chunks(data)};off,b=cs['TEX07'];po,pb=cs['PAL07'];indices=decode_indices(b);pal=np.frombuffer(pb[16:],np.uint8).reshape(-1,4)
 source=np.frombuffer(cs['PAL09'][1][16:],np.uint8).reshape(-1,4)[decode_indices(cs['TEX09'][1])]
 out=indices.copy();colors=pal.astype(float);colors[:,:3]*=colors[:,3:4]/255
 for rank in range(10):
  sx=rank%8*32;sy=88 if rank<8 else 109
  im=Image.fromarray(source[sy:sy+19,sx:sx+32]).resize((44,20),Image.Resampling.LANCZOS);row=np.array(im).astype(float);row[:,:,:3]*=row[:,:,3:4]/255
  for y in range(20):out[22+rank//5*22+y,rank%5*50:rank%5*50+44]=((row[y,:,None,:]-colors[None,:,:])**2).sum(2).argmin(1)
 new=encode_indices(out,b[12]);result=bytearray(data);result[off+16:off+len(b)]=new
 report=[dict(file='PNMAIN.CHK',offset=off+16,size=len(new),original=data[off+16:off+len(b)].hex(),patched=new.hex(),reason='원본 순위 숫자 그림을 사용해 1~10위 하단 표시 구성')]
 Image.fromarray(pal[out]).resize((512,128)).save('build/kbo_home_ranks.png')
 return bytes(result),report
