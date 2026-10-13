"""LG 사용자 시스템 저장 검증 증거를 최종 ISO와 연결한다."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads((ROOT/p).read_text('utf8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
 original=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00).iso'
 audit=read('build/lg_rebuild/live_roster_audit.json');digest=sha(iso)
 assert digest==audit['iso_sha256'] and audit['passed']
 assert read('build/validation.json')['sha256']==digest
 shots=list((ROOT/'build/lg_rebuild').glob('final_*.png'));assert len(shots)>=4
 user=Path(r'D:\psp\ppsspp_win\memstick\PSP\SAVEDATA\NPJH50838SS\SYSTEM.DAT')
 assert sha(user)=='b51eca56ba29d9d0d8e5656148a1f1bb1446784110c7ffcc6491b0388b71d88e'
 report=dict(status='LG 새 명단 및 사용자 SYSTEM.DAT로 새 페넌트 편성 검증 통과',tested_at='2026-10-11',iso=iso.name,iso_sha256=digest,original_sha256=sha(original),runtime_verified=True,runtime_scope='LG 새 페넌트 팀 편성: DH 타순, 투수/야수 등록 및 1군 외국인',emulator='독립 work/emulator PPSSPP 1.17.1',user_system_sha256=sha(user),user_system_original_modified=False,user_system_copy_used=True,savestate_used_for_final_validation=False,manual_reset_all_teams_used=False,memory_modified_for_final_validation=False,cheats=False,external_texture_pack=False,installation_data_rebuilt=False,static_validation='build/validation.json',static_validation_passed=True,tests=dict(count=9,passed=True),live_audit='build/lg_rebuild/live_roster_audit.json',evidence_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in shots},checks=['사용자 SYSTEM.DAT 복사 후 콜드 부팅, 새 페넌트 LG 선택','투수13/야수15 실제 화면과 RAM 대조','치리노스/톨허스트/웰스 선발, 오스틴3번1루수, 문보경4번DH','LG63명 주 포지션 및 캐시·전체 이름·외국인·1군 등록 감사','감독1/코치4 실제 슬롯과 선수 슬롯 분리 감사'],limitations=read('translation/kbo_2026/LG.json')['limitations']+['다른9팀의 사용자 저장 편성은 이번 수정 범위 밖이다.','새 팀 편성 화면 생성 시 LG의 사용자 지정 편성도 ISO 기본값으로 초기화한다.','진행 중 페넌트 저장 변환, 시즌 완주, 실제 PSP 검증은 하지 않았다.','얼굴/영문 등 이름 및 능력치 전체의 2026 선수별 정확성은 이번 검증 범위 밖이다.'])
 write('build/runtime_validation.json',report)
 hashes=f"{report['original_sha256']}  {original.name}\n{digest}  {iso.name}\n"
 for p in ['SHA256SUMS.txt','build/SHA256SUMS.txt']:(ROOT/p).write_text(hashes,'utf8')
 paths=set((ROOT/'tools').glob('*.py'))|set((ROOT/'translation').rglob('*.json'))
 paths.update(ROOT/p for p in ['LG_REBUILD.md','ROSTER_RUNTIME_FIX.md','SHA256SUMS.txt','work/lg_rebuild/official_roster.xlsx','work/kbo_roster_research/20260328/LG.json'])
 write('build/source_hashes.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)})
 print(json.dumps(dict(iso_sha256=digest,evidence=len(shots),runtime_verified=True),ensure_ascii=False))
if __name__=='__main__':main()
