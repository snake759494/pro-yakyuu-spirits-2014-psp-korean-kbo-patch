"""KBO의 2026 소속선수·코칭스태프 XLSX를 구조화한다."""
import json, re
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'work/kbo_roster_research/2026_kbo_club_roster.xlsx'
OUT = ROOT / 'work/kbo_roster_research/2026_kbo_club_roster.json'
TEAM_CODES = {
    'LG 트윈스':'LG', '한화 이글스':'HH', 'SSG 랜더스':'SK',
    '삼성 라이온즈':'SS', 'NC 다이노스':'NC', 'KT 위즈':'KT',
    '롯데 자이언츠':'LT', 'KIA 타이거즈':'HT', '두산 베어스':'OB',
    '키움히어로즈':'WO',
}
POSITIONS = {'투수':'P','포수':'C','내야수':'IF','외야수':'OF'}

def parse():
    wb=load_workbook(SRC,data_only=True)
    result={}
    for ws in wb.worksheets:
        rows=list(ws.iter_rows(values_only=True))
        starts=[]
        for i,row in enumerate(rows):
            title=row[3] if len(row)>3 else None
            if isinstance(title,str) and title.strip() in TEAM_CODES:
                starts.append((i,TEAM_CODES[title.strip()],title.strip()))
        for j,(start,code,title) in enumerate(starts):
            stop=starts[j+1][0] if j+1<len(starts) else len(rows)
            players=[];staff=[]
            # The right-hand block has no explicit label for its first group.
            # Its category differs by worksheet layout: teams whose first label is
            # catcher list pitchers first, while teams whose first label is infield
            # list catchers first. Kiwoom starts with the outfield label, so its
            # preceding right block is the infield group.
            first_right_heading=next((row[6].strip() for row in rows[start+1:stop]
                if len(row)>6 and isinstance(row[6],str) and row[6].strip() in POSITIONS),None)
            initial_right={'포수':'P','내야수':'C','외야수':'IF','투수':'P'}.get(first_right_heading,'P')
            category={0:'P',3:'P',6:initial_right}
            summary=rows[start][6] or ''
            coach_match=re.search(r'감독\s*(\d+)\s*,\s*코치\s*(\d+)\s*,\s*선수\s*(\d+)',summary)
            expected_staff=(int(coach_match.group(1))+int(coach_match.group(2))) if coach_match else 0
            staff_rows=[]
            for row in rows[start+1:stop]:
                row=list(row)+[None]*max(0,9-len(row))
                staff_name=row[1]
                if isinstance(staff_name,str) and staff_name.strip():
                    note=row[2].strip() if isinstance(row[2],str) else ''
                    role=row[0].strip() if isinstance(row[0],str) else ''
                    name=staff_name.strip()
                    if name in ('성명',):continue
                    staff_rows.append(dict(name=name,role=role or '코치',note=note))
            staff=staff_rows[:expected_staff]
            # KBO's workbook sometimes stores a manager's former playing position
            # (for example "투수") in the position column. In each club sheet the
            # declared staff block starts with the manager, then lists coaches.
            for si, item in enumerate(staff):
                item['role'] = '감독' if si == 0 else '코치'
            staff_names={x['name'] for x in staff}
            # A few club sheets continue the coaching list into the first player column.
            # Fill the declared count from the leading untyped names there, preserving the
            # workbook's row order. The remaining cells are the complete player roster.
            spill_staff=[]
            first_pitcher_row=next((ri for ri,row in enumerate(rows[start+1:stop]) if row[3]=='투수'),None)
            if len(staff)<expected_staff:
                for ri,row in enumerate(rows[start+1:stop]):
                    row=list(row)+[None]*max(0,9-len(row))
                    if first_pitcher_row is not None and ri>=first_pitcher_row:break
                    name=row[4].strip() if isinstance(row[4],str) else ''
                    if name=='성명':continue
                    if name and name not in staff_names:
                        spill_staff.append(dict(name=name,role='코치',note=(row[5] or '').strip() if isinstance(row[5],str) else ''))
                        staff_names.add(name)
                        if len(staff)+len(spill_staff)>=expected_staff:break
            staff.extend(spill_staff)
            needed_staff=set(x['name'] for x in staff)
            for ri,row in enumerate(rows[start+1:stop]):
                row=list(row)+[None]*max(0,9-len(row))
                for col in (0,3,6):
                    kind=row[col].strip() if isinstance(row[col],str) else ''
                    value=row[col+1].strip() if isinstance(row[col+1],str) else ''
                    if kind in POSITIONS:category[col]=POSITIONS[kind]
                    elif kind in ('감독','코치'): category[col]=None
                    if col==0 and value in needed_staff:continue
                    if col==3 and value in needed_staff:continue
                    if value and category[col] and value not in ('성명',):
                        note=row[col+2].strip() if isinstance(row[col+2],str) else ''
                        players.append(dict(name=value,category=category[col],note=note,source_column=col))
            # Staff names can appear in the first column even when the sheet uses a
            # position word (e.g. "투수") as the person's role; remove them by identity.
            players=[p for p in players if p['name'] not in needed_staff]
            # Honor KBO's declared roster size if the sheet uses overlapping position
            # labels or a duplicated display row. Every retained name is still sourced.
            expected_players=int(coach_match.group(3)) if coach_match else len(players)
            if len(players)>expected_players:
                # Ambiguous extra entries occur only before an explicit position label;
                # remove them from the tail of the first column, which is the overflow.
                overflow=len(players)-expected_players
                for i in range(len(players)-1,-1,-1):
                    if overflow and players[i].get('source_column')==0:
                        players.pop(i);overflow-=1
                if overflow:
                    raise ValueError(f'{code}: {overflow} roster entries exceed the official declared count; refusing to truncate')
            if len(players)!=expected_players:
                raise ValueError(f'{code}: parsed {len(players)} players, official declared count is {expected_players}')
            for p in players:p.pop('source_column',None)
            # Store the officially announced counts so later tooling can audit gaps.
            result[code]=dict(code=code,official_team=title,players=players,staff=staff,
                              declared_players=expected_players,declared_staff=expected_staff)
    assert len(result)==10, (len(result),result.keys())
    for code,spec in result.items():
        print(code,len(spec['players']),'players',len(spec['staff']),'staff entries (declared',spec['declared_staff'],')')
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    return result

if __name__=='__main__':parse()
