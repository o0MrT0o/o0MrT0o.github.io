import requests,subprocess,pathlib,json
p=pathlib.Path('yellowstone_2024');p.mkdir(exist_ok=True)
url='https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/video/2024_Jul_24_Hydrothermal_Explosion_Biscuit_Basin.mp4'
dest=p/'full.mp4'
with requests.get(url,stream=True,timeout=120) as r:
 r.raise_for_status()
 with open(dest,'wb') as f:
  for b in r.iter_content(1<<20):f.write(b)
print('DOWNLOADED',dest.stat().st_size,flush=True)
pr=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height,avg_frame_rate:format=duration','-of','json',str(dest)],capture_output=True,text=True)
(p/'probe.json').write_text(pr.stdout);print('PROBE',pr.stdout,flush=True)
from PIL import Image,ImageDraw
frames=[]
for t in list(range(3,175,9)):
 out=p/f'f_{t:03d}.jpg'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(dest),'-frames:v','1','-vf','scale=430:-2',str(out)],check=True)
 frames.append((t,Image.open(out).convert('RGB')))
canvas=Image.new('RGB',(430*4,275*5),'#111')
d=ImageDraw.Draw(canvas)
for i,(t,im) in enumerate(frames):
 x=(i%4)*430;y=(i//4)*275
 canvas.paste(im,(x,y))
 d.rectangle((x,y+242,x+430,y+275),fill='#101010')
 d.text((x+7,y+251),f'2024 - {t}s',fill='white')
canvas.save(p/'contact.jpg',quality=85)
