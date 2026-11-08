#!/usr/bin/env python3
"""Forensic motion-source probe for nine PNAS supplementary high-speed MP4 movies."""
from pathlib import Path
import requests,zipfile,shutil,json,subprocess,re,math,os
from PIL import Image, ImageDraw, ImageFont
D=Path('electric_nematode_originals');D.mkdir(exist_ok=True)
O=Path('electric_nematode_probe');O.mkdir(exist_ok=True)
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; educational research integrity audit)'})
# PMC retired legacy OA service in August 2026.
# The officially supported unsigned S3 Cloud Service holds individual original supplementary files.
import xml.etree.ElementTree as ET
base='https://pmc-oa-opendata.s3.amazonaws.com'
art='PMC12557510.1'
r=S.get(base+'/',params={'list-type':'2','prefix':art+'/'},timeout=35)
print('S3_LIST',r.status_code,r.url,r.text[:1800],flush=True);r.raise_for_status()
root=ET.fromstring(r.text)
keys=[x.text for x in root.iter() if x.tag.rsplit('}',1)[-1]=='Key' and x.text]
print('S3_KEYS',keys,flush=True)
metadata_url=f'{base}/{art}/{art}.json'
m=S.get(metadata_url,timeout=35)
print('S3_METADATA',m.status_code,m.text[:1500],flush=True)
if m.status_code==200:
 obj=m.json()
 print('S3_LICENSE',obj.get('license_code'),'MEDIA_URLS',len(obj.get('media_urls') or []),flush=True)
 media_urls=obj.get('media_urls') or []
else:media_urls=[]
contents=[]
for n in ['01','02','03','04','07','08']:
 name=f'pnas.2503555122.sm{n}.mp4'
 matches=[x for x in media_urls if name in x]
 if not matches:matches=[base+'/'+key for key in keys if key.endswith('/'+name)]
 if not matches:
  print('NO_S3_MATCH',name,flush=True);continue
 u=matches[0]
 try:
  with S.get(u,timeout=90,stream=True) as response:
   print('S3_VIDEO_GET',name,response.status_code,response.headers.get('content-type'),response.headers.get('content-length'),flush=True)
   response.raise_for_status()
   dst=D/name
   size=0
   with open(dst,'wb') as f:
    for chunk in response.iter_content(1024*1024):
     if chunk:
      size+=len(chunk)
      if size>40_000_000:raise RuntimeError('movie over cap')
      f.write(chunk)
  if size<200000:raise RuntimeError('not real MP4')
  contents.append((name,size));print('S3_OK',name,size,flush=True)
 except Exception as exc:print('S3_FILE_ERROR',name,repr(exc),flush=True)
print('RETRIEVED',contents,flush=True)
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
