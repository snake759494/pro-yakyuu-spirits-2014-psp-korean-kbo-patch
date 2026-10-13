"""원 평가 함수 분석과 최종 PPSSPP 증거를 연결한 검수 보고서."""
import json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'build/team_strength'
read=lambda p:json.loads(p.read_text('utf8'))
iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
with iso.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
before=read(D/'before.json');after=read(D/'after/after.json');sim=read(D/'simulation.json')
names=dict(LG='LG',SS='삼성',HT='KIA',WO='키움',KT='KT',HH='한화',OB='두산',SK='SSG',NC='NC',LT='롯데')
bar=lambda x,k:20+80*(min(75 if k=='pitching' else 70,max(50,x))-50)/(25 if k=='pitching' else 20)
for a in after:
 s=next(r for r in sim if r['code']==a['code'])['after']
 for k in ('pitching','batting','fielding'):assert abs(a[k]-s[k])<.0001,(a['code'],k,a[k],s[k])
rows=[]
for a in after:
 b=next(r for r in before if r['code']==a['code'])
 rows.append('| '+names[a['code']]+' | '+' | '.join(f'{bar(b[k],k):.1f} → {bar(a[k],k):.1f}' for k in ('pitching','batting','fielding'))+' |')
text='''# 페넌트 팀 선택 전력 평가 재검수

## 원인과 계산 경로

`com_sel.elf:0x08cd9b90`은 선수 데이터를 읽어 팀 전력을 계산한다. 고정된 구단 점수표가 아니다.
활성 투수의 개인 피칭 평가를 평균하고, 좌/우 상대 선발 타순의 타자 평가와 주 포지션 수비 평가를 평균한다.
이번 실제 화면의 표본은 투수 11~14명, 타격/수비 16 또는 18개다. 1·2군 모든 선수의 단순 평균은 아니다.
개인 함수는 피칭 `BOOT:0x0890303c`, 배팅 `0x08900898`, 필딩 `0x08900984`이다.
평균 직후 `0x08cd9e40`에서 부동소수점 레지스터 F22/F20/F24를 읽었다.

- 피칭 막대(%) = `20 + 80 × (clamp(평균, 50, 75) − 50) / 25`
- 배팅/필딩 막대(%) = `20 + 80 × (clamp(평균, 50, 70) − 50) / 20`

평균 75/70이면 이미 최대 막대다. 막대 길이는 선수 능력치 자체의 100점 환산과 다르다.
기존 KBO 개막 투수의 개인 평가 평균은 93.06으로, 원본 게임 개막 투수 평균 약 66.9보다 크게 높았다.
원본은 평가 척도 대조용이며 두 리그의 실제 우열을 의미하지 않는다.
구종의 구위·변화·제구는 비선형 가중치로 결합되고, 여러 변화구가 합산된다.
기존 환산은 여러 구종을 동시에 높게 만들었고, 드물게 던진 구종의 소표본 헛스윙률도 과대 반영했다.
예: 롯데 최준용의 사용률 1.6% 커터에 변화/구위 6을 부여하여 개인 피칭 평가가 129까지 상승했다.
타격 기준 컨택 60, 수비 기본값 52·포구/송구 60도 원본 척도에 비해 높았다.

## 수정

표시 함수와 막대 상한은 수정하지 않았다. 619명 전원의 환산 명세를 재검수했다.
구종 헛스윙률에 120구 사전 표본을 적용하고, 사용률 3% 미만은 구위/변화 상한 2,
10% 미만은 상한 3을 적용했다. 구위와 제구의 기준도 원본 척도에 맞게 조정했다.
컨택 기준 45, 파워 기준 25, 수비 기본값 42를 사용한다. 타격 기록이 없는 선수는
타율 .220/ISO .080 사전분포를 사용하고 추정 표시를 남겼다.
팀별 목표 순위는 지정하지 않았다. 선수 ID·보직·얼굴 연결·구속·구종 구성·개막 명단은 유지했다.
세부 공식은 `tools/recalibrate_team_strength.py`, 개인별 변경 전후는
`build/team_strength/calibration_changes.json`에 있다. 명세 재생성에도 최종 환산을 연결했다.

## 실제 화면 막대 길이 비교

아래는 게임 함수로 계산한 막대 길이 비율(%)이며 화면에 숫자로 표시되는 선수 능력치가 아니다.

| 구단 | 피칭 전 → 후 | 배팅 전 → 후 | 필딩 전 → 후 |
|---|---:|---:|---:|
'''+ '\n'.join(rows)+'''

## 검증과 산출물

- 기존 10개 팀 객체를 원 MIPS 함수로 재생하여 실제 화면에서 읽은 평균과 일치 확인.
- 최종 ISO를 설치 데이터·치트·상태저장·외부 텍스처 없이 새로 실행.
- 실제 10개 팀 선택 화면의 평균과 수정 후보 함수 재생값이 모두 일치.
- 새 페넌트의 기본/시즌 편성에서 619명 능력치·보직·등록명·290명 1군·50명 스태프 연결 대조.
- 최종 10개 화면: `build/team_strength/after/*_after.png`.
- 인수인계 JSON: `roster_data/KBO_2026_전체선수_스태프.json`.
- 설치 데이터 미생성. 검증 후 PPSSPP 종료.

능력치는 공식 게임 등급이 아닌 기록 기반 추정이다. 38명의 구종 구성 미확인, 9명 공용 3D 모델,
일본 슬롯의 통산 기록 잔재는 남아 있다. 이번 검증은 전력 표시와 편성 데이터이며 시즌 완주나
619명 전원의 실제 경기 동작을 검증한 것은 아니다. 기존 진행 중 시즌의 능력치 이행은 미검증이다.
G: 복사는 로컬 파일 해시로 검증하며 Google Drive 서버 동기화 완료를 뜻하지 않는다.

최종 ISO SHA-256: `'''+digest+'`\n'
(ROOT/'TEAM_STRENGTH_REVIEW.md').write_text(text,'utf8')
evidence=dict(iso_sha256=digest,before_iso_sha256='d2bf04d96dae58d3ab2b3295f400dfbbb934db891ca1342bd92c69c2c25c8e1f',tested_at=datetime.datetime.now().astimezone().isoformat(),live_matches_simulation=True,teams=after,display_function_changed=False)
(D/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),'utf8')
print(digest)
