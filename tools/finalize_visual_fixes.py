"""최종 ISO와 실제 관찰·이전 동일 자원 검증을 구분하여 기록한다."""
import json,datetime
from inventory import ROOT,ISO
from build import OUT,sha

def main():
 def read(p):return json.loads((ROOT/p).read_text('utf8'))
 base=ROOT/'build/visual_fixes'
 build=read('build/build_report.json');static=read('build/validation.json')
 stadium=read('build/face_stadium/stadium_validation.json')
 closed=read('build/visual_fixes/emulator_closed.json')
 incremental=read('build/visual_fixes/incremental_validation.json')
 observed=read('build/visual_fixes/observations.json');digest=sha(OUT)
 assert digest==build['sha256']==static['sha256']==stadium['iso_sha256']==closed['iso_sha256']==incremental['final_iso_sha256']
 assert closed['owned_emulator_running']==0 and stadium['passed']
 assert sha(ISO)==build['original_sha256'] and static['installation_archive_preserved'] and not build['installation_data_patched']
 assert read('build/hanwha_visual_data_validation.json')['previous_abilities_ids_voices_all_other_records_preserved']
 for log in ('tests.log','visual_tests.log'):assert 'OK' in (base/log).read_text('utf8')
 def screens(folder,names):
  return [dict(path=(folder/n).relative_to(ROOT).as_posix(),sha256=sha(folder/n)) for n in names]
 previous=read('build/visual_fixes/before_icon_uv/live_records.json')
 assert previous['iso_sha256']==incremental['previous_iso_sha256'] and previous['all_roster_fields_match']
 report=dict(status='피부색·간판 UV·스윙 판정 문자·한화 경기 로고·빈 등록명 수정',tested_at=datetime.datetime.now().astimezone().isoformat(),iso=OUT.name,iso_sha256=digest,original_sha256=build['original_sha256'],runtime_verified=True,
  emulator='PPSSPP 1.17.1',environment='work/emulator 독립 메모리스틱; 완전 종료 후 새 부팅; 설치/치트/외부 텍스처팩/상태 저장 미사용',emulator_closed_after_testing=True,
  checks=observed['checks'],screenshots=screens(base/'final',observed['screenshots']),
  complete_nine_inning_user_game_verified=False,shortened_com_game_verified=observed['shortened_com_game_verified'],full_season_verified=False,save_reload_verified=False,real_psp_verified=False,
  static_tests=dict(passed=True,regression_tests=26,original_iso_preserved=True,installation_archive_preserved=True,installation_data_rebuilt=False,stadium_geometry_chunks_preserved=stadium['geometry_chunks_preserved'],previous_abilities_ids_voices_other_records_preserved=True),
  previous_same_asset_evidence=dict(iso_sha256=incremental['previous_iso_sha256'],mode='1P COM 대전에서 직접 타격 입력',checks=['타이밍 빠름! 문구 가독성 확인','페라자/강백호 타석 피부색 확인','채은성 타석 HUD 이름 확인','실행 메모리 선수·코치 67명 명단 필드 일치'],screenshots=screens(base/'before_icon_uv',['intro_09.png','atbat_0.png','kang_face.png','swing_3.png','chae_intro2.png']),difference_from_final='한화 경기 소형 로고 4개 파일의 UV 크기만 최종 보정; 나머지 빌드 영역 일치 검사 통과',comparison='build/visual_fixes/incremental_validation.json',live_records='build/visual_fixes/before_icon_uv/live_records.json'),
  limitations=['느림/약간 문구는 원본 UV와 정적 텍스처로 검증했으며 이번 직접 입력에서 모든 판정 조합을 실제 발생시키지는 못했다.','채은성 기존 등록명 선택값은 원본 MIPS 함수 실행으로 검사했다. 사용자 기존 페넌트 저장을 재로드한 검증은 아니다. 오래된 시스템/페넌트 저장은 피부 등 이전 선수 설정을 담을 수 있다.','모든 로고 연출·카메라·선수·조명 조합을 전수 확인하지 않았다.','원본 3D 얼굴형과 64×64 얼굴 텍스처를 이용한 보정이며 대전 구장은 마쓰다 기반 근사 모델이다. 다른 팀 선수/유니폼, 일본어 음성, 포스트시즌 등 이전 잔여 범위는 유지된다.'],
  previous_report='build/baseline_before_visual_fixes/runtime_validation.json')
 (ROOT/'build/runtime_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
 (ROOT/'SHA256SUMS.txt').write_text(build['original_sha256']+'  '+ISO.name+'\n'+digest+'  '+OUT.name+'\n','utf8')
 old=read('build/source_hashes.json');paths={ROOT/p for p in old if (ROOT/p).is_file()}
 paths.update(ROOT.glob('*.md'));paths.add(ROOT/'requirements.txt');paths.update((ROOT/'tools').glob('*.py'));paths.update(p for p in (ROOT/'translation').rglob('*') if p.is_file())
 hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
 (ROOT/'build/source_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),'utf8')
 (base/'build.log').write_text('전체 빌드 후 한화 소형 로고 UV 보정. 설치 데이터 원본 보존.\n최종 SHA256 '+digest+'\n정적 검사, 원본 보존, 에뮬레이터 종료 확인.\n','utf8')
 print(json.dumps(dict(sha256=digest,screenshots=len(report['screenshots']),source_files=len(hashes),emulator_closed=True),ensure_ascii=False))
if __name__=='__main__':main()
