"""2026 KBO 전체 소속 선수단을 기존 게임의 선수/감독 슬롯에 연결한다."""
import json, re, struct
from pathlib import Path
from collections import Counter
from analyze import chunks
from player_fields import get
from kbo_roster_slots import STAFF_SLOTS, KBO_ROLE_COACHES

ROOT=Path(__file__).resolve().parents[1]
FULL=ROOT/'work/kbo_roster_research/2026_kbo_club_roster.json'
OUT=ROOT/'translation/kbo_2026'
TEAM_IDS={'LG':0,'SS':1,'HT':2,'WO':3,'KT':4,'LT':5,'HH':6,'OB':7,'SK':8,'NC':9}
ROSTER_URL='https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11831'
POSITION_ORDER={'P':0,'C':1,'IF':2,'OF':3}

def norm(s):return re.sub(r'\s+','',s).replace('（','(').replace('）',')')

def main():
    full=json.loads(FULL.read_text('utf8'))
    # Active first-team bios/stats were collected from KBO's dated register pages.
    old={c:json.loads((OUT/f'{c}.json').read_text('utf8')) for c in TEAM_IDS}
    for code,teamid in TEAM_IDS.items():
        if code=='HH':continue
        base=old[code]
        byname={norm(p['name']):p for p in base['records'] if p['kind']=='player'}
        registered=[p for p in base['records'] if p['kind']=='player' and p.get('player_id')]
        roster=[dict(p) for p in full[code]['players']]
        # March 28 official active entries supersede one same-position preseason slot
        # when a newly registered regular is absent from the Feb 10 roster document.
        names={norm(p['name']) for p in roster}
        additions=[]
        for p in registered:
            if norm(p['name']) in names:continue
            additions.append(p)
        replaced=[]
        for incoming in additions:
            cat=incoming['category']
            candidate=next((i for i in range(len(roster)-1,-1,-1)
              if roster[i]['category']==cat and norm(roster[i]['name']) not in {norm(x['name']) for x in registered}
              and i not in replaced),None)
            if candidate is None:continue
            roster[candidate]=dict(name=incoming['name'],category=cat,note='2026-03-28 1군 등록 명단 반영')
            replaced.append(candidate);names.add(norm(incoming['name']))
        # Five personnel rows: manager, pitching, batting, infield, outfield/running.
        # Match responsibilities, not the order in the official staff spreadsheet.
        staff=full[code]['staff']
        manager=next((x for x in staff if x['role']=='감독'),None)
        assert manager is not None,(code,'official roster has no manager')
        chosen=[manager]+[next(x for x in staff if norm(x['name'])==norm(name)) for name in KBO_ROLE_COACHES[code]]
        pd={n:b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes())}['PDN']
        all_indices=[i for i in range(len(pd)//192) if pd[i*192+90]&63==teamid]
        manager_index,coach_only_indices=STAFF_SLOTS[code]
        coach_indices=[manager_index,*coach_only_indices]
        assert len(coach_indices)==5 and len(set(coach_indices))==5
        assert all(i in all_indices for i in coach_indices),(code,teamid,coach_indices,all_indices)
        player_indices=[i for i in all_indices if i not in coach_indices]
        need=max(0,len(roster)+len(coach_indices)-len(all_indices))
        all_shared=[i for i in range(len(pd)//192) if pd[i*192+90]&63==31]
        borrowed=all_shared[-need:] if need else []
        player_indices.extend(borrowed)
        assert len(roster)<=len(player_indices),(code,len(roster),len(player_indices))
        # Position groups are stable in the official KBO sheet; keep its ordering within
        # each group so the game lineup editor opens with sensible roster sections.
        roster.sort(key=lambda p:POSITION_ORDER[p['category']])
        records=[]
        for i,p in zip(player_indices,roster):
            prior=byname.get(norm(p['name']))
            rec=dict(index=i,name=p['name'],kind='player',category=p['category'],source='KBO 2026 official roster')
            if i in borrowed:rec['borrowed']=True
            if prior:
                rec.update({k:v for k,v in prior.items() if k not in ('index','name','kind','category','opening_entry')})
            rec['index']=i;rec['name']=p['name'];rec['kind']='player';rec['category']=p['category']
            rec['roster_source_note']=p.get('note','')
            records.append(rec)
        for slot,item in zip(coach_indices,chosen):
            role='감독' if slot==manager_index else '코치'
            rec=dict(index=slot,name=item['name'],kind='coach',role=role,source='KBO 2026 official roster')
            records.append(rec)
        # A few remaining Japanese-only records exceed KBO's registered player count.
        # The build layer will release them to the game's common free-agent pool.
        selected={r['index'] for r in records}
        vacant=[i for i in all_indices if i not in selected]
        spec=dict(team_id=teamid,code=code,name=base['name'],cutoff='2026-03-28',
          full_roster_date='2026-02-10',full_roster_source=ROSTER_URL,
          active_roster_source='https://www.koreabaseball.com/Player/Register.aspx',
          registered_players=len(roster),official_declared_players=full[code]['declared_players'],
          official_staff_count=full[code]['declared_staff'],applied_staff_slots=len(chosen),
          all_official_staff=staff,assigned_players=len(roster),assigned_staff=len(chosen),
          manager_index=manager_index,coach_indices=coach_indices,coach_only_indices=list(coach_only_indices),
          vacated_indices=vacant,borrowed_indices=borrowed,records=records,
          source_file='work/kbo_roster_research/2026_kbo_club_roster.json',
          limitations=['공식 2026-02-10 소속선수 명단과 2026-03-28 1군 등록 명단을 통합했다. 신분/등록 변경 선수는 개막 1군 등록을 우선했다.',
            '게임 구단별 스태프 슬롯은 감독 1명과 코치 4명이다. 감독 ID와 코치 ID는 원본 게임의 일본인 역할 레코드에 고정해 적용한다. 전체 KBO 등록 코칭스태프는 이 JSON에 보존했다.',
            '2군 선수의 공개 게임 능력치·생년월일·키·투타 상세가 없는 경우 한글 이름과 포지션만 교체하고 나머지 원 레코드 값은 유지한다.'])
        (OUT/f'{code}.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),'utf8')
        print(code,'players',len(roster),'staff slots',len(chosen),'full staff source',len(staff),'added opening',len(additions),'vacated',len(vacant),'coaches',coach_indices)

if __name__=='__main__':main()
