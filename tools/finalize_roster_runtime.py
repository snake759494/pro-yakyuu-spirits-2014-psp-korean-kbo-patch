"""2026-10-11 새 페넌트 로스터 실기 증거와 최종 ISO를 연결한다."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text('utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 audit=read('build/roster_diagnosis/live_roster_audit.json')
 iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
 digest=sha(iso);assert digest==audit['iso_sha256'] and audit['passed']
 evidence={}
 for p in (ROOT/'build/roster_diagnosis').glob('final_*.png'):
  evidence[p.relative_to(ROOT).as_posix()]=sha(p)
 report=dict(status='새 페넌트 10개 팀의 1군 화면 및 619명/50명 실행 데이터 검증 통과',
  tested_at='2026-10-11',iso=iso.name,iso_sha256=digest,
  original_sha256='d58bb782f027e0889e47c145462b2c694433c856fcbf2411ce5d186a40521e5f',
  runtime_verified=True,runtime_scope='새 페넌트 팀 편성 및 등록 분류',
  emulator='독립 work/emulator PPSSPP 1.17.1, ISO 직접 읽기, 콜드 부팅',
  savestate_used_for_final_validation=False,cheats=False,external_texture_pack=False,
  memory_modified_for_final_validation=False,installation_data_rebuilt=False,
  user_state_diagnosis='사용자가 남긴 슬롯1 복사본과 스크린샷으로 원인 분석. 원본 저장은 수정하지 않음.',
  static_validation='build/validation.json',static_validation_passed=True,
  tests={'unittest_count':6,'passed':True,'name_records':669,'registration_variants_per_record':6},
  live_audit='build/roster_diagnosis/live_roster_audit.json',
  checks=['10개 팀 1군 편성 화면을 직접 확인하고 촬영',
   '619명 소속·주 포지션·이름·1군 구분을 초기화된 실제 RAM과 대조',
   '50명 감독/코치의 실제 팀 구조체 슬롯·이름·선수 슬롯과 분리 확인',
   '한화 스태프 안내 화면의 김경문 감독·양상문 투수코치·김민호 타격코치 표시 확인',
   'NC 투수·야수 등록의 2군 목록 스크롤 확인',
   '최종 ISO의 수정된 MIPS 등록명 함수를 669명×6개 선택자로 실행: 빈 이름 없음'],
  evidence_sha256=evidence,
  limitations=['한화 기존 62명 명단은 공식 2월 64명과 구성 차이가 남아 있다. 단순 2명 누락만은 아니다.',
   '게임 한 팀 1군은 28명(투수12/야수16), 스태프는 감독1/코치4 슬롯을 사용한다.',
   '기본 선발/타순은 게임용 구성이다. 3월28일 실제 선발 명단 또는 당일 등록29명과 동일하지 않다.',
   '예비 내야수/외야수는 공식 IF/OF 그룹에 맞췄으며 세부 주 수비 위치는 일부 기본값이다.',
   '일부 팀의 편성 미리보기는 비DH 타순을 표시한다. 종전 정규시즌 DH 코드는 유지했다.',
   '9개 비한화 구단의 스태프 화면 전체와 모든 2군 이름을 화면으로 전수 촬영하지는 않았다. 실제 RAM은 전수 검사했다.',
   '경기 출전·시즌 완주·새 저장/불러오기·실제 PSP는 이번 실행 검증 범위 밖이다.'])
 write('build/runtime_validation.json',report)
 hashes=f"{report['original_sha256']}  Pro Yakyuu Spirits 2014 (Japan) (v2.00).iso\n{digest}  {iso.name}\n"
 for p in ['SHA256SUMS.txt','build/SHA256SUMS.txt']:(ROOT/p).write_text(hashes,'utf8')
 old=read('build/source_hashes.json');paths={ROOT/p for p in old if (ROOT/p).is_file()}
 paths.update((ROOT/'tools').glob('*.py'));paths.update((ROOT/'translation').rglob('*.json'))
 paths.update(ROOT/p for p in ['KBO_2026_TEAMS.md','ROSTER_RUNTIME_FIX.md','SHA256SUMS.txt'])
 write('build/source_hashes.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)})
 print(json.dumps({'sha256':digest,'evidence':len(evidence),'runtime':True},ensure_ascii=False))
if __name__=='__main__':main()
