"""LG 능력/외형 최종 빌드에 실제 관찰한 실행 증거만 연결한다."""
from finalize_lg_rebuild import ROOT,sha,read,write
from pathlib import Path
import json
def main():
 iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso';original=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00).iso';digest=sha(iso)
 audit=read('build/lg_rebuild/live_roster_audit.json');assert audit['passed'] and audit['iso_sha256']==digest
 assert read('build/validation.json')['sha256']==digest
 user=Path(r'D:\psp\ppsspp_win\memstick\PSP\SAVEDATA\NPJH50838SS\SYSTEM.DAT');assert sha(user)=='b51eca56ba29d9d0d8e5656148a1f1bb1446784110c7ffcc6491b0388b71d88e'
 shots=sorted((ROOT/'build/lg_rebuild').glob('details_*.png'));assert len(shots)>=4
 r=dict(status='LG 능력·신체·등 이름·등번호 및 새 페넌트 실제 데이터 검증 통과',tested_at='2026-10-11',iso=iso.name,iso_sha256=digest,original_sha256=sha(original),runtime_verified=True,runtime_scope='사용자 SYSTEM.DAT 복사본으로 새 페넌트 편성, 선수 정보 및 LG 68명 런타임 데이터 감사',emulator='work/emulator PPSSPP 1.17.1',user_system_sha256=sha(user),user_system_original_modified=False,user_system_copy_used=True,savestate_used_for_final_validation=False,memory_modified_for_final_validation=False,cheats=False,external_texture_pack=False,installation_data_rebuilt=False,tests=dict(count=10,passed=True),static_validation='build/validation.json',live_audit='build/lg_rebuild/live_roster_audit.json',evidence_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in shots},checks=['LG 선수63/스태프5 실제 포인터와 이름·투타 분류','투수13/야수15 및 외국인4명 1군 유지','68명 등 이름·번호·키·체형 런타임 값,63명 기본 능력값','치리노스/웰스 메뉴 얼굴과 선수 연결 재검증'],limitations=['공식 기록은 2025 이전만 사용. 구속 상한·구종·수비·어깨·신인 능력은 편집 추정값.','원본 전용 얼굴61명 사진 텍스처. 공용 모델7명의 경기 중 전용 실사 얼굴 모델은 미구현.','원본 모델의 두상·기하·투타 폼·음성은 유지한다.','군보류 박명근·박관우의 미부여 등번호는0. 일부 신체 정보는 현재 공식 프로필이므로 개막일과 다를 수 있다.','1군28명 제한 및 외국인 전원1군 요청에 맞춘 편성으로 실제29명 개막 등록과 다르다.','모든 선수의 경기 중 외형을 하나씩 관찰하거나 시즌 완주·진행 중 페넌트 변환·실제PSP 검증을 하지 않았다.'])
 write('build/runtime_validation.json',r)
 text=f"{r['original_sha256']}  {original.name}\n{digest}  {iso.name}\n"
 for path in ('SHA256SUMS.txt','build/SHA256SUMS.txt'):(ROOT/path).write_text(text,'utf8')
 paths=set((ROOT/'tools').glob('*.py'))|set((ROOT/'translation').rglob('*.json'))|set((ROOT/'translation/lg_2026').glob('*.png'))
 paths.update(ROOT/p for p in ('LG_REBUILD.md','LG_DETAILS.md','SHA256SUMS.txt','work/lg_rebuild/official_roster.xlsx'))
 write('build/source_hashes.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)})
 print(json.dumps(dict(sha256=digest,evidence=len(shots)),ensure_ascii=False))
if __name__=='__main__':main()
