"""잘못된 저장 포지션을 의도적으로 넣어 원인 경로를 재현하는 MIPS 회귀 검사."""
import struct, unittest, json
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN
from unicorn.mips_const import *
from kbo_identity_code import patches
from league_code import Asm
from inventory import ROOT

BASE=0x8800000;ENTRY=0x9400000;RECORD=0x9410000;END=0x9500000

class IdentitySyncTests(unittest.TestCase):
    def setUp(self):
        self.u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
        self.u.mem_map(BASE,0x1800000)
        for _,a,b,_ in patches():self.u.mem_write(a,b)
        for addr,value in [(0x88ef474,RECORD),(0x88ef504,RECORD+192),(0x895650c,RECORD)]:
            a=Asm(addr);a.i(15,2,0,value>>16);a.emit(0x03e00008);a.i(13,2,2,value&65535)
            self.u.mem_write(addr,a.done())

    def call(self,address,a0,a1=0):
        u=self.u
        for reg,value in [(UC_MIPS_REG_SP,0x94f0000),(UC_MIPS_REG_RA,END),(UC_MIPS_REG_A0,a0),(UC_MIPS_REG_A1,a1)]:u.reg_write(reg,value)
        u.emu_start(address,END,count=1000)
        self.assertEqual(u.reg_read(UC_MIPS_REG_PC),END)
        return u.reg_read(UC_MIPS_REG_V0)

    def test_every_player_against_every_stale_position(self):
        m=json.loads((ROOT/'translation/kbo_2026/ratings_review.json').read_text('utf8'))
        for t in m['teams'].values():
            for p in t['players']:
                for stale in range(9):
                    entry=bytearray(24);struct.pack_into('<H',entry,0,p['index']);entry[4]=0x87|(stale<<3)
                    rec=bytearray(192);rec[168]=3|(p['primary_position']<<3)
                    self.u.mem_write(ENTRY,bytes(entry));self.u.mem_write(RECORD,bytes(rec))
                    self.assertEqual(self.call(0x8c91ea0,ENTRY),1)
                    out=bytes(self.u.mem_read(ENTRY,24))
                    self.assertEqual(out[4],0x87|(p['primary_position']<<3),p['name'])
                    self.assertEqual(out[5:16],entry[5:16])
                    self.assertEqual(bytes(self.u.mem_read(RECORD,192)),bytes(rec))

    def test_display_copy_preserves_role_and_other_saved_bits(self):
        for actual in range(9):
            for stale in range(9):
                self.u.mem_write(ENTRY,struct.pack('<I',0x89abcdef&~0x78|stale<<3))
                self.u.mem_write(RECORD+168,struct.pack('<I',actual<<3|3))
                self.u.reg_write(UC_MIPS_REG_A2,ENTRY)
                self.call(0x88ea7f8,0,RECORD)
                got=struct.unpack('<I',self.u.mem_read(RECORD+168,4))[0]
                self.assertEqual(got,0x89abcdef&~0x78|actual<<3)

    def test_created_player_selector_keeps_original_behavior(self):
        for selector in range(8):
            e=bytearray(24);struct.pack_into('<H',e,0,0x8000);e[4]=0x2b
            struct.pack_into('<H',e,10,0x8000|(selector<<11)|123)
            r=bytearray(192);struct.pack_into('<I',r,160,3<<13)
            self.u.mem_write(ENTRY,bytes(e));self.u.mem_write(RECORD,bytes(r))
            self.assertEqual(self.call(0x8c91ea0,ENTRY),1)
            got=bytes(self.u.mem_read(ENTRY,24))
            self.assertEqual(got[4],e[4])
            self.assertEqual((struct.unpack_from('<H',got,10)[0]>>11)&7,3 if selector==5 else selector)

    def test_system_loader_rebuilds_only_ten_participating_teams(self):
        a=Asm(0x88fcde8);a.i(43,6,5,0);a.emit(0x03e00008);a.emit(0)
        self.u.mem_write(0x88fcde8,a.done())
        for team in range(12):
            self.u.mem_write(ENTRY,b'\xff'*4)
            self.u.reg_write(UC_MIPS_REG_S0,team);self.u.reg_write(UC_MIPS_REG_S1,ENTRY)
            self.u.reg_write(UC_MIPS_REG_S7,ENTRY)
            stop=0x89040b0 if team<10 else 0x89040a0
            self.u.emu_start(0x8904078,stop,count=100)
            self.assertEqual(self.u.reg_read(UC_MIPS_REG_PC),stop)
            self.assertEqual(struct.unpack('<I',self.u.mem_read(ENTRY,4))[0],team if team<10 else 0xffffffff)

if __name__=='__main__':unittest.main(verbosity=2)
