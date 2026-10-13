"""새 팀 편성 진입 때 LG와 활성 추가 구단의 옛 편성을 ISO 기준으로 재작성."""
from league_code import Asm
import struct

def patches():
 # select.elf 팀 편성 루트 생성자의 반복 lui/addu를 묶어 공간 확보.
 # 기존 초기화와 호출을 보존하고, 생성자 끝에서 대상 구단과 LG를 초기화한다.
 # 기존 페넌트 저장을 읽는 pnteam.elf 경로에는 적용하지 않는다.
 start=0x8d20000;end=0x8d20108
 a=Asm(start);a.i(15,4,0,4);a.r(0x21,4,23,4)
 for offset in range(-0x56ac,-0x5680,4):a.i(43,0,4,offset)
 a.i(40,0,4,-0x5680);a.i(40,0,4,-0x567f);a.li(5,1);a.i(40,5,4,-0x567e)
 for offset in (-0x567c,-0x5678,-0x5674,-0x5670):a.i(43,0,4,offset)
 a.jal(0x8a388e4);a.i(35,4,23,0x28)
 a.jal(0x8cd91b0);a.mv(4,0);a.i(43,2,23,0x60)
 a.i(35,4,23,0x5c);a.branch(5,4,0,'have');a.emit(0)
 a.jal(0x88fdff0);a.emit(0);a.i(43,2,23,0x5c)
 a.label('have')
 # 10개 구단을 모두 초기화한다. LG는 마지막에 동일하게 호출.
 from club_brand import configs
 mask=sum(1<<tid for tid in range(1,10)) # 한화도 포함한 나머지 9구단; LG는 마지막 호출
 if mask:
  a.i(9,29,29,-16);a.i(43,0,29,0)
  a.label('club');a.i(35,9,29,0);a.li(8,mask);a.r(6,8,9,8);a.i(12,8,8,1)
  a.branch(4,8,0,'next_club');a.emit(0)
  # 088fe168 및 088fd2e8의 원본 배열 stride. a0은 루트, a1은 대상 팀.
  a.i(35,4,23,0x5c);a.li(8,0x28e8);a.r(0x18,0,9,8);a.r(0x12,5,0);a.r(0x21,5,4,5)
  a.jal(0x88fcde8);a.mv(6,9)
  a.label('next_club');a.i(35,9,29,0);a.i(9,9,9,1);a.i(43,9,29,0);a.i(10,8,9,10)
  a.branch(5,8,0,'club');a.emit(0);a.i(9,29,29,16)
 a.i(35,4,23,0x5c);a.mv(5,4)
 a.jal(0x88fcde8);a.mv(6,0)
 a.j(end);a.emit(0)
 code=a.done();assert len(code)<=end-start
 return [('select.elf',start,code.ljust(end-start,b'\0'),'새 팀 편성 생성자: LG 및 구단별 검증 대상의 오래된 저장 편성을 ISO 기준 초기화'),
         ('select.elf',0x8d1fb18,struct.pack('<I',0xaee00068),'팀 편성 미리보기의 고정 비DH 값을 DH 사용으로 변경'),
         ('select.elf',0x8d225e4,struct.pack('<I',0xae000068),'구단 선택 뒤 원 센트럴 리그 판정이 미리보기를 비DH로 되돌리지 않도록 DH 유지')]
