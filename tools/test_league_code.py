"""실제 MIPS 코드로 통합 순위·DH·선택 목록을 검사한다. 게임 실행 검증과 별개다."""
import json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import *
from league_code import patches
from inventory import ROOT, WORK

u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
u.mem_map(0x8800000, 0x1800000)
for name in ('BOOT.BIN', 'com_sel.elf'):
    raw = next((WORK / 'iso').rglob(name)).read_bytes()
    ph = struct.unpack_from('<I', raw, 28)[0]
    off, va, _, size = struct.unpack_from('<4I', raw, ph + 4)
    u.mem_write(va, raw[off:off + size])
for name, addr, raw, _ in patches():
    if name in ('BOOT.BIN', 'com_sel.elf'):
        u.mem_write(addr, raw)

def imports(cpu, addr, size, user):
    dst, src, length = (cpu.reg_read(r) for r in (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2))
    cpu.mem_write(dst, bytes(cpu.mem_read(src, length)))
    cpu.reg_write(UC_MIPS_REG_V0, dst)
    cpu.reg_write(UC_MIPS_REG_PC, cpu.reg_read(UC_MIPS_REG_RA))

u.hook_add(UC_HOOK_CODE, imports, begin=0x8a848a0, end=0x8a848a0)
u.reg_write(UC_MIPS_REG_CP0_STATUS, u.reg_read(UC_MIPS_REG_CP0_STATUS) | 0x20000000)
central, pacific, out, end = 0x9900000, 0x9901000, 0x9902000, 0x9ff0000
results = []
for case in ('descending', 'ascending', 'all_zero'):
    for team in range(12):
        for opp in range(12):
            row = bytearray(12)
            if team < 10 and opp == (team + 1) % 10 and case != 'all_zero':
                row[8] = 10 - team if case == 'descending' else team + 1
                row[9] = 10 - row[8]
            if opp >= 10:
                row[8] = 99
            u.mem_write((central if team < 6 else pacific) + (team % 6) * 144 + opp * 12, bytes(row))
    u.mem_write(out, bytes(336))
    for reg, value in ((UC_MIPS_REG_SP, 0x9f00000), (UC_MIPS_REG_RA, end), (UC_MIPS_REG_A0, out), (UC_MIPS_REG_A1, central), (UC_MIPS_REG_A2, pacific)):
        u.reg_write(reg, value)
    u.emu_start(0x8c61790, end, count=2000000)
    rows = []
    for i in range(10):
        b = bytes(u.mem_read(out + i * 28, 28))
        rows.append(dict(team=struct.unpack_from('<I', b, 24)[0], wins=b[8], losses=b[9], rank=struct.unpack_from('<I', b, 20)[0]))
    assert sorted(r['team'] for r in rows) == list(range(10)), rows
    assert all(r['wins'] <= 10 and r['losses'] <= 10 for r in rows), rows
    if case != 'all_zero':
        assert [r['wins'] for r in rows] == list(range(10, 0, -1)), rows
    else:
        assert all(r['wins'] == r['losses'] == 0 for r in rows), rows
    results.append(dict(case=case, records=rows))

for schedule_id in range(46):
    u.mem_write(central, struct.pack('<I', schedule_id))
    u.reg_write(UC_MIPS_REG_A0, central)
    u.reg_write(UC_MIPS_REG_RA, end)
    u.emu_start(0x8a2dfe4, end, count=20)
    assert u.reg_read(UC_MIPS_REG_V0) == 0

obj = 0x9980000
u.reg_write(UC_MIPS_REG_S4, obj)
u.reg_write(UC_MIPS_REG_S5, 1)
u.reg_write(UC_MIPS_REG_S7, 0x40000)
u.mem_write(obj + 0x4c, bytes(4))
u.emu_start(0x8c61910, 0x8ce38dc, count=1000)
assert struct.unpack('<10I', u.mem_read(obj + 0x3a414, 40)) == tuple(range(10))
report = dict(passed=True, rank_cases=results, dh_inputs_tested=46, selector_ids=list(range(10)), scope='MIPS CPU 검사. 실제 게임 화면·시즌 완주 검증은 별도.')
row_address = 0x99d0000
for index in (0, 9, 10, 11, None):
    if index is not None:
        u.mem_write(row_address, struct.pack('<I', index))
    def next_row(cpu, addr, size, user):
        cpu.reg_write(UC_MIPS_REG_V0, row_address if index is not None else 0)
        cpu.reg_write(UC_MIPS_REG_PC, cpu.reg_read(UC_MIPS_REG_RA))
    hook = u.hook_add(UC_HOOK_CODE, next_row, begin=0x8b63dc8, end=0x8b63dc8)
    u.reg_write(UC_MIPS_REG_SP, 0x9f00000); u.reg_write(UC_MIPS_REG_RA, end)
    u.emu_start(0x8c61970, end, count=1000)
    assert u.reg_read(UC_MIPS_REG_V0) == (row_address if index in (0, 9) else 0)
    assert u.reg_read(UC_MIPS_REG_SP) == 0x9f00000
    u.hook_del(hook)
table, descriptor = 0x99e0000, 0x99e1000
u.mem_write(table + 0x34, struct.pack('<I', descriptor))
u.mem_write(table + 0x70, struct.pack('<I', 12))
u.mem_write(descriptor, struct.pack('<I', 12))
def numeric_table(cpu, addr, size, user):
    assert cpu.reg_read(UC_MIPS_REG_A0) == table
    assert struct.unpack('<I', cpu.mem_read(descriptor, 4))[0] == 10
    assert struct.unpack('<I', cpu.mem_read(table + 0x70, 4))[0] == 10
    cpu.reg_write(UC_MIPS_REG_V0, 0x99e2000)
    cpu.reg_write(UC_MIPS_REG_PC, cpu.reg_read(UC_MIPS_REG_RA))
hook = u.hook_add(UC_HOOK_CODE, numeric_table, begin=0x8b63e54, end=0x8b63e54)
for reg, value in ((UC_MIPS_REG_A0, table), (UC_MIPS_REG_RA, end), (UC_MIPS_REG_SP, 0x9f00000), (UC_MIPS_REG_S0, 0x1234), (UC_MIPS_REG_S1, 0x5678)):
    u.reg_write(reg, value)
u.emu_start(0x8c619b0, end, count=1000)
assert struct.unpack('<I', u.mem_read(descriptor, 4))[0] == 12
assert struct.unpack('<I', u.mem_read(table + 0x70, 4))[0] == 12
assert u.reg_read(UC_MIPS_REG_V0) == 0x99e2000
assert u.reg_read(UC_MIPS_REG_SP) == 0x9f00000
assert u.reg_read(UC_MIPS_REG_S0) == 0x1234 and u.reg_read(UC_MIPS_REG_S1) == 0x5678
u.hook_del(hook)
report.update(row_iterator_excludes_inactive=True, numeric_table_uses_10_rows_and_restores_layout=True)
(ROOT / 'build/league_code_cpu_test.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
print('통과: 순위 3개 경우, DH 46개 입력, 선택 ID 0~9')
