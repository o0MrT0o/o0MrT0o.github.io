#!/usr/bin/env python3
"""Recover the original licensed 8K source, transcode to a high-quality 4K archival source."""
from pathlib import Path
import requests,subprocess,json,time
p=Path('flame_hires');p.mkdir(exist_ok=True)
f='Burning_Eternal_Flame_Falls_Chestnut_Ridge_Park_NY_2025-09.webm'
b='https://upload.wikimedia.org/wikipedia/commons/'
urls=[b+'transcoded/b/b6/'+f+'/'+f+'.2160p.vp9.webm',b+'b/b6/'+f]
s=requests.Session();s.headers.update({'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36','Referer':'https://commons.wikimedia.org/wiki/File:'+f})
def probe(x):
 r=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height','-show_entries','format=duration,size','-of','json',str(x)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-800:])
 return json.loads(r.stdout)
source=None
for i,u in enumerate(urls):
 dst=p/('wikimedia_2160p.webm' if i==0 else 'wikimedia_original_8k.webm')
 for trial in range(2):
  try:
   with s.get(u,stream=True,timeout=120) as r:
    print('SOURCE',i,'HTTP',r.status_code,'CONTENT_LENGTH',r.headers.get('content-length'),'CONTENT_TYPE',r.headers.get('content-type'),flush=True)
    if r.status_code>=400:r.raise_for_status()
    with open(dst,'wb') as f2:
     n=0
     for piece in r.iter_content(1024*1024):
      if piece:n+=len(piece);f2.write(piece)
    print('COMPLETED',n,'bytes',flush=True)
   if dst.stat().st_size<10000000:raise RuntimeError('File too small to be actual source')
   source=dst;break
  except Exception as e:
   print('FAIL',repr(e)[:300],flush=True);dst.unlink(missing_ok=True);time.sleep(2)
 if source:break
if source is None:raise RuntimeError('No 4K/8K source retrievable')
out=p/'SBV_ETERNAL_FLAME_ORIGINAL_HIRES_4K.mp4'
print('TRANSCODE_BEGIN',str(source),flush=True)
cmd=['ffmpeg','-hide_banner','-loglevel','error','-stats','-y','-threads','4','-i',str(source),'-vf','scale=3840:2160:flags=lanczos,fps=30','-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
r=subprocess.run(cmd)
if r.returncode:raise RuntimeError('4K transcode failed')
print('READY_4K',out.stat().st_size,json.dumps(probe(out)),flush=True)
(p/'SOURCE_CREDIT.txt').write_text('G. Edward Johnson, Eternal Flame Falls, 5 and 9 September 2025, CC BY 4.0, https://commons.wikimedia.org/wiki/File:Burning_Eternal_Flame_Falls_Chestnut_Ridge_Park_NY_2025-09.webm. This file is transcoded to 4K from the author original.\n')
