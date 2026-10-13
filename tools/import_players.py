"""검수한 레코드별 직접 표기를 전체 원본 이름 키와 연결한다."""
import json
from inventory import ROOT
def main():
 p=ROOT/'translation/players.json';rows=json.loads(p.read_text('utf8'));o=ROOT/'translation/player_name_overrides.json';over=json.loads(o.read_text('utf8'))
 for line in (ROOT/'translation/players_direct.txt').read_text('utf8').splitlines():
  if not line or line.startswith('#'):continue
  i,*ko=line.split('|');r=rows[int(i)];assert len(r['ja'])==len(ko),(i,r,ko);over['|'.join(r['ja'])]=ko;r['ko']=ko
 p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8');o.write_text(json.dumps(over,ensure_ascii=False,indent=2),'utf8')
 print('이름 번역',sum(bool(r['ko']) for r in rows),'/',len(rows))
if __name__=='__main__':main()
