#!/usr/bin/env python3
import requests,re,json,subprocess,time,html,os
from pathlib import Path
from PIL import Image,ImageDraw
D=Path('new_ecballium_probe');D.mkdir(exist_ok=True)
s=requests.Session();s.headers.update({'User-Agent':'Mozilla/5.0'})
page='https://www.nature.com/articles/s44383-025-00003-7'
urls=[]
try:
 r=s.get(page,timeout=35)
 print('ARTICLE',r.status_code,len(r.content),r.url,flush=True)
 (D/'nature-page-links.txt').write_text('\n'.join(sorted(set(re.findall(r'(?:https?://[^\"<>\s]+|\S+)\\.avi(?:\\?[^\"<>\s]*)?',r.text,re.I))))[:60000])
 for term in ['.avi','Supplementary Movie-1','MOESM','springer','mediaobjects']:
  print('SEARCH',term,[r.text[max(0,m.start()-170):m.start()+220] for m in list(re.finditer(re.escape(term),r.text,re.I))[:6]],flush=True)
 for raw in re.findall(r'(?:href|src)=[\'"]([^\'"]+)[\'"]',r.text):
  x=html.unescape(raw)
  if '.avi' in x.lower() or 'MOESM' in x:urls.append(x)
except Exception as e:print('ARTICLE ERR',repr(e),flush=True)
urls.extend([
'https://static-content.springer.com/esm/art%3A10.1038%2Fs44383-025-00003-7/MediaObjects/44383_2025_3_MOESM2_ESM.avi',
'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs44383-025-00003-7/MediaObjects/44383_2025_3_MOESM2_ESM.avi',
'https://static-content.springer.com/esm/art%3A10.1038%2Fs44383-025-00003-7/MediaObjects/44383_2025_3_MOESM1_ESM.avi',
'https://static-content.springer.com/esm/art%3A10.1038%2Fs44383-025-00003-7/MediaObjects/44383_2025_4_MOESM2_ESM.avi'
])
results=[]
def probe(path):
 q=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,timeout=60)
 if q.returncode:return {'error':q.stderr[-300:]}
 j=json.loads(q.stdout);v=next((a for a in j['streams'] if a['codec_type']=='video'),None)
 return {'duration':j['format'].get('duration'),'v':{'w':v['width'],'h':v['height'],'codec':v['codec_name']} if v else None}
for url in dict.fromkeys(urls):
 if url.startswith('/'):url='https://www.nature.com'+url
 if not url.startswith('https://'):continue
 try:
  rr=s.get(url,timeout=85,stream=True,headers={'Referer':page})
  print('GET',rr.status_code,rr.headers.get('Content-Length'),rr.headers.get('Content-Type'),url[:150],flush=True)
  if rr.status_code!=200 or any(x in rr.headers.get('Content-Type','') for x in ['html','text']):continue
  size=int(rr.headers.get('Content-Length') or 0)
  if size>160000000:continue
  name=D/'gorges_2025_sup_video.avi'
  count=0
  with open(name,'wb') as f:
   for chunk in rr.iter_content(1048576):
    if chunk:
     count+=len(chunk)
     if count>160000000:raise RuntimeError('Too large')
     f.write(chunk)
  if count<100000:continue
  met=probe(name);print('VIDEO METADATA',met,flush=True)
  if met.get('v'):
   results.append({'url':url,'bytes':count,'probe':met})
   frames=[.08,.22,.4,.6,.8,.95]
   dur=float(met['duration'])
   canvas=Image.new('RGB',(3*360,2*670),'#101010');draw=ImageDraw.Draw(canvas)
   for i,portion in enumerate(frames):
    t=min(.98*dur,max(.03,dur*portion))
    file=D/f'frame_{i}.jpg'
    z=subprocess.run(['ffmpeg','-hide_banner','-v','error','-y','-ss',str(t),'-i',str(name),'-frames:v','1',str(file)],capture_output=True,text=True)
    if z.returncode or not file.exists():continue
    with Image.open(file) as im:
     im.thumbnail((350,610));x=(i%3)*360+(360-im.width)//2;y=(i//3)*670
     canvas.paste(im,(x,y));draw.text(((i%3)*360+10,y+620),f'{t:.2f}s',fill='white')
   canvas.save(D/'GORGES_2025_STILLS.jpg')
   break
 except Exception as e:print('SOURCE FAILED',repr(e),flush=True)
(D/'SOURCE_PROBE.json').write_text(json.dumps(results,indent=2))
print('FINISH',results,flush=True)
