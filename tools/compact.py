"""고정 폭 이름을 글자 누락 없이 표시하는 공유 복합 글리프 분할."""
from collections import Counter
from functools import lru_cache

def split_phrases(phrases):
    counts=Counter()
    for phrase in phrases:
        for n in (2,3):
            counts.update(phrase[i:i+n] for i in range(len(phrase)-n+1))
    result={}
    for phrase,cells in phrases.items():
        @lru_cache(None)
        def solve(pos,left):
            if pos==len(phrase):return (0,()) if left>=0 else None
            if left<=0:return None
            best=None
            for n in (1,2,3):
                if pos+n>len(phrase):continue
                tail=solve(pos+n,left-1)
                if tail is None:continue
                token=phrase[pos:pos+n]
                # 3글자 압축은 2글자로 수용할 수 없을 때만 선택한다.
                cost=(0 if n==1 else 20/counts[token])+(100 if n==3 else 0)+tail[0]
                candidate=(cost,(token,)+tail[1])
                if best is None or candidate[0]<best[0]:best=candidate
            return best
        answer=solve(0,cells)
        if answer is None:raise ValueError((phrase,cells))
        result[phrase]=answer[1]
    return result
