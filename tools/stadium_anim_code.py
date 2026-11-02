"""모델을 교체한 구장 슬롯의 전용 광고·전광판 애니메이션 노드 조회를 끈다.

한화(미야기 12), NC(오사카 10, 삿포로 주간 11) 슬롯은 마쓰다 모델 복제본을 쓴다.
원본 코드는 구장 번호로 미야기/오사카/삿포로 전용 노드(adv_ledb_*, adv_led3_* 등)를
이름으로 찾고 결과를 검사하지 않아, 노드가 없으면 NULL+4를 읽는다. PPSSPP는
잘못된 메모리 접근 무시 설정에서 통과하지만 실기는 경기 로딩 중 종료된다.
마쓰다(전용 처리 없음)와 같은 경로로 보낸다. 다른 구장 번호의 동작은 보존한다.
"""
import struct
from inventory import WORK

NONE_INIT=0x898f274   # 초기화 switch의 공통 종료
NONE_FRAME=0x898f7ec  # 프레임 갱신 switch의 공통 종료
NONE_TICK=0x898f420   # 프레임 카운터 갱신 경로(a0=+0x9bc)

def patches():
 boot=(WORK/'iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();off=lambda a:a-0x8804000+0x1018
 word=lambda a:struct.unpack_from('<I',boot,off(a))[0]
 out=[]
 init=0x8aa8cb8   # 구장 2..12
 for sid in (10,11,12):
  a=init+(sid-2)*4;assert word(a)!=NONE_INIT
  out.append(('BOOT.BIN',a,struct.pack('<I',NONE_INIT),f'구장 {sid} 교체 모델: 전용 광고 노드 초기화 생략'))
 frame=0x8aa8ce8  # 구장 3..12
 for sid in (11,12):
  a=frame+(sid-3)*4;assert word(a)!=NONE_FRAME
  out.append(('BOOT.BIN',a,struct.pack('<I',NONE_FRAME),f'구장 {sid} 교체 모델: 전용 광고 프레임 갱신 생략'))
 assert word(frame+7*4)==NONE_FRAME  # 10번은 원래 처리 없음
 # 0x898f288: 10번은 0x898f2dc, 12번은 0x898f37c 전용 갱신. 나머지와 같이 카운터만 증가.
 assert word(0x898f2c0)==0x10000006 and word(0x898f2cc)==0x1085002b
 b=0x10000000|((NONE_TICK-0x898f2c4)>>2)
 out.append(('BOOT.BIN',0x898f2c0,struct.pack('<2I',b,0x8e0409bc),'구장 10 교체 모델: 전용 전광판 갱신 생략'))
 out.append(('BOOT.BIN',0x898f2cc,struct.pack('<I',0),'구장 12 교체 모델: 전용 전광판 갱신 생략'))
 return out
