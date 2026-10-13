"""추가 8개 구단의 실제 관찰 기록을 최종 ISO와 연결한다."""
from finalize_lg_rebuild import ROOT,sha,read,write
from pathlib import Path
import subprocess,json,html

def main():
 iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
 original=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00).iso'
 digest=sha(iso);codes=['SS','HT','WO','KT','LT','OB','SK','NC']
 assert read('build/validation.json')['sha256']==digest
 static=read('build/club_brand/static_validation.json')
 assert static['passed'] and static['iso_sha256']==digest
 audit_path='build/club_brand/live_SS_HT_WO_KT_LT_OB_SK_NC_LG.json'
 audit=read(audit_path);assert audit['passed'] and audit['iso_sha256']==digest
 observations=read('build/club_brand/observations.json')
 assert observations['iso_sha256']==digest and set(observations['teams'])==set(codes)
 assert all(observations['teams'][c]['reviewed'] for c in codes)
 assert not any(observations['teams'][c].get('pending') for c in codes)
 shots=sorted((ROOT/'build/club_brand/final').glob('*.png'))
 for c in codes:
  for suffix in ('uniform_select','stadium_select','intro','home','away','field'):
   assert (ROOT/f'build/club_brand/final/{c}_{suffix}.png').exists(),(c,suffix)
 closed=subprocess.run(['powershell','-NoProfile','-Command',"if (Get-Process PPSSPPWindows64 -ErrorAction SilentlyContinue) { exit 1 }"],capture_output=True).returncode==0
 assert closed,'검증 에뮬레이터 종료 필요'
 user=Path(r'D:\psp\ppsspp_win\memstick\PSP\SAVEDATA\NPJH50838SS\SYSTEM.DAT')
 assert sha(user)=='b51eca56ba29d9d0d8e5656148a1f1bb1446784110c7ffcc6491b0388b71d88e'
 r=dict(status='추가 8개 구단 외형 및 새 페넌트 명단 연결 검증 완료',tested_at='2026-10-12',iso=iso.name,iso_sha256=digest,original_sha256=sha(original),runtime_verified=True,runtime_scope=observations,emulator='독립 work/emulator PPSSPP 1.17.1',emulator_closed=True,user_system_copy_used=True,user_system_original_modified=False,user_system_sha256=sha(user),savestate_used_for_final_validation=False,memory_modified_for_final_validation=False,cheats=False,external_texture_pack=False,installation_data_rebuilt=False,tests=dict(count=10,passed=True),static_validation='build/validation.json',brand_static_validation='build/club_brand/static_validation.json',live_audit=audit_path,players_audited=audit['players'],staff_audited=audit['staff'],evidence_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in shots},limitations=[
  '이번 작업은 구단 외형·지역·구장·로고·약칭 확장이다. 추가 8개 구단 선수 개별 얼굴/체형/등 영문명/능력치를 새로 제작하지 않았다.',
  '명단 검증은 저장된 패치 데이터와 실제 새 페넌트 포인터·보직·등록 상태의 일치 검사다. 2026 공식 선수 정보 전체를 다시 검수한 것은 아니다.',
  '기존 대전 저장 편성은 남을 수 있다. 검증은 R 초기 멤버로 ISO 기본 명단을 사용했다. 대전 DH 설정은 별도로 확인해야 한다.',
  '실제 KBO 구장 형상이 아닌 유사 원본 모델이다. 모델 치수·충돌을 보존했으며 선택 사진은 해당 원본 모델이다.',
  '두산/NC 구장 복제로 사용하지 않는 원 도쿄/삿포로 자원을 재활용했다. KBO 홈 외 일본 구장 슬롯의 독립성은 보장하지 않는다.',
  'SSG 야간 LIGHTS는 복사했으나 공간 제한으로 밤 전용 조명 번짐 텍스처는 제외했다. 야간 선택과 실제 로딩을 확인했으며 전체 조명 변화는 미검증이다.',
  '유니폼 기본 색·가슴/모자/소매 표장을 적용했다. 실제 모든 스폰서/기념/특별 유니폼의 완전한 복제는 아니다.',
  '일부 일본 광고, 원본 바지 줄무늬, 일본 음성/배경/특별 유니폼 명칭은 남아 있다.',
  '경기 도입과 1회초 화면까지 확인했다. 경기/시즌 완주, 기존 페넌트 저장 변환, 모든 카메라와 실제 PSP는 검증하지 않았다.'
 ])
 copy=ROOT/'build/club_brand/g_drive_copy.json'
 if copy.exists():
  g=read(copy.relative_to(ROOT));assert g['sha256']==digest and g['verified'];r['g_drive_copy']=g
 write('build/runtime_validation.json',r)
 names={'SS':'삼성','HT':'KIA','WO':'키움','KT':'KT','LT':'롯데','OB':'두산','SK':'SSG','NC':'NC'}
 sections=[]
 for c in codes:
  figures=''.join(f'<figure><a href="final/{c}_{s}.png"><img loading="lazy" src="final/{c}_{s}.png"></a><figcaption>{label}</figcaption></figure>' for s,label in [('uniform_select','유니폼 선택'),('stadium_select','구장 선택'),('intro','경기 도입'),('home','홈 유니폼'),('away','원정 유니폼'),('field','1회초 화면')])
  sections.append(f'<section><h2>{names[c]}</h2><div class="grid">{figures}</div></section>')
 page='<!doctype html><html lang="ko"><meta charset="utf-8"><title>KBO 8구단 검증</title><style>body{background:#14191f;color:#eee;font:16px sans-serif;max-width:1500px;margin:30px auto;padding:20px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}figure{margin:0}img{width:100%}figcaption{padding:8px}code{overflow-wrap:anywhere}li{margin:10px 0}</style><h1>KBO 추가 8개 구단 검증 화면</h1>'
 page+=f'<p>ISO SHA-256: <code>{digest}</code></p><p>새 페넌트: 선수 {audit["players"]}명, 스태프 {audit["staff"]}명 연결 대조 통과. 경기 도입과 1회초 외형 확인이며 완주 검증은 아닙니다.</p>'
 page+='<details><summary>적용 범위와 남은 제한</summary><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in r['limitations'])+'</ul></details>'
 page+=''.join(sections)+'</html>'
 (ROOT/'build/club_brand/review.html').write_text(page,'utf8')
 progress=read('translation/club_brand_progress.json')
 progress.update(working_iso_sha256=digest,g_drive_updated='g_drive_copy' in r,note='구단별 경기 화면 및 새 페넌트 명단 연결 검사 완료. 한계는 runtime_validation.json 참고.')
 for c in codes:progress['teams'][c]['status']='구단별 화면 확인 및 정적/새 페넌트 연결 검사 통과'
 write('translation/club_brand_progress.json',progress)
 hashes=f"{r['original_sha256']}  {original.name}\n{digest}  {iso.name}\n"
 for p in ('SHA256SUMS.txt','build/SHA256SUMS.txt'):(ROOT/p).write_text(hashes,'utf8')
 paths=set((ROOT/'tools').glob('*.py'))|set((ROOT/'translation').rglob('*.json'))|set((ROOT/'translation').rglob('*.png'))
 paths.update(ROOT/p for p in ('KBO_TEAM_PATCH_RULES.md','KBO_CLUB_BRANDING.md','AGENTS.md','SHA256SUMS.txt'))
 write('build/source_hashes.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)})
 print(json.dumps(dict(sha256=digest,evidence=len(shots),emulator_closed=closed,g_drive_updated='g_drive_copy' in r),ensure_ascii=False))
if __name__=='__main__':main()
