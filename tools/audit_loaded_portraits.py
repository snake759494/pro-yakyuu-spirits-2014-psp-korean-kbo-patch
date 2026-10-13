"""현재 PPSSPP가 읽은 COMFACE 픽셀을 최종 ISO와 바이트 단위 대조한다."""
import json,hashlib,sys
from inventory import ROOT
from ppsspp_rpc import Debugger,readmem
from kbo_team_layout import layouts
inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'))
e=next(e for e in inv['fbd'] if e['name']=='COMFACE.BIN')
iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
with iso.open('rb') as f:
    digest=hashlib.file_digest(f,'sha256').hexdigest();f.seek(e['offset']);data=f.read(e['size'])
d=Debugger();status=d.call('cpu.status')
try:
    d.call('cpu.stepping');ram=readmem(d,0x8800000,0x1800000)
finally:
    if not status.get('stepping'):d.call('cpu.resume')
    d.close()
names={t['start']+j:dict(team=c,index=p['index'],name=p['name']) for c,t in layouts().items() for j,p in enumerate(t['rows'])}
found=[]
for i in range(len(data)//6144):
    b=data[i*6144+16:i*6144+4112];at=ram.find(b[1024:1088])
    if at>=1024 and ram[at-1024:at-1024+4096]==b:
        found.append(dict(slot=i,address=hex(0x8800000+at-1024),sha256=hashlib.sha256(b).hexdigest(),**names.get(i,{})))
expected=int(sys.argv[1]);assert any(p['slot']==expected for p in found),(expected,found)
report=dict(iso_sha256=digest,expected_slot=expected,loaded=found,memory_write=False,passed=True)
(ROOT/f'build/identity_audit/final/portrait_{expected}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(report,ensure_ascii=False))
