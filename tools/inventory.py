from pathlib import Path
import json,struct,hashlib,pycdlib
ROOT=Path(__file__).resolve().parents[1]
ISO=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00).iso'
WORK=ROOT/'work'
def main():
 iso=pycdlib.PyCdlib();iso.open(str(ISO)); files=[]
 for root,dirs,names in iso.walk(iso_path='/'):
  for name in names:
   path=root.rstrip('/')+'/'+name;r=iso.get_record(iso_path=path)
   files.append(dict(name=path,offset=r.extent_location()*2048,size=r.data_length))
 iso.close();entries=[]
 with ISO.open('rb') as f:
  base=next(e for e in files if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
  f.seek(base['offset']);h=f.read(22);assert h[:4]==b'BDSV'
  sector,start,count=struct.unpack_from('<3I',h,10);assert sector==2048
  table=f.read(count*268)
  for i in range(count):
   name=table[i*268:i*268+256].split(b'\0')[0].decode('ascii');lba,size,capacity=struct.unpack_from('<3I',table,i*268+256)
   assert lba>=start and size<=capacity and lba*sector+capacity<=base['size'],(i,name,lba,size,capacity)
   e=dict(index=i,name=name,offset=base['offset']+lba*sector,size=size,capacity=capacity);entries.append(e)
   if any(s in name for s in ('FONT','MENU','PLAYER','TEXT')):
    out=WORK/'assets'/name;out.parent.mkdir(parents=True,exist_ok=True);f.seek(e['offset']);out.write_bytes(f.read(size))
  for e in files:
   if e['name'].endswith('.elf') or e['name'] in ['/PSP_GAME/SYSDIR/EBOOT.BIN','/PSP_GAME/PARAM.SFO']:
    out=WORK/'iso'/e['name'].lstrip('/');out.parent.mkdir(parents=True,exist_ok=True);f.seek(e['offset']);out.write_bytes(f.read(e['size']))
 (WORK/'inventory.json').write_text(json.dumps(dict(iso=files,fbd=entries),ensure_ascii=False,indent=2),encoding='utf-8')
 print('ISO files:',len(files),'BDSV entries:',len(entries));print([(e['name'],e['size']) for e in entries if 'FONT' in e['name']])
 with ISO.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 (ROOT/'build/original.json').write_text(json.dumps(dict(file=ISO.name,size=ISO.stat().st_size,sha256=sha),indent=2),encoding='utf-8')
 print('SHA256',sha)
if __name__=='__main__': main()
