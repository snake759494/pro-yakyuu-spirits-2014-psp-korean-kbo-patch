"""검토한 미션 문장의 숫자 변형. 전체 패턴 일치에서만 번역한다."""
from pathlib import Path
import json,re,unicodedata
root=Path(__file__).resolve().parents[1];p=root/'translation/new_ui.json';ui=json.loads(p.read_text('utf8'));audit=[]
patterns=[
(r'プロ通算(\d+)勝をあげろ',lambda m:f'프로 통산 {m[1]}승을 올려라'),
(r'通算(\d+)勝目をあげればクリアだ',lambda m:f'통산 {m[1]}승째를 올리면 성공'),
(r'シーズン(\d+)勝目をあげればクリア',lambda m:f'시즌 {m[1]}승째를 올리면 성공'),
(r'ホールドまたは救援勝利をあげて\nホールドポイント(\d+)に到達せよ',lambda m:f'홀드 또는 구원승으로\n홀드 포인트 {m[1]}을 달성하라'),
(r'試合を締めくくり\n(通算)?(\d+)セーブ目を記録せよ',lambda m:'경기를 마무리해\n'+('통산 ' if m[1] else '')+m[2]+'세이브를 기록하라'),
(r'シーズン奪三振(\d+)に到達すれば\nクリアだ',lambda m:f'시즌 {m[1]}탈삼진에 도달하면\n성공이다'),
(r'通算(\d+)奪三振を記録すれば\nクリアだ',lambda m:f'통산 {m[1]}탈삼진을 기록하면\n성공이다'),
(r'プロ通算(\d+)となる\nホールドポイントを記録せよ',lambda m:f'프로 통산 {m[1]}\n홀드 포인트를 기록하라'),
]
nouns={'安打':'안타','本安打':'안타','本塁打':'홈런','打点':'타점','盗塁':'도루','試合出場':'경기 출장','ホールドポイント':'홀드 포인트','奪三振':'탈삼진','セーブ':'세이브'}
for r in json.loads((root/'work/strings.json').read_text('utf8')):
 j=r['ja'];s=j.translate(str.maketrans('０１２３４５６７８９','0123456789'));k=None
 for pat,fn in patterns:
  m=re.fullmatch(pat,s)
  if m:k=fn(m);break
 m=re.fullmatch('(シーズン|通算)(\d+)('+ '|'.join(nouns)+')を達成せよ',s)
 if m:k=('시즌 ' if m[1]=='シーズン' else '통산 ')+m[2]+nouns[m[3]]+' 달성'
 m=re.fullmatch('(シーズン|通算)('+ '|'.join(nouns)+')(記録を更新せよ|新記録)',s)
 if m:k=('시즌 ' if m[1]=='シーズン' else '통산 ')+nouns[m[2]]+(' 기록 경신' if m[3].startswith('記録') else ' 신기록')
 m=re.fullmatch('第(一|二)(ストレート|スライダー|カーブ|フォーク|シンカー|シュート)系の(球威|制球|変化量)。',j)
 if m:k='제'+('1' if m[1]=='一' else '2')+{'ストレート':'직구','スライダー':'슬라이더','カーブ':'커브','フォーク':'포크','シンカー':'싱커','シュート':'슈트'}[m[2]]+' '+{'球威':'구위','制球':'제구','変化量':'변화량'}[m[3]]+'.'
 if k and j not in ui:ui[j]=k;audit.append({'ja':j,'ko':k})
p.write_text(json.dumps(ui,ensure_ascii=False,indent=2),'utf8');(root/'build/mission_templates.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),'utf8');print('미션 변형 추가',len(audit))
