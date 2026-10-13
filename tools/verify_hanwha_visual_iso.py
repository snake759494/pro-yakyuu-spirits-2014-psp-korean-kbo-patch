"""직전 승인된 명단 ISO와 최종 외형 ISO의 PLAYERDATA 변경 범위를 비교한다."""
import json,hashlib,struct
from inventory import ROOT
def spec():return json.loads((ROOT/'translation/hanwha_visual/appearance.json').read_text('utf8'))

def main():
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'));e=next(e for e in inv['fbd'] if e['name']=='PLAYERDATA.CHK')
 path=next(ROOT.glob('*Korean DEV*.iso'))
 with path.open('rb') as f:f.seek(e['offset']);data=f.read(e['size'])
 baseline=(ROOT/'build/baseline_before_hanwha_visual/PLAYERDATA.CHK').read_bytes();restored=bytearray(data);rows=[]
 for p in spec():
  o=5120+p['index']*192
  assert data[o+92:o+104].split(b'\0')[0].decode('ascii')==p['back_name']
  assert data[o+152]==p['height']
  word=struct.unpack_from('<I',data,o+156)[0];old=struct.unpack_from('<I',baseline,o+156)[0]
  assert word>>27==p['body_type'] and word&0x07ffffff==old&0x07ffffff
  for start,end in ((92,104),(152,153),(156,160)):restored[o+start:o+end]=baseline[o+start:o+end]
  if 'skin_type' in p:
   current=struct.unpack_from('<I',data,o+152)[0]
   assert (current>>23)&7==p['skin_type']
   value=struct.unpack_from('<I',restored,o+152)[0];previous=struct.unpack_from('<I',baseline,o+152)[0]
   struct.pack_into('<I',restored,o+152,(value&~0x03800000)|(previous&0x03800000))
  rows.append(dict(name=p['name'],index=p['index'],back_name=p['back_name'],height=p['height'],weight=p['weight'],body_type=p['body_type']))
 assert restored==baseline,'외형 허용 범위 밖 PLAYERDATA 변경'
 report=dict(passed=True,players_and_coaches=len(rows),previous_abilities_ids_voices_all_other_records_preserved=True,rows=rows)
 (ROOT/'build/hanwha_visual_data_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('외형 데이터 검증 통과: 67명, 기존 능력/ID/모션/다른 구단 보존')
if __name__=='__main__':main()
