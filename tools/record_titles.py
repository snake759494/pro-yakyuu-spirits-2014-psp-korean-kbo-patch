"""직접 번역한 기록 표제의 숫자 변형을 원문 전체 일치로 확장한다."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=ROOT/'translation/new_ui.json';ui=json.loads(p.read_text('utf8'));audit=[]
 nouns={'安打':'안타','本塁打':'홈런','打点':'타점','盗塁':'도루','出場試合':'출장','勝利':'승리','登板':'등판','セーブ':'세이브','ホールドポイント':'홀드 포인트','ホールド':'홀드','奪三振':'탈삼진','投球回':'투구 이닝','二塁打':'2루타','三塁打':'3루타','犠牲バント':'희생 번트','犠牲フライ':'희생 플라이'}
 counts={'安打':'안타','本塁打':'홈런','打点':'타점','盗塁':'도루','勝':'승','試合登板':'경기 등판','セーブ':'세이브','ホールドポイント':'홀드 포인트','奪三振':'탈삼진','投球回':'이닝'}
 for r in json.loads((ROOT/'work/strings.json').read_text('utf8')):
  j=r['ja'];k=None
  m=re.fullmatch('(通算|シーズン)([0-9０-９]+)('+ '|'.join(counts)+')',j)
  if m:k=('통산' if m[1]=='通算' else '시즌')+' '+str(int(m[2]))+counts[m[3]]
  m=re.fullmatch('(通算|シーズン)('+ '|'.join(nouns)+')記録(?:の)?更新',j)
  if m:k=('통산' if m[1]=='通算' else '시즌')+' '+nouns[m[2]]+' 기록 경신'
  m=re.fullmatch('([0-9０-９]+)試合出場',j)
  if m:k=str(int(m[1]))+'경기 출장'
  m=re.fullmatch('プロ初('+ '|'.join(nouns)+')',j)
  if m:k='프로 첫 '+nouns[m[1]]
  if k and j not in ui:ui[j]=k;audit.append({'ja':j,'ko':k})
 p.write_text(json.dumps(ui,ensure_ascii=False,indent=2),'utf8');(ROOT/'build/record_titles.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),'utf8');print('기록 표제 추가',len(audit))
if __name__=='__main__':main()
