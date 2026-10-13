"""2026 시즌 종료 기준 입력 재생성 순서(수집 결과 사용, 네트워크 없음)."""
import subprocess,sys
from pathlib import Path
T=Path(__file__).resolve().parent
for args in (['plan_season_end_2026.py'],['apply_season_end_2026.py'],['derive_layout_2026.py'],['prepare_ratings_review.py'],['prepare_identity_faces.py'],['apply_season_end_2026.py','sync']):
 print('>>',*args,flush=True);subprocess.run([sys.executable,'-X','utf8',str(T/args[0]),*args[1:]],cwd=T,check=True)
