#!/usr/bin/env python3
"""Forensic motion-source probe for nine PNAS supplementary high-speed MP4 movies."""
from pathlib import Path
import requests,zipfile,shutil,json,subprocess,re,math,os
from PIL import Image, ImageDraw, ImageFont
D=Path('electric_nematode_originals');D.mkdir(exist_ok=True)
O=Path('electric_nematode_probe');O.mkdir(exist_ok=True)
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; educational research integrity audit)'})
URL='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12557510/supplementaryFiles'
p=D/'PNAS_2503555122_supplementary.zip'
with S.get(URL,timeout=170,stream=True) as r:
 print('ZIP HTTP',r.status_code,r.headers.get('content-type'),r.headers.get('content-length'),flush=True);r.raise_for_status()
 with open(p,'wb') as f:
  for b in r.iter_content(1024*1024):
   if b:f.write(b)
print('Downloaded zip',p.stat().st_size,flush=True)
with zipfile.ZipFile(p) as z:
 contents=[(i.filename,i.file_size) for i in z.infolist()]
 print('FILES',json.dumps(contents,indent=2),flush=True)
 for i in z.infolist():
  if Path(i.filename).suffix.lower() in ('.mp4','.avi','.mov','.m4v') and i.file_size<60_000_000:
   dst=D/Path(i.filename).name
   with z.open(i) as src,open(dst,'wb') as out:shutil.copyfileobj(src,out)
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
