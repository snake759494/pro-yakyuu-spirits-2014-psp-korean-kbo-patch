"""선수 본체와 저장 편성의 주 포지션 불일치를 읽기 경로에서 보정한다."""
from league_code import Asm
import struct


def patches():
    # 24-byte team entry resolver. Built-in records retain authoritative PDN
    # primary position; created players retain the original selector behavior.
    start=0x8c91ea0
    a=Asm(start)
    a.i(9,29,29,-16);a.i(43,16,29,0);a.i(43,31,29,4);a.mv(16,4)
    a.i(37,4,16,0);a.li(5,0x8000);a.r(0x2a,5,4,5)
    a.branch(4,5,0,'created');a.emit(0)
    a.jal(0x88ef474);a.emit(0);a.i(43,2,16,16)
    a.jal(0x88ef504);a.i(37,4,16,0);a.i(43,2,16,20)
    a.i(35,4,16,16);a.branch(4,4,0,'fail');a.emit(0)
    a.i(36,8,4,168);a.i(36,9,16,4)
    a.r(0x26,8,8,9);a.i(12,8,8,0x78);a.r(0x26,9,9,8)
    a.i(40,9,16,4);a.branch(4,0,0,'ok');a.emit(0)
    a.label('created');a.jal(0x895650c);a.emit(0)
    a.i(43,2,16,16);a.branch(4,2,0,'fail');a.i(9,5,2,192)
    a.i(43,5,16,20);a.i(37,4,16,10);a.i(12,5,4,0x3800);a.li(6,0x2800)
    a.branch(5,5,6,'ok');a.emit(0)
    a.i(35,5,2,160);a.r(2,5,0,5,13);a.i(12,5,5,7);a.r(0,5,0,5,11)
    a.i(12,4,4,0xc7ff);a.r(0x25,4,4,5);a.i(41,4,16,10)
    a.label('ok');a.branch(4,0,0,'return');a.li(2,1)
    a.label('fail');a.i(43,0,16,20);a.mv(2,0)
    a.label('return');a.i(35,16,29,0);a.i(35,31,29,4);a.emit(0x03e00008);a.i(9,29,29,16)
    assert len(a.done())<=0xf0
    # Display/match record copy used to overwrite the verified role with stale
    # 4-byte save metadata. Preserve only the authoritative role bits; copy all
    # other metadata as before. Register/jersey behavior before this stays intact.
    b=Asm(0x88ea7f8)
    b.i(35,8,6,0);b.i(35,9,5,168);b.r(0x26,9,8,9);b.i(12,9,9,0x78)
    b.r(0x26,8,8,9);b.i(43,8,5,168);b.emit(0x03e00008);b.i(9,29,29,16)
    # SYSTEM.DAT의 기본 팀 로스터 복원 루프(0..11). 이 경로가 옛 일본
    # 인원/슬롯/포지션을 되살렸다. 참가 0..9는 ISO 편성으로 재생성하고
    # 비참가 10..11 및 별도 사용자 팀 12..13의 원본 복원 경로는 보존한다.
    c=Asm(0x8904078)
    c.i(11,4,16,10);c.branch(4,4,0,'old');c.mv(5,17)
    c.mv(4,23);c.jal(0x88fcde8);c.mv(6,16)
    c.j(0x89040b0);c.emit(0);c.emit(0);c.emit(0)
    c.label('old');assert c.base+len(c.done())==0x89040a0
    from kbo_team_layout import layouts
    portraits=[('BOOT.BIN',0x8a96878+t['team_id']*8,struct.pack('<HHI',t['start'],len(t['active']),(5<<12)|(len(t['players'])-len(t['active']))),code+' COMFACE 별도 구단 시작 위치·인원 표 동기화') for code,t in layouts().items()]
    return [('com_sel.elf',start,a.done().ljust(0xf0,b'\0'),'기존 편성 포인터 재연결 시 선수 본체의 주 포지션 동기화'),
            ('BOOT.BIN',0x88ea7f8,b.done(),'선수 표시·경기 복사 시 오래된 편성 포지션 덮어쓰기 방지'),
            ('BOOT.BIN',0x8904078,c.done(),'SYSTEM 기본 10구단 편성을 ISO의 KBO 명단으로 재생성'),*portraits]
