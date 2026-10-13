"""원 일본 선수 ID에 하드코딩된 체형 예외를 한화 교체 슬롯에서 해제한다."""
import struct
from inventory import ROOT,WORK
def patches():
 from hanwha_visual import spec
 ids={r['face_id'] for r in spec()};d=(WORK/'iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();out=[]
 for va in range(0x8998398,0x89984a4,4):
  o=va-0x8804000+0x1018;w=struct.unpack_from('<I',d,o)[0]
  if w>>26==13 and (w>>21)&31==0 and (w&65535) in ids:
   out.append(('BOOT.BIN',va,struct.pack('<I',(w&0xffff0000)|0x6fff),'한화 선수 슬롯의 일본 선수 전용 체형 예외 해제'))
 # 등록명=이름(3)인 기존 저장 데이터도 빈 두 번째 문자열 대신 전체 이름 표시.
 # 다른 성+이름 조합 호출에는 빈 문자열을 그대로 반환해 중복을 막는다.
 from league_code import Asm
 a=Asm(0x88f1a58)
 a.i(9,2,4,110);a.mv(3,2)
 a.label('scan');a.i(36,8,2,0);a.branch(5,8,0,'scan');a.i(9,2,2,1)
 # 전체/짧은 등록명 호출 RA 0x88f1efc, 0x88f20d4만 일치한다.
 # 원본 모든 ELF의 직접 호출자를 회귀 검사하여 다른 조합 호출 제외.
 a.i(12,9,31,0xc1d7);a.i(14,9,9,0x00d4)
 a.branch(5,9,0,'done');a.i(36,8,2,0)
 a.r(10,2,3,8) # movz v0,v1,t0
 a.label('done');a.emit(0x03e00008);a.emit(0)
 assert len(a.done())==48
 out.append(('BOOT.BIN',0x88f1a58,a.done(),'기존 이름 등록 방식에서 빈 문자열이면 전체 이름 표시'))
 for va in (0x88f1f10,0x88f20e8):
  out.append(('BOOT.BIN',va,struct.pack('<I',0x0c000000|(0x88f1a50>>2)),'등록명 별명 선택도 저장된 전체 한글 이름 사용'))
 return out
