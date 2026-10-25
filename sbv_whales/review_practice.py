from pathlib import Path
import requests,subprocess,io,math,json
from PIL import Image,ImageDraw
p=Path('practice_footage');p.mkdir(exist_ok=True)
url="https://ndownloader.figshare.com/files/60552604"
with requests.get(url,timeout=140,stream=True) as r:
 print('GET',r.status_code,r.headers.get('Content-Length'),flush=True);r.raise_for_status()
 with (p/'practice.mp4').open('wb') as f:
  for chunk in r.iter_content(1024*1024):f.write(chunk)
f=p/'practice.mp4'
q=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate:format=duration','-of','json',str(f)],capture_output=True,text=True)
print('FFPROBE',q.stdout,flush=True)
j=json.loads(q.stdout)
duration=float(j['format']['duration']);num=32
c=Image.new('RGB',(320*4,210*8),'#101010');d=ImageDraw.Draw(c)
for i in range(num):
 t=(duration-0.8)*i/(num-1)
 x=subprocess.run(['ffmpeg','-loglevel','error','-ss',f'{t:.3f}','-i',str(f),'-frames:v','1','-vf','scale=320:-2','-f','image2pipe','-vcodec','mjpeg','pipe:1'],capture_output=True)
 if x.returncode!=0 or not x.stdout:continue
 im=Image.open(io.BytesIO(x.stdout)).convert('RGB');im.thumbnail((320,180))
 ix=(i%4)*320;iy=(i//4)*210;c.paste(im,(ix,iy))
 d.text((ix+8,iy+184),f'{t:.1f}s',fill='white')
c.save(p/'contact.jpg',quality=83)
(p/'meta.json').write_text(json.dumps({'duration':duration,'ffprobe':j}))
