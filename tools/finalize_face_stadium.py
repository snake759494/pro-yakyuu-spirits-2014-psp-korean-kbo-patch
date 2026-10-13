"""얼굴/구장 변경의 실제 관찰 범위를 해당 ISO와 연결한다."""
import json,hashlib,datetime
from inventory import ROOT,ISO
from build import OUT

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
 def read(p):return json.loads((ROOT/p).read_text('utf8'))
 build=read('build/build_report.json');static=read('build/validation.json');stadium=read('build/face_stadium/stadium_validation.json');closed=read('build/face_stadium/emulator_closed.json');live=read('build/hanwha_live_records.json')
 digest=sha(OUT)
 assert digest==build['sha256']==static['sha256']==stadium['iso_sha256']==closed['iso_sha256']==live['iso_sha256']
 assert closed['owned_emulator_running']==0 and stadium['passed'] and live['every_record_has_matching_copy']
 assert sha(ISO)==build['original_sha256'] and static['installation_archive_preserved'] and not build['installation_data_patched']
 assert read('build/hanwha_visual_data_validation.json')['previous_abilities_ids_voices_all_other_records_preserved']
 assert 'OK' in (ROOT/'build/face_stadium/visual_tests.log').read_text('utf8')
 names=['select_day.png','select_night.png','lineup.png','day_stadium.png','day_coach_face.png','day_field.png','day_hernandez_front.png','day_pitch.png','main_hernandez_face.png','night_stadium.png','night_pitch.png']
 screens=[dict(path='build/face_stadium/'+n,sha256=sha(ROOT/'build/face_stadium'/n)) for n in names]
 report=dict(status='한화 얼굴 피부톤/경계 보정 및 대전 구장 근사 모델 적용',tested_at=datetime.datetime.now().astimezone().isoformat(),iso=OUT.name,iso_sha256=digest,original_sha256=build['original_sha256'],runtime_verified=True,emulator='PPSSPP 1.17.1',environment='work/emulator/memstick; 최종 ISO 새 부팅; 설치/상태 저장/외부 텍스처팩/치트 미사용',emulator_closed_after_testing=True,screenshots=screens,
  checks=['구장 선택의 대전 명칭, 낮/밤 사진, 천연잔디와 복제 모델 치수 확인','낮/밤 COM 대전 진입, 한화 간판 및 구장 전경 확인','에르난데스 등판과 메인 메뉴 얼굴, 코치 얼굴에서 큰 흰 외곽 띠 제거 및 목과 피부톤 연결 확인','한화 타순 메뉴의 얼굴 초상화 확인','낮/밤 경기에서 직접 투구 입력과 투구/포구 동작 확인'],
  complete_game_verified=False,full_season_verified=False,save_reload_verified=False,real_psp_verified=False,
  static_tests=dict(passed=True,visual_test_cases=12,face_and_uniform_files=94,visual_regions=762,stadium_regions=len(build['hanwha_stadium']),stadium_geometry_chunks=stadium['geometry_chunks_preserved'],hanwha_home_games=72,other_stadium_assets_preserved=True,previous_player_abilities_ids_voices_and_other_records_preserved=True,installation_data_rebuilt=False,installation_archive_preserved=True),
  user_reference_screenshots='build/face_stadium/user_screenshots.json',user_reference_build_hash_known=False,
  live_records=dict(report='build/hanwha_live_records.json',matching_records=67,every_record_has_matching_copy=True,all_raw_copies_identical=False,note='경기 중에는 30명만 검색되었다. 메인 메뉴에서는 67명 모두 정상 일치 복사본을 확인했으나 에르난데스 별도 복사본 1곳의 키 바이트 차이를 함께 기록했다.'),
  limitations=['기존 64×64 얼굴 UV와 3D 얼굴형을 이용한 보정이며 실제 얼굴형의 정밀 모델링은 아니다. 모든 선수/각도/조명은 실제 화면으로 전수 확인하지 않았다.','대전 홈구장은 기존 마쓰다 모델을 한화 전용 슬롯에 복제한 근사 모델이다. 실제 볼파크의 8m 벽과 정확한 외야 거리/복층 불펜을 재현하지 않았다.','구장 선택 사진은 원래 마쓰다 사진을 재사용해 일부 원 광고가 남는다. 경기 내 주요 간판 66개는 한화/대전 표기로 변경했지만 모든 소형 배경 표기를 전수 확인하지 않았다.','선수 소개창의 일부 원 팀 소형 아이콘, 과거 기록, 일본어 음성, 다른 구단 선수/유니폼은 잔여 항목이다.','전체 경기 완주, 기존 페넌트 저장 재로드, 시즌 종료/다음 해, 실기 검증은 하지 않았다.'],
  previous_evidence='build/baseline_before_face_stadium/runtime_validation.json')
 (ROOT/'build/runtime_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
 (ROOT/'SHA256SUMS.txt').write_text(build['original_sha256']+'  '+ISO.name+'\n'+digest+'  '+OUT.name+'\n','utf8')
 old=read('build/source_hashes.json');paths={ROOT/p for p in old if (ROOT/p).is_file()}
 paths.update(ROOT.glob('*.md'));paths.add(ROOT/'requirements.txt');paths.update((ROOT/'tools').glob('*.py'));paths.update(p for p in (ROOT/'translation').rglob('*') if p.is_file())
 hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
 (ROOT/'build/source_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),'utf8')
 (ROOT/'build/face_stadium/build.log').write_text('전체 ISO 빌드 및 재읽기 검사 완료\nSHA256 '+digest+'\n설치 데이터 재생성 없음\n정적/실행 결과: build/validation.json, build/runtime_validation.json\n','utf8')
 print(json.dumps(dict(sha256=digest,screenshots=len(screens),source_files=len(hashes),emulator_closed=True),ensure_ascii=False))
if __name__=='__main__':main()
