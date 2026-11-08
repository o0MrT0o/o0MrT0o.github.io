#!/usr/bin/env python3
"""Forensic motion-source probe for nine PNAS supplementary high-speed MP4 movies."""
from pathlib import Path
import requests,zipfile,shutil,json,subprocess,re,math,os
from PIL import Image, ImageDraw, ImageFont
D=Path('electric_nematode_originals');D.mkdir(exist_ok=True)
O=Path('electric_nematode_probe');O.mkdir(exist_ok=True)
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; educational research integrity audit)'})
# PMC open-access package endpoint is authoritative and avoids web-player anti-bot layers.
import tarfile,xml.etree.ElementTree as ET
contents=[]
OA='https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12557510'
try:
 oa=S.get(OA,timeout=30);print('OA_RESPONSE',oa.status_code,oa.url,oa.text[:1800],flush=True)
 roots=ET.fromstring(oa.text)
 archive_links=[a.attrib.get('href','') for a in roots.iter() if a.tag=='link' and a.attrib.get('format') in ('tgz','tar.gz')]
 print('OA_ARCHIVES',archive_links,flush=True)
 for link in archive_links[:2]:
  u=link.replace('ftp://ftp.ncbi.nlm.nih.gov/','https://ftp.ncbi.nlm.nih.gov/')
  dst=D/'open_access_package.tar.gz'
  with S.get(u,timeout=160,stream=True) as res:
   print('OA_TAR',res.status_code,res.headers.get('content-type'),res.headers.get('content-length'),flush=True)
   res.raise_for_status()
   with open(dst,'wb') as f:
    n=0
    for b in res.iter_content(1024*1024):
     if b:
      f.write(b);n+=len(b)
      if n>350000000:raise RuntimeError('OA package larger than 350MB')
  with tarfile.open(dst,'r:gz') as z:
   contents=[(x.name,x.size) for x in z.getmembers()]
   print('OA_TAR_LIST',json.dumps(contents[:90]),flush=True)
   for mem in z.getmembers():
    if mem.isfile() and mem.name.lower().endswith(('.mp4','.avi','.mov')) and mem.size<60_000_000:
     with z.extractfile(mem) as inp,open(D/Path(mem.name).name,'wb') as out:shutil.copyfileobj(inp,out)
except Exception as e:
 print('OA_ERROR',type(e).__name__,repr(e)[:850],flush=True)

# As an independent fallback, some authors share movies on Zenodo.
try:
 zen=S.get('https://zenodo.org/api/records/17203860',timeout=25)
 print('ZENODO',zen.status_code,zen.text[:1800],flush=True)
 if zen.status_code==200:
  z=zen.json()
  print('ZEN_FILES',[(f.get('key'),f.get('size'),f.get('links',{}).get('self')) for f in z.get('files',[])][:35],flush=True)
except Exception as e:print('ZEN_ERROR',repr(e)[:400],flush=True)

# Last resort: publisher's individual supplementary original MP4s.
if not any(p.suffix.lower()=='.mp4' for p in D.iterdir()):
 for n in ['01','02','03','04','07','08']:
  name=f'pnas.2503555122.sm{n}.mp4'
  urls=[
   f'https://www.pnas.org/doi/suppl/10.1073/pnas.2503555122/suppl_file/{name}',
   f'https://pmc.ncbi.nlm.nih.gov/articles/instance/12557510/bin/{name}',
  ]
  for u in urls:
   try:
    with S.get(u,timeout=12,stream=True) as res:
     print('DIRECT',n,res.status_code,res.headers.get('content-type'),flush=True)
     if res.status_code!=200 or not any(x in res.headers.get('content-type','').lower() for x in ['video','octet-stream']):continue
     dest=D/name
     with open(dest,'wb') as f:
      for b in res.iter_content(1024*1024):
       if b:f.write(b)
     break
   except Exception as e:print('DIRECT ERROR',repr(e)[:150],flush=True)
def ff(cmd):
 o=subprocess.run(cmd,capture_output=True,text=True)
 if o.returncode:raise RuntimeError(' '.join(map(str,cmd[:7]))+'\n'+o.stderr[-800:])
 return o.stdout
results=[]
for f in sorted(D.iterdir()):
 if f.suffix.lower() not in ['.mp4','.mov','.avi']:continue
 try:
  j=json.loads(ff(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]))
  vid=next(x for x in j['streams'] if x['codec_type']=='video')
  duration=float(j['format']['duration'])
  meta={'file':f.name,'bytes':f.stat().st_size,'width':vid['width'],'height':vid['height'],'fps':vid.get('avg_frame_rate'),
        'codec':vid.get('codec_name'),'duration':duration,'frames':vid.get('nb_frames')}
  output=Image.new('RGB',(4*280,3*230),'#151922');draw=ImageDraw.Draw(output)
  ts=[(i+.25)/12*duration for i in range(12)]
  for k,t in enumerate(ts):
   frame=O/f'{f.stem}_frame_{k:02d}.jpg'
   try:
    ff(['ffmpeg','-v','error','-y','-ss',f'{t:.3f}','-i',str(f),'-frames:v','1',str(frame)])
    with Image.open(frame) as im:
     im.thumbnail((275,204))
     x=(k%4)*280;y=(k//4)*230
     output.paste(im,(x+(280-im.width)//2,y))
     draw.text((x+6,y+207),f'{t:.1f}s',fill='white')
   except Exception as e:print('FRAME ERR',f.name,k,repr(e)[:150],flush=True)
  output.save(O/f'{f.stem}_CONTACT.jpg',quality=85)
  results.append(meta);print('SOURCE',meta,flush=True)
 except Exception as e:print('PROBE ERR',f.name,repr(e),flush=True)
(O/'SOURCE_PROBE.json').write_text(json.dumps({'article':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12557510/','media_files':results,'zip_files':contents},indent=2))
if len(results)<4:raise RuntimeError(f'Insufficient original scientific video material {len(results)}')
print('MEDIA_VERIFIED',len(results),'distinct source videos',flush=True)
