"""PSP의 192바이트 선수 레코드에서 표시 이름만 추출한다."""
from pathlib import Path
import json,unicodedata
from inventory import ROOT,WORK
from analyze import chunks

def main():
 path=ROOT/'translation/players.json';previous=json.loads(path.read_text(encoding='utf8')) if path.exists() else []
 known={tuple(r['ja']):r['ko'] for r in previous if r.get('ko')}
 overrides=json.loads((ROOT/'translation/player_name_overrides.json').read_text(encoding='utf8'));rows=[]
 for chunk,base,data in chunks((WORK/'assets/PLAYERDATA.CHK').read_bytes()):
  if chunk not in ('PDN','PDTS'):continue
  assert len(data)%192==0
  for i in range(len(data)//192):
   off=i*192;raw=data[off+110:off+152]
   if raw in (b'\xcc'*42,b'\0'*42):continue
   try:names=[s.decode('cp932') for s in raw.rstrip(b'\0').split(b'\0')]
   except UnicodeDecodeError:continue
   if not names[0]:continue
   rows.append(dict(chunk=chunk,index=i,offset=base+off+110,ja=names,ko=overrides.get('|'.join(names)) or known.get(tuple(names)),latin=data[off+92:off+104].split(b'\0')[0].decode('ascii',errors='replace')))
 path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print(len(rows),'이름 레코드;',sum(bool(r['ko']) for r in rows),'번역 연결')
if __name__=='__main__':main()
