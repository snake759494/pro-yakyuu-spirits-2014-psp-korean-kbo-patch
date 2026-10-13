"""관찰한 외형 검증 화면을 최종 ISO 해시와 연결하고 소스 목록을 갱신한다."""
import json,hashlib,datetime
from pathlib import Path
from inventory import ROOT,ISO
from build import OUT

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 build=json.loads((ROOT/'build/build_report.json').read_text('utf8'))
 validation=json.loads((ROOT/'build/validation.json').read_text('utf8'))
 live=json.loads((ROOT/'build/hanwha_live_records.json').read_text('utf8'))
 assert sha(OUT)==build['sha256']==validation['sha256']==live['iso_sha256']
 assert sha(ISO)==build['original_sha256'] and live['all_roster_fields_match']
 assert 'OK' in (ROOT/'build/hanwha_visual_tests.log').read_text('utf8')
 names=['hanwha_visual_select_home.png','hanwha_visual_select_away.png','hanwha_visual_home_model.png','hanwha_visual_lineup.png','hanwha_visual_ryu_portrait.png','hanwha_visual_away_front.png','hanwha_visual_away_back.png','hanwha_visual_home_back.png']
 screens=[dict(path='build/'+n,sha256=sha(ROOT/'build'/n)) for n in names]
 report=dict(status='한화 영문 등 이름·키/체형·얼굴/메뉴 초상화·홈/원정 유니폼 보완판',
  tested_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
  iso=OUT.name,iso_sha256=build['sha256'],original_sha256=build['original_sha256'],
  runtime_verified=True,complete_game_verified=False,full_season_verified=False,save_reload_verified=False,real_psp_verified=False,
  emulator='PPSSPP 1.17.1',environment='work/emulator/memstick; 최종 ISO 새 부팅; COM 대전; 외부 텍스처 팩/치트/상태 저장 미사용',
  emulator_closed_after_testing=True,screenshots=screens,
  checks=['홈/원정 선택 화면에 한화 유니폼 표시','한화 타순·류현진 상세의 공식 사진 기반 초상화와 E 모자 표시',
   '메인 메뉴 3D 모델의 홈 한화 유니폼과 에르난데스 얼굴 표시',
   '류현진 경기: 회색 원정 유니폼, RYU H.J., 99번, 투구 조작 및 첫 투구 후 화면 확인',
   '에르난데스 경기: 흰색 홈 유니폼, HERNANDEZ, 12번 표시',
   '실행 메모리의 67명 레코드는 ISO와 일치; 동명이인 박준영의 자동 구분 플래그는 게임 동작으로 구별'],
  static_tests=dict(mips_and_texture_tests=12,passed=True,visual_files=94,visual_regions=validation['hanwha_visual_regions_verified'],
   previous_abilities_ids_voices_and_other_rosters_preserved=True,iso_size_lba_preserved=True,install_macs_and_direct_archive_match=validation.get('install_plaintext_matches_direct_archive')),
  live_record_report='build/hanwha_live_records.json',data_scope_report='build/hanwha_visual_data_validation.json',
  limitations=['3D 얼굴 골격·머리카락·기존 피부 재질은 유지하며 공식 사진 기반 얼굴 텍스처와 메뉴 초상화를 적용했다. 정밀 초상 조형 아님.',
   '체형은 공식 키/몸무게를 기존 게임 모델에 대응한 근사치. 개막 당일 신체 측정 기록이 없으면 조사 시점 공식 프로필 사용.',
   '한화 유니폼은 기존 UV에 맞춘 재현으로 모든 스폰서 패치·자수·봉제선을 복제하지 않음. 대체 유니폼은 정적 검증; 게임의 기존 해금 조건 유지.',
   '구장 광고·일부 원 NPB 표기/개인 소개/과거 기록·음성·다른 팀 선수와 유니폼은 이번 작업 범위 밖.',
   '전체 경기 완주, 저장 후 재로드, 시즌 종료·다음 해, PSP 실기는 이번 외형 빌드에서 검증하지 않음.'],
  previous_accepted_roster_evidence='build/baseline_before_hanwha_visual/runtime_validation.json')
 (ROOT/'build/runtime_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
 (ROOT/'SHA256SUMS.txt').write_text(build['original_sha256']+'  '+ISO.name+'\n'+build['sha256']+'  '+OUT.name+'\n','utf8')
 old=json.loads((ROOT/'build/source_hashes.json').read_text('utf8'))
 paths={ROOT/p for p in old if (ROOT/p).is_file()}
 paths.update(ROOT.glob('*.md'));paths.add(ROOT/'requirements.txt')
 paths.update((ROOT/'tools').glob('*.py'));paths.update(p for p in (ROOT/'translation').rglob('*') if p.is_file())
 paths.update([ROOT/'tools/bin/face_detection_yunet_2023mar.onnx',ROOT/'tools/bin/face_detection_yunet_LICENSE'])
 hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
 (ROOT/'build/source_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),'utf8')
 (ROOT/'build/hanwha_visual_build.log').write_text('최종 외형 빌드 완료\nSHA256 '+build['sha256']+'\n전체 빌드 후 외형 허용 영역 재생성. 정적/실행 검증은 validation.json과 runtime_validation.json 참고.\n','utf8')
 print(json.dumps(dict(iso_sha256=build['sha256'],screenshots=len(screens),source_files=len(hashes)),ensure_ascii=False))
if __name__=='__main__':main()
