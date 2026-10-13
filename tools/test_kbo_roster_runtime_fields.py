"""최종 ISO 레코드를 원 게임 MIPS 포지션/등록명 함수에 넣어 전수 검사한다."""
import json
import struct
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN
from unicorn.mips_const import *

from analyze import chunks
from inventory import ROOT, WORK

TEAM_CODES = ('LG','SS','HT','WO','KT','LT','HH','OB','SK','NC')
TEAM_IDS = {'LG':0,'SS':1,'HT':2,'WO':3,'KT':4,'LT':5,'HH':6,'OB':7,'SK':8,'NC':9}
POSITION_GETTER = 0x088ec5b0
NAME_GETTER = 0x088f1e04
RETURN = 0x09e00000
RECORD = 0x09f00000
BUFFER = 0x09f01000
PATCH_ISO = ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'


class FinalIsoRosterTests(unittest.TestCase):
    def test_portrait_loader_uses_updated_team_offsets(self):
        from kbo_team_layout import layouts
        from league_code import Asm
        target=0x08a62030
        old=bytes(self.u.mem_read(target,32))
        try:
            for code,t in layouts().items():
                for j,p in enumerate(t['rows']):
                    a=Asm(target)
                    a.li(8,t['team_id']);a.i(43,8,4,0)
                    a.li(8,j);a.i(43,8,5,0)
                    a.emit(0x03e00008);a.li(2,1)
                    self.u.mem_write(target,a.done())
                    self.u.ctl_remove_cache(target,target+32)
                    for reg,val in [(UC_MIPS_REG_A0,p['index']),(UC_MIPS_REG_A1,0),(UC_MIPS_REG_A2,t['team_id']),(UC_MIPS_REG_A3,0),(UC_MIPS_REG_SP,0x09f10000),(UC_MIPS_REG_RA,RETURN)]:
                        self.u.reg_write(reg,val)
                    self.u.emu_start(0x08a622c8,RETURN,count=1000)
                    self.assertEqual(self.u.reg_read(UC_MIPS_REG_PC),RETURN)
                    self.assertEqual(self.u.reg_read(UC_MIPS_REG_V0),t['start']+j,(code,p['name']))
        finally:
            self.u.mem_write(target,old)
            self.u.ctl_remove_cache(target,target+32)

    def test_final_normalizer_preserves_all_290_opening_entries(self):
        from kbo_team_layout import layouts
        inv=json.loads((WORK/'inventory.json').read_text('utf8'))
        e=next(e for e in inv['iso'] if e['name'].endswith('/com_sel.elf'))
        with PATCH_ISO.open('rb') as f:f.seek(e['offset']);elf=f.read(e['size'])
        ph=struct.unpack_from('<I',elf,28)[0];es,n=struct.unpack_from('<HH',elf,42)
        for j in range(n):
            typ,o,a,_,sz,_,_,_=struct.unpack_from('<8I',elf,ph+j*es)
            if typ==1:self.u.mem_write(a,elf[o:o+sz])
        for code,t in layouts().items():
            root=0x09400000;rows=bytearray(0x28e8)
            struct.pack_into('<II',rows,0,t['team_id'],len(t['players']))
            active={p['index'] for p in t['active']}
            for j,p in enumerate(t['players']):
                at=8+j*24;ptr=0x09600000+j*192
                struct.pack_into('<H',rows,at+10,0x4000 if p['index'] in active else 0x8000)
                struct.pack_into('<I',rows,at+16,ptr)
                self.u.mem_write(ptr,self.pdn[p['index']*192:(p['index']+1)*192])
            self.u.mem_write(root,bytes(rows));self.u.reg_write(UC_MIPS_REG_A0,root)
            self.u.reg_write(UC_MIPS_REG_SP,0x09f10000);self.u.reg_write(UC_MIPS_REG_RA,RETURN)
            self.u.emu_start(0x8ccc034,RETURN,count=50000)
            self.assertEqual(self.u.reg_read(UC_MIPS_REG_PC),RETURN)
            out=bytes(self.u.mem_read(root,len(rows)))
            got={p['index'] for j,p in enumerate(t['players']) if struct.unpack_from('<H',out,18+j*24)[0]>>14==1}
            self.assertEqual(got,active,code)

            # 시즌 진입 때는 레코드를 포인터가 아닌 0x350바이트 객체에 복사한다.
            obj=0x09400000;data=bytearray(0x10000)
            struct.pack_into('<I',data,0xe7e0,len(t['players']))
            for j,p in enumerate(t['players']):
                at=j*0x350
                data[at+0x18:at+0x18+192]=self.pdn[p['index']*192:(p['index']+1)*192]
                struct.pack_into('<I',data,at+0x30c,1 if p['index'] in active else 2)
            self.u.mem_write(obj,bytes(data))
            for reg,value in [(UC_MIPS_REG_S5,obj),(UC_MIPS_REG_S2,obj+0x10000),(UC_MIPS_REG_S0,0),(UC_MIPS_REG_S1,0),(UC_MIPS_REG_A0,len(t['players']))]:self.u.reg_write(reg,value)
            self.u.emu_start(0x8ccdb84,0x8ccdc50,count=30000)
            self.assertEqual(self.u.reg_read(UC_MIPS_REG_PC),0x8ccdc50)
            self.assertEqual(self.u.reg_read(UC_MIPS_REG_S0)+self.u.reg_read(UC_MIPS_REG_S1),29,code)
            self.assertEqual(bytes(self.u.mem_read(obj,len(data))),bytes(data),code)

    def test_final_constructor_registration_cap_is_29(self):
        for count in (0,27,28,29,30,70):
            self.u.reg_write(UC_MIPS_REG_S3,count)
            self.u.emu_start(0x88fce54,0x88fce60,count=3)
            self.assertEqual(self.u.reg_read(UC_MIPS_REG_S3),min(count,29),count)

    def test_all_final_iso_abilities_and_pitch_grades(self):
        from kbo_ratings_review import manifest
        from player_fields import get,POSITIONS,PITCHES
        getters={'power':0x88ec6f4,'contact_r':0x88ec7fc,'speed':0x88ec9ac,'arm':0x88ecaa8,'catching':0x88ecc9c,'throwing':0x88ecba0,'recovery':0x88ecd98}
        for code,t in manifest()['teams'].items():
            for p in t['players']:
                r=self.pdn[p['index']*192:(p['index']+1)*192]
                for key,value in p['abilities'].items():self.assertEqual(get(r,key),value,(code,p['name'],key))
                for key,address in getters.items():self.assertEqual(self.call(address,r,0),p['abilities'][key],(code,p['name'],key))
                self.assertEqual(self.call(0x88ec7fc,r,0,1),p['abilities']['contact_l'])
                for j,key in enumerate(POSITIONS):self.assertEqual(self.call(POSITION_GETTER,r,j),p['fielding'].get(key,0))
                self.assertEqual(self.call(0x88ecfc0,r,0),p['velocity'])
                expected={PITCHES[q['name']][0]:q for q in p['pitches']};seen=set()
                for slot in range(12):
                    kind=self.call(0x88ed5f8,r,slot)
                    if kind==37:continue
                    self.assertIn(kind,expected,(code,p['name'],kind));q=expected[kind];seen.add(kind)
                    for key,address in [('break',0x88ed108),('stuff',0x88ed3e8),('control',0x88ed3a0)]:self.assertEqual(self.call(address,r,slot),q[key],(code,p['name'],q['name'],key))
                self.assertEqual(seen,set(expected))

    @classmethod
    def setUpClass(cls):
        inv=json.loads((WORK/'inventory.json').read_text('utf8'))
        fbd={e['name']:e for e in inv['fbd']}
        entry=fbd['PLAYERDATA.CHK']
        with PATCH_ISO.open('rb') as f:
            f.seek(entry['offset'])
            raw=f.read(entry['size'])
        cls.pdn=next(b for n,_,b in chunks(raw) if n=='PDN')
        cls.u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
        cls.u.mem_map(0x08800000,0x01800000)
        executable=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/SYSDIR/EBOOT.BIN')
        with PATCH_ISO.open('rb') as f:
            f.seek(executable['offset']);boot=f.read(executable['size'])
        ph=struct.unpack_from('<I',boot,28)[0]
        entsize,count=struct.unpack_from('<HH',boot,42)
        for i in range(count):
            typ,off,vaddr,_,size,_,_,_=struct.unpack_from('<8I',boot,ph+i*entsize)
            if typ==1:
                cls.u.mem_write(vaddr,boot[off:off+size])
        cls.specs={c:json.loads((ROOT/f'translation/kbo_2026/{c}.json').read_text('utf8'))
                   for c in TEAM_CODES if c!='HH'}
        cls.specs['HH']=json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))

    def call(self, address, record, arg, extra=0):
        u=self.u
        u.mem_write(RECORD,record)
        u.reg_write(UC_MIPS_REG_A0,RECORD)
        u.reg_write(UC_MIPS_REG_A1,arg)
        u.reg_write(UC_MIPS_REG_A2,extra)
        u.reg_write(UC_MIPS_REG_SP,0x09f10000)
        u.reg_write(UC_MIPS_REG_RA,RETURN)
        u.emu_start(address,RETURN,count=20000)
        return u.reg_read(UC_MIPS_REG_V0)

    def test_primary_role_and_template_membership(self):
        from kbo_team_layout import layouts
        inv=json.loads((WORK/'inventory.json').read_text('utf8'))
        entry=next(e for e in inv['fbd'] if e['name']=='PLAYERDATA.CHK')
        with PATCH_ISO.open('rb') as f:
            f.seek(entry['offset']);raw=f.read(entry['size'])
        template=next(b for n,o,b in chunks(raw) if n=='PDTPLIST')
        for code,t in layouts().items():
            expected=[p['game_id'] for p in t['rows']]
            actual=list(struct.unpack_from('<%dH'%len(expected),template,t['start']*2))
            self.assertEqual(actual,expected,code)
            players={p['index'] for p in t['players']}
            staff={p['index'] for p in t['coaches']}
            self.assertFalse(players & staff,code)
            for p in t['players']:
                pos=(self.pdn[p['index']*192+168]&0x78)>>3
                allowed={'P':{0},'C':{1},'IF':{2,3,4,5},'OF':{6,7,8}}
                self.assertIn(pos,allowed[p['category']],(code,p['name'],pos))

    def test_all_registration_variants_return_full_name(self):
        for code,spec in self.specs.items():
            for p in spec['records']:
                r=self.pdn[p['index']*192:(p['index']+1)*192]
                expected=r[110:152].split(b'\0')[0]
                for selector in range(6):
                    self.u.mem_write(BUFFER,bytes(128))
                    self.call(NAME_GETTER,r,BUFFER,selector)
                    actual=bytes(self.u.mem_read(BUFFER,64)).split(b'\0')[0]
                    self.assertEqual(actual,expected,(code,p['name'],selector))

    def test_all_player_categories_and_staff_names_in_final_iso(self):
        players=staff=0
        errors=[]
        for code,spec in self.specs.items():
            for item in spec['records']:
                index=item['index']
                rec=bytes(self.pdn[index*192:(index+1)*192])
                self.assertEqual(rec[90]&63,TEAM_IDS[code],(code,index,item['name'],'team'))
                if item['kind']=='player':
                    players+=1
                    flags=[self.call(POSITION_GETTER,rec,i) for i in range(9)]
                    cat={'PC':'P','CC':'C'}.get(item['category'],item['category'])
                    observed=('P' if flags[0] else 'C' if flags[1] else
                              'OF' if max(flags[6:9]) else 'IF' if max(flags[2:6]) else 'NONE')
                    if cat=='P':self.assertEqual(observed,'P',(code,index,item['name'],flags))
                    elif cat=='C':self.assertEqual(observed,'C',(code,index,item['name'],flags))
                    elif cat=='OF':self.assertEqual(observed,'OF',(code,index,item['name'],flags))
                    else:self.assertIn(observed,('IF','OF'),(code,index,item['name'],flags))
                else:
                    staff+=1
                self.call(NAME_GETTER,rec,BUFFER,6)
                actual=bytes(self.u.mem_read(BUFFER,42)).split(b'\0')[0]
                expected=rec[110:152].split(b'\0')[0]
                self.assertTrue(actual,(code,index,item['name'],'blank registered name',rec[161]))
                self.assertEqual(actual,expected,(code,index,item['name'],'wrong registered-name selection'))
        self.assertEqual(players,619)
        self.assertEqual(staff,50)


if __name__=='__main__':
    unittest.main(verbosity=2)
