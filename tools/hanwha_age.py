"""달력은 보존하면서 새 한화 선수의 나이 계산만 2026 기준으로 맞춘다.

DH getter 08a2dfe4는 KBO 패치에서 첫 8바이트가 즉시 반환한다.
그 뒤 도달 불가능해진 dispatch 36바이트만 helper로 재사용한다.
원래 switch의 반환 타깃(08a2e010/18/20)과 다음 함수는 보존한다.
"""
import struct
def patches():
 from league_code import Asm
 h=Asm(0x8a2dfec)
 h.i(37,8,16,0x5a);h.i(12,8,8,0x3f);h.li(9,6)
 h.branch(5,8,9,'normal');h.emit(0);h.i(9,5,5,12)
 h.label('normal');h.r(0x23,4,5,4);h.j(0x88f2a24);h.emit(0)
 assert len(h.done())==36
 return [('BOOT.BIN',0x88f2a1c,struct.pack('<2I',0x08000000|(0x8a2dfec>>2),0x3084007f),'한화 선수 나이 계산을 개막 기준 2026으로 연결'),
  ('BOOT.BIN',0x8a2dfec,h.done(),'DH 즉시 반환 뒤 미사용 코드에서 팀 6의 계산 연도만 12년 보정')]
