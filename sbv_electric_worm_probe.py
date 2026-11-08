#!/usr/bin/env python3
"""Forensic motion-source probe for nine PNAS supplementary high-speed MP4 movies."""
from pathlib import Path
import requests,zipfile,shutil,json,subprocess,re,math,os
from PIL import Image, ImageDraw, ImageFont
D=Path('electric_nematode_originals');D.mkdir(exist_ok=True)
O=Path('electric_nematode_probe');O.mkdir(exist_ok=True)
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; educational research integrity audit)'})
# Try publisher-hosted and PMC-hosted direct supplementary MP4s.
# Europe PMC does not supply the supplementary ZIP for this recent PNAS article (NoSuchKey).
contents=[]
base='pnas.2503555122.sm'
ids=['01','02','03','04','07','08']
templates=[
 'https://www.pnas.org/doi/suppl/10.1073/pnas.2503555122/suppl_file/{file}',
 'https://pmc.ncbi.nlm.nih.gov/articles/instance/12557510/bin/{file}',
 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12557510/bin/{file}',
 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12557510/bin/{file}',
 'https://cdn.ncbi.nlm.nih.gov/pmc/articles/PMC12557510/bin/{file}',
]
# Observe availability and HTTP content type using tiny range requests before downloading full file.
valid=[]
for n in ids:
 name=f'{base}{n}.mp4'
 dest=D/name
 for template in templates:
  u=template.format(file=name)
  try:
   response=S.get(u,headers={'Range':'bytes=0-65535','Referer':'https://www.pnas.org/'},timeout=18,stream=True,allow_redirects=True)
   typ=response.headers.get('content-type','')
   size=int(response.headers.get('content-length') or 0)
   print('CHECK',n,response.status_code,typ,size,response.url[:130],flush=True)
   if response.status_code not in [200,206] or not any(x in typ for x in ('video/','octet-stream','application/mp4')):response.close();continue
   response.close()
   with S.get(u,timeout=110,stream=True,headers={'Referer':'https://www.pnas.org/'}) as rr:
    rr.raise_for_status()
    with open(dest,'wb') as f:
     total=0
     for b in rr.iter_content(1024*1024):
      if b:
       total+=len(b);f.write(b)
       if total>55000000:raise RuntimeError('over size limit')
   print('DOWNLOADED',name,dest.stat().st_size,flush=True)
   if dest.stat().st_size>100000:valid.append(name);break
  except Exception as e:
   print('FAILED',name,type(e).__name__,str(e)[:180],flush=True)
   dest.unlink(missing_ok=True)
print('RETRIEVED',valid,flush=True)
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
