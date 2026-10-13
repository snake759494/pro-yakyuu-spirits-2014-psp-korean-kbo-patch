"""KBO 전체 선수단 적용 범위 문서와 현재 검증 메타데이터를 갱신한다."""
import json,hashlib,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ISO=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
FULL=json.loads((ROOT/'work/kbo_roster_research/2026_kbo_club_roster.json').read_text('utf8'))
REPORT=json.loads((ROOT/'build/build_report.json').read_text('utf8'))
ROSTER_REPORT=json.loads((ROOT/'build/kbo_rosters.json').read_text('utf8'))
HASH=hashlib.sha256(ISO.read_bytes()).hexdigest()
CODE_ORDER=['LG','SS','HT','WO','KT','LT','HH','OB','SK','NC']
TEAM={'LG':'LG 트윈스','SS':'삼성 라이온즈','HT':'KIA 타이거즈','WO':'키움 히어로즈','KT':'KT 위즈','LT':'롯데 자이언츠','HH':'한화 이글스','OB':'두산 베어스','SK':'SSG 랜더스','NC':'NC 다이노스'}

# Preserve the complete official Hanwha roster/staff source alongside its earlier,
# individually modeled 62-player in-game data set.
hhpath=ROOT/'translation/kbo_2026/HH.json'
hh=json.loads(hhpath.read_text('utf8'))
hh.update(full_roster_date='2026-02-10',full_roster_source='https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11831',
          official_roster_players=FULL['HH']['declared_players'],applied_players=ROSTER_REPORT['teams']['HH']['players'],
          all_official_roster_players=FULL['HH']['players'],official_staff_count=FULL['HH']['declared_staff'],
          all_official_staff=FULL['HH']['staff'],applied_staff_slots=5)
hh['limitations']=(hh.get('limitations') or [])+['KBO 2026-02-10 명단은 한화 64명을 공시하지만 기존 외형/능력 ID와 연결한 게임 적용은 62명으로 유지했다. 원본 한화 모델에서 추가 2명은 아직 레코드로 연결하지 않았다.']
hhpath.write_text(json.dumps(hh,ensure_ascii=False,indent=2),'utf8')

rows=['# KBO 2026 전체 선수단 변환', '',
      '원본과 같은 폴더의 Korean DEV ISO에 KBO 10팀 선수 명단을 확장 적용했다. 원본 ISO는 변경하지 않았다.', '',
      '## 공식 기준과 게임 반영', '',
      '선수단 기준은 KBO가 2026년 2월 10일 공시한 구단별 코칭스태프·소속선수 명단이며, 시즌 개막 1군 등록 변경은 2026년 3월 28일 KBO 등록 현황을 우선했다. 두 기준일은 서로 다르므로 개막 1군 등록이 바뀐 선수는 공식 2월 명단의 같은 포지션 예비 슬롯을 대체했다.', '',
      'KBO 게임 슬롯은 선수 ID와 음성 키를 유지해 이름·신상·기록을 옮겼다. 9개 구단은 공식 등록 선수 전원을 반영했고, 한화는 기존 검수된 선수·능력·얼굴 세트 62명을 유지했다. KBO 2월 공시 한화 명단 64명 중 2명은 아직 게임 레코드에 연결되지 않아 이번 패치의 총 적용 선수는 619명이다.', '',
      '공식 등록 코칭스태프 전체 명단은 각 구단 JSON에 보존했다. 다만 게임은 구단마다 감독·코치 레코드 5개만 제공하므로 감독과 주요 코치 4명씩, 총 50명을 표시·적용했다. 나머지 공식 코치 이름을 팀별 원본 선수 데이터 슬롯으로 억지 변환하지 않았다.', '',
      '| 구단 | 게임 반영 선수 | 게임 반영 스태프 | 공식 명단 스태프 |', '|---|---:|---:|---:|']
for c in CODE_ORDER:
    spec=json.loads((ROOT/'translation/kbo_2026'/f'{c}.json').read_text('utf8'))
    applied=ROSTER_REPORT['teams'][c]
    rows.append(f"| {TEAM[c]} | {applied['players']}명 | {applied['staff']}명 | {spec.get('official_staff_count',len(spec.get('all_official_staff',[])))}명 |")
rows += ['', '공식 전체 선수 이름과 포지션은 `translation/kbo_2026/{구단코드}.json`의 `records`에, 전체 스태프 명단은 `all_official_staff`에 보존했다. 한화의 전체 공시 선수단과 스태프 원문 구조화 자료는 `translation/kbo_2026/HH.json`에 있다. 원본 KBO XLSX와 날짜별 등록 HTML/JSON은 `work/kbo_roster_research/`에 보존했다.', '',
         '## 능력치·외형의 범위', '',
         f"공식 KBO 시즌 기록을 게임 척도로 환산한 비한화 선수는 {ROSTER_REPORT['statistics']}명이다. 나머지 전체 로스터는 공식 한글 이름과 포지션을 반영했지만, 공개 기록 ID가 확보되지 않은 2군 선수는 게임 능력치를 새로 산정하지 못해 원 레코드 능력값을 유지한다. 외국인 등록 이름을 반영하며 고정 크기·ID·음성 키를 보존했다.", '',
         'KBO 10팀 로고와 기존 유니폼 색상·엠블럼 및 구장명·지역 표기는 종전 빌드 작업을 유지했다. 한화 외 선수의 얼굴 사진, 체형, 등 영문 이름과 구단별 3D 구장 모델은 완성 범위가 아니다. 한화 62명에 적용했던 사진 기반 외형은 유지했다.', '',
         '## 한계와 검증', '',
         '단일 리그·10팀 순위·DH 정규시즌 코드는 유지된다. 2014 달력, 포스트시즌과 다음 시즌 로직은 KBO 방식으로 바뀌지 않았다. 이번 ISO는 PPSSPP에서 실행하지 않았으므로 선수단 화면·새 페넌트 저장·경기 중 유니폼을 실기 검증했다고 보지 않는다. 설치 데이터는 재생성하지 않았다.', '',
         f"정적 ISO 검증은 통과했다. 현재 ISO SHA-256: `{HASH}`. 원본 해시와 실행 검증 범위는 `build/validation.json`, `build/runtime_validation.json`, `SHA256SUMS.txt`에서 확인한다.", '',
         '## 공식 출처', '',
         '- [KBO 2026 구단별 코칭스태프 및 소속선수 명단 공시 (2026-02-10)](https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11831)',
         '- [KBO 날짜별 선수 등록 현황](https://www.koreabaseball.com/Player/Register.aspx)', '']
(ROOT/'KBO_2026_TEAMS.md').write_text('\n'.join(rows),'utf8')

# Bind the new build metadata to the exact ISO without inheriting prior runtime proof.
REPORT['league_trial']['kbo_rosters']=True
REPORT['league_trial']['kbo_roster_players']=ROSTER_REPORT['assigned_players']
REPORT['league_trial']['game_staff_slots']=ROSTER_REPORT['assigned_staff']
REPORT['league_trial']['status']='10팀 정규시즌 일정·통합 순위·DH·KBO 전체 선수단; 포스트시즌은 원본 로직'
(ROOT/'build/build_report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),'utf8')
trialpath=ROOT/'build/league_trial.json'
trial=json.loads(trialpath.read_text('utf8'));trial['kbo_rosters']=True;trial['kbo_roster_players']=ROSTER_REPORT['assigned_players'];trial['game_staff_slots']=ROSTER_REPORT['assigned_staff'];trial['status']='10팀 정규시즌 일정·통합 순위·DH·KBO 전체 선수단; 포스트시즌은 원본 로직'
trialpath.write_text(json.dumps(trial,ensure_ascii=False,indent=2),'utf8')

runpath=ROOT/'build/runtime_validation.json'
old=json.loads(runpath.read_text('utf8'))
shutil.copy2(runpath,ROOT/'build/runtime_validation_before_full_rosters.json')
runtime=dict(status='정적 검사 통과; 전체 선수단 빌드의 PPSSPP 실기 검증은 미실행',tested_at='2026-10-10',iso=ISO.name,iso_sha256=HASH,
 original_sha256=REPORT['original_sha256'],runtime_verified=False,emulator='PPSSPP 실행하지 않음',static_validation='build/validation.json',static_validation_passed=True,
 checks=['ISO 크기와 LBA 배치 보존','ISO readback과 빌드 SHA-256 일치','독립 정적 영역 검증 통과','10팀 단일 일정·통합 순위·DH 정적 검증 통과','비한화 9개 구단 공식 소속 선수 명단 전체 이름 연결','구단당 감독/코치 5슬롯 적용, 전체 공식 스태프 명단 소스 보존','설치 데이터 원본 보존'],
 not_runtime_checked=['새 페넌트 팀 선택과 팀별 전체 선수단 화면','새 KBO 선수의 상세 능력·신체 정보와 경기 출전','경기 중 선수 이름·등번호·유니폼·엠블럼','각 구단 구장 화면과 저장/불러오기·시즌 진행'],
 previous_runtime_evidence={'file':'build/baseline_before_kbo2026/runtime_validation_previous_hanwha.json','iso_sha256':'17487f837aa6ab24df4f0d32ebc5af1af4fdfffe7a19ef81530fae6a4a0ea830','applies_to_current_iso':False},
 limitations=['한화는 기존 62명 모델을 유지했으며 2026 공식 명단 64명 중 2명은 미연결.','게임에서 표시 가능한 팀별 감독/코치는 5명으로 제한되며 전체 등록 코칭스태프는 출전 명단이 아닌 소스 JSON에 보존.','비한화 공식 성적을 이용해 게임 능력을 변환한 선수는 138명이며 나머지 선수의 능력값은 원 레코드를 유지.','한화 외 선수 얼굴·체형·영문 등 이름 및 타 구단 3D 구장은 적용하지 않음.','포스트시즌과 다음 해 진행은 원본 로직이며 장기 플레이를 검증하지 않음.'],previous_snapshot=old.get('iso_sha256'))
runpath.write_text(json.dumps(runtime,ensure_ascii=False,indent=2),'utf8')

orig='d58bb782f027e0889e47c145462b2c694433c856fcbf2411ce5d186a40521e5f'
(ROOT/'SHA256SUMS.txt').write_text(f"{orig}  Pro Yakyuu Spirits 2014 (Japan) (v2.00).iso\n{HASH}  {ISO.name}\n",'utf8')
(ROOT/'build/SHA256SUMS.txt').write_text((ROOT/'SHA256SUMS.txt').read_text('utf8'),'utf8')
print('docs/runtime/SHA updated',HASH)
