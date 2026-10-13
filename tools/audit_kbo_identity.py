"""공식 KBO ID/보직/사진과 ISO 선수·초상화·3D 얼굴 연결의 전수 감사."""
import json,struct,hashlib,collections
from inventory import ROOT
from analyze import chunks
from kbo_team_layout import layouts
read=lambda p:json.loads((ROOT/p).read_text('utf8'))
official=read('work/identity_audit/official_profiles.json');assert not official['errors']
profiles={p['index']:p for p in official['players']}
appearance={p['index']:p for p in read('translation/kbo_2026/appearance.json')}
ratings=read('translation/kbo_2026/ratings_review.json')
inv=read('work/inventory.json');entries={e['name']:e for e in inv['fbd']}
iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
with iso.open('rb') as f:
    digest=hashlib.file_digest(f,'sha256').hexdigest()
    e=entries['PLAYERDATA.CHK'];f.seek(e['offset']);pdn=dict((n,b) for n,o,b in chunks(f.read(e['size'])))['PDN']
    e=entries['COMFACE.BIN'];f.seek(e['offset']);portraits=f.read(e['size'])
    face_bytes={}
    for p in appearance.values():
        if p['dedicated_face']:
            e=entries[p['face_file']];f.seek(e['offset']);face_bytes[p['index']]=hashlib.sha256(f.read(e['size'])).hexdigest()
rows=[]
for code,t in layouts().items():
    rmap={p['index']:p for p in ratings['teams'][code]['players']}
    for j,p in enumerate(t['players']):
        idx=p['index'];o=profiles[idx];a=appearance[idx];r=rmap[idx]
        assert str(r['player_id'])==o['player_id']==a['player_id'],(code,p['name'],'공식 ID')
        clean=lambda s:s.replace(' ','').split('(')[0]
        assert clean(r['name'])==clean(o['official_name']),(code,r['name'],o['official_name'])
        cat=next(v for k,v in [('투수','P'),('포수','C'),('내야수','IF'),('외야수','OF')] if o['position'].startswith(k))
        assert r['category']==cat,(code,p['name'],r['category'],cat)
        assert hashlib.sha256((ROOT/a['photo']).read_bytes()).hexdigest()==a['photo_sha256']
        assert struct.unpack_from('<H',pdn,idx*192+86)[0]==a['face_id']
        ordinal=next(k for k,q in enumerate(t['rows']) if q['index']==idx);slot=t['start']+ordinal
        rows.append(dict(team=code,index=idx,name=r['name'],player_id=o['player_id'],category=cat,official_position=o['position'],source=o['source'],photo=a['photo'],photo_source=a['photo_source'],photo_sha256=a['photo_sha256'],portrait_slot=slot,portrait_sha256=hashlib.sha256(portraits[slot*6144+16:slot*6144+4112]).hexdigest(),face_file=a['face_file'],dedicated_face=a['dedicated_face'],face_file_sha256=face_bytes.get(idx)))
assert len(rows)==619 and len({r['index'] for r in rows})==619
assert len({r['portrait_slot'] for r in rows})==619
assert len({r['face_file'] for r in rows if r['dedicated_face']})==610
original=next(p for p in ROOT.glob('*.iso') if 'Korean' not in p.name)
with original.open('rb') as f:
    for row in rows:
        if row['dedicated_face']:
            e=entries[row['face_file']];f.seek(e['offset'])
            row['original_face_sha256']=hashlib.sha256(f.read(e['size'])).hexdigest()
            assert row['original_face_sha256']!=row['face_file_sha256'],row['name']
report=dict(iso_sha256=digest,players=len(rows),categories=dict(collections.Counter(r['category'] for r in rows)),dedicated_3d_faces=610,dedicated_3d_faces_changed_from_original=610,generic_3d_faces=9,method='KBO 공식 고유 ID·포지션·사진 해시와 ISO 레코드 얼굴 ID·초상화 슬롯 전수 대조',passed=True,rows=rows)
(ROOT/'build/identity_audit/official_iso_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))
