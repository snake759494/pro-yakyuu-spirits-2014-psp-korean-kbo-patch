"""직접 번역한 도움말 문장 조각을 원래 색상/버튼 태그와 재결합한다."""
import json,re
from inventory import ROOT
from ui_textures import original_chunks
from analyze import strings

def main():
    segments=json.loads((ROOT/'translation/help_segments.json').read_text('utf8'))
    p=ROOT/'translation/new_ui.json';mapping=json.loads(p.read_text('utf8'));count=0
    existing=json.loads((ROOT/'translation/reference_matches.json').read_text('utf8'))
    for line in (ROOT/'translation/new_ui.txt').read_text('utf-8-sig').splitlines():
        if '|' in line:
            k,v=line.split('|',1);existing[k]=v
    existing.update(json.loads((ROOT/'translation/script_direct.json').read_text('utf8')))
    existing.update(mapping)
    for fn in ('GPTEXT.CHK','NTMAIN.CHK'):
        for _,source in strings(original_chunks(fn)['HELP']):
            if source in existing:
                mapping[source]=existing[source];continue
            parts=re.split(r'(<[^>]+>)',source)
            for i,text in enumerate(parts):
                if i%2 or not re.search('[ぁ-ヿ一-鿿]',text):continue
                key=text.strip();assert key in segments,(fn,key)
                left=len(text)-len(text.lstrip());right=len(text.rstrip())
                parts[i]=text[:left]+segments[key]+text[right:]
            translated=''.join(parts)
            assert re.findall(r'<[^>]+>',source)==re.findall(r'<[^>]+>',translated)
            assert re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',source)==re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',translated),(source,translated)
            assert not re.search('[ぁ-ヿ一-鿿]',translated),(source,translated)
            mapping[source]=translated;count+=1
    p.write_text(json.dumps(mapping,ensure_ascii=False,indent=2),'utf8');print(count,'도움말 문자열 반영')
if __name__=='__main__':main()
