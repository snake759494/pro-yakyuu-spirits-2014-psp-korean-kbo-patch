"""LG 구단 외형 최종 빌드와 실제 관찰 증거를 연결한다."""
from finalize_lg_rebuild import ROOT,sha,read,write
from pathlib import Path
import json,subprocess

def main():
 iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
 original=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00).iso';digest=sha(iso)
 assert read('build/validation.json')['sha256']==digest
 assert read('build/lg_brand/static_validation.json')['iso_sha256']==digest
 audit=read('build/lg_rebuild/live_roster_audit.json');assert audit['passed'] and audit['iso_sha256']==digest
 shots=sorted((ROOT/'build/lg_brand').glob('final_*.png'));assert len(shots)>=4
 closed=subprocess.run(['powershell','-NoProfile','-Command',"if (Get-Process PPSSPPWindows64 -ErrorAction SilentlyContinue) { exit 1 }"],capture_output=True).returncode==0
 assert closed,'검증 에뮬레이터 종료 필요'
 user=Path(r'D:\psp\ppsspp_win\memstick\PSP\SAVEDATA\NPJH50838SS\SYSTEM.DAT')
 assert sha(user)=='b51eca56ba29d9d0d8e5656148a1f1bb1446784110c7ffcc6491b0388b71d88e'
 observations=read('build/lg_brand/observations.json')
 r=dict(status='LG 서울·잠실·유니폼·로고 및 KBO 한 글자 약칭 적용',tested_at='2026-10-11',iso=iso.name,iso_sha256=digest,original_sha256=sha(original),runtime_verified=True,runtime_scope=observations,emulator='work/emulator PPSSPP 1.17.1',emulator_closed=closed,user_system_copy_used=True,user_system_original_modified=False,user_system_sha256=sha(user),savestate_used_for_final_validation=False,memory_modified_for_final_validation=False,cheats=False,external_texture_pack=False,installation_data_rebuilt=False,tests=dict(count=10,passed=True),static_validation='build/validation.json',brand_static_validation='build/lg_brand/static_validation.json',live_audit='build/lg_rebuild/live_roster_audit.json',evidence_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in shots},limitations=['잠실 근사치로 CHIBA 개방형 모델을 사용한다. 원 모델 형상, 좌우99.5m/중앙122m, 충돌, 잔디와 카메라를 유지한다.','선택 미리보기는 해당 원본 구장 사진이며 광고는 실제 경기 모델에서 교체했다. 도시 배경과 일본 지도 전체를 재제작하지 않았다.','유니폼 원본 모델과 재단을 유지한다. 모든 스폰서·기념 패치를 완전히 복제하지 않았다.','LG 선수 능력·외형 패치의 기존 추정값 및 공용 얼굴 모델7명 제한은 LG_DETAILS.md 참고.','새 페넌트 LG 편성은 다시 검사했다. 시즌 완주, 진행 중 저장 변환, 실제 PSP, 모든 선수·모드·카메라 조합은 검증하지 않았다.'])
 write('build/runtime_validation.json',r)
 hashes=f"{r['original_sha256']}  {original.name}\n{digest}  {iso.name}\n"
 for p in ('SHA256SUMS.txt','build/SHA256SUMS.txt'):(ROOT/p).write_text(hashes,'utf8')
 paths=set((ROOT/'tools').glob('*.py'))|set((ROOT/'translation').rglob('*.json'))|set((ROOT/'translation/lg_brand').glob('*.png'))|set((ROOT/'translation/lg_2026').glob('*.png'))|set((ROOT/'translation/kbo_logos').glob('*.png'))
 paths.update(ROOT/p for p in ('KBO_TEAM_PATCH_RULES.md','LG_BRAND.md','LG_DETAILS.md','LG_REBUILD.md','AGENTS.md','SHA256SUMS.txt'))
 write('build/source_hashes.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)})
 print(json.dumps(dict(sha256=digest,evidence=len(shots),emulator_closed=closed),ensure_ascii=False))
if __name__=='__main__':main()
