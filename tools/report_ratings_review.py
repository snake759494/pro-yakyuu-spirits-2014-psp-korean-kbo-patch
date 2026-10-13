"""최종 ISO 및 실행 검사에 묶인 능력치 전수 재검수 보고서."""
import json,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'build/ratings_review'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 m=read(ROOT/'translation/kbo_2026/ratings_review.json');before=read(D/'before.json')
 iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso';digest=sha(iso)
 live=read(D/'live_all.json');assert live['iso_sha256']==digest and live['passed']
 result={'iso_sha256':digest,'manifest_sha256':sha(ROOT/'translation/kbo_2026/ratings_review.json'),
 'baseline_iso_sha256':'0e9febd9c81cf47c5da94df90002a3034fbc3280336fd4f1aa47c22fc60862a0',
 'opening_date':'2026-03-28','stats_last_year':2025,'players':619,'opening_players':290,
 'baseline_decoder_note':'before.json의 catching/throwing 키는 수정 전 역전된 명칭이다. 원시 비교 자료를 보존했다.',
 'game_ratings_are_estimates':True,'teams':{},'unverified_pitchers':[],'changes':[]}
 lines=['# 2026 개막 로스터·능력치 전수 재검수','',f'최종 ISO SHA-256: `{digest}`','',
 'KBO 2026년 3월 28일 등록 명단 290명과 선수 고유 ID를 대조했다. 게임에 수록된 619명 전체의 기본 능력치·구종을 다시 기록했다. 2026 시즌 중 성적으로 능력치를 역산하지 않았다.',
 '', '## 오류 원인과 수정', '',
 '- 기존 일부 구단은 능력치 입력이 누락돼 일본 슬롯의 수치를 상속했다. 일부는 불완전한 명세로 84바이트 능력 영역을 초기화하여 구종이 모두 비었다.',
 '- 포구와 송구의 비트 필드가 뒤바뀌어 있던 오류를 상세 화면과 대조해 수정했다. 어깨 표기도 별도 표시한다.',
 '- 619명 완전 명세를 한 경로에서 적용하고 PDN/PDW 두 능력치 사본을 일치시켰다. 선수 ID·음성 키·레코드 크기를 보존했다.',
 '- 29명 명단을 넣어도 새 페넌트 생성자가 28명으로 잘랐다. 생성자와 편성 보정 함수의 비교·상한 명령 여섯 개를 수정했다. 29명 등록과 실제 경기 출전 인원 규칙은 별개다.',
 '- 삼성의 중복 이승현 슬롯은 공식 ID·생일을 대조하여 누락됐던 홍원표로 바로잡았다.',
 '- 개막일 미등록인 선발/외국인은 임의로 1군에 넣지 않았다. 선발 다섯 자리를 채우려고 불펜 투수를 넣던 편성도 바로잡았다.',
 '', '## 구단별 대조', '', '|구단|전체 선수|개막 투수/야수|수정 전 빈 구종 투수|수정 후|구종 미확인|','|---|---:|---:|---:|---:|---:|']
 for code,t in m['teams'].items():
  ps=t['players'];old={p['index']:p for p in before[code]};active=[p for p in ps if p['opening_entry']]
  missing=[p for p in ps if p['category']=='P' and ('미확인' in p['pitch_basis'] or '미확보' in p['pitch_basis'])]
  b=sum(p['category']=='P' and not p['pitch_kinds'] for p in old.values());a=sum(p['category']=='P' and not p['pitches'] for p in ps)
  np=sum(p['category']=='P' for p in active)
  result['teams'][code]=dict(players=len(ps),opening_pitchers=np,opening_batters=len(active)-np,before_empty_pitchers=b,after_empty_pitchers=a,unverified_pitchers=len(missing))
  lines.append(f'|{code}|{len(ps)}|{np}/{len(active)-np}|{b}|{a}|{len(missing)}|')
  result['unverified_pitchers'] += [dict(team=code,name=p['name'],player_id=p['player_id'],opening=p['opening_entry'],basis=p['pitch_basis']) for p in missing]
  for p in ps:result['changes'].append(dict(team=code,index=p['index'],name=p['name'],before=old[p['index']],after=p))
 counts=Counter(p['pitch_basis'] for t in m['teams'].values() for p in t['players'] if p['category']=='P')
 result['pitch_sources']=dict(counts)
 lines += ['', '## 자료와 환산 범위', '',
 '[개막 등록 명단](https://www.koreabaseball.com/Player/Register.aspx), [2026 운영 규정](https://www.koreabaseball.com/Kbo/League/GameManage2026.aspx), [KBO 선수 기록](https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx), [2025 수비 기록](https://www.koreabaseball.com/Record/Player/Defense/Basic.aspx)을 사용했다. 원문과 고유 ID는 work/ratings_review에 보존했다.',
 '', '능력치 등급은 KBO 공식 수치가 아니다. 2025년까지 최근 세 시즌 기록을 1/.6/.35로 가중하고 소표본을 평균으로 보정했다. 수비는 포지션별 이닝·실책을 반영했다. 좌/우 상대별 컨택, 수비 범위, 최고 구속 일부와 구종별 게임 등급은 추정이다. 특수능력은 일본 선수의 것을 상속하지 않는다.',
 '', '구종 자료: [2025 투구 분석](https://kbo-analytics-2025.vercel.app/), [야구나라](https://www.yagoonara.com/)의 연도 지정 공개 구종 기록 및 입단 전 구단 발표·스카우팅 보도. 선수별 출처는 translation/kbo_2026/ratings_review.json에 연결했다.',
 '', f'투수 319명 중 {319-len(result["unverified_pitchers"])}명은 공개 구종 자료와 대조했고, {len(result["unverified_pitchers"])}명은 구종 구성이 미확인이다. 미확인 선수에게 빈 구종이나 일본 슬롯 구종을 상속시키지 않고 명시적 임시 추정값을 넣었다. 이를 검증 완료된 실측값으로 간주하면 안 된다.',
 '', '미확인 구종 선수: '+', '.join(p['team']+' '+p['name']+(' (개막 등록)' if p['opening'] else '') for p in result['unverified_pitchers'])+'.',
 '', '## 실행 검증', '',
 '최종 ISO를 설치 데이터·치트·외부 텍스처·상태저장 없이 부팅하고, 사용자 SYSTEM.DAT의 독립 복사본에서 새 페넌트를 생성했다. live_all.json은 실제 게임 RAM의 619명 능력치·구종·등록명·포지션, 290명 등록 플래그, 스태프 50명의 포인터 연결을 읽기 전용으로 전수 대조한 결과다.',
 '', '시즌 시작 후 한화의 투수 11명·야수 18명(오재원 포함) 유지와 등록 확정을 추가 확인했다.',
 '', '개별 화면 확인은 final 폴더의 스크린샷 목록을 기준으로 한다. 전 선수 개별 화면을 수동으로 열었다는 뜻은 아니다. 시즌 완주·전 경기·실기 PSP 검증은 포함하지 않는다. 기존 페넌트 저장 파일의 선수 데이터 자동 이행도 검증하지 않았다.',
 '', '잔여 사항: 통산 기록·기록 달성 알림에는 원 일본 슬롯의 경력이 남아 있다(정우주 홀드/세이브 달성 예고 화면에서 확인). 이번 수정의 기본 능력치·구종과 별도 데이터이며, 이 부분까지 실제 경력으로 교체했다고 주장하지 않는다.',
 '', '수치 전수 검사: 최종 ISO에서 직접 읽은 레코드를 원 게임 MIPS 함수로 실행해 컨택·파워·주력·어깨·포구·송구·회복·수비·구속·구종·변화량·구위·제구를 대조했다.']
 copyfile=D/'drive_copy.json'
 if copyfile.exists():
  copy=read(copyfile)
  if copy.get('destination_sha256')==digest:
   result['drive_copy']=copy
   lines += ['', '## 전달 확인', '',
     f"`{copy['destination']}`에 덮어썼다. 크기 {copy['size']:,}바이트, 전체 SHA-256 일치. 복사 확인 시각: {copy['copied_at']}. G 드라이브에서 읽은 파일을 검증했으며 클라우드 서버 동기화 상태는 별도 확인하지 않았다.",
     '', '원본 ISO와 사용자 원본 SYSTEM.DAT는 보존했다. PPSSPP는 검증 후 종료했다. 변경된 개막 편성과 능력치는 새 페넌트로 확인해야 한다.']
 (D/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
 (ROOT/'ROSTER_RATINGS_REVIEW.md').write_text('\n'.join(lines)+'\n','utf8')
 print(digest)
if __name__=='__main__':main()
