import requests,hashlib,time
from pathlib import Path
from PIL import Image,ImageDraw
D=Path('flame_frame_test');D.mkdir(exist_ok=True)
name='Burning_Eternal_Flame_Falls_Chestnut_Ridge_Park_NY_2025-09.webm'
b='https://commons.wikimedia.org/wiki/Special:Redirect/file/'+name
paths=[
 b+'?width=1280&thumbtime=1',
 b+'?width=1280&thumbtime=3',
 b+'?width=1280&thumbtime=5',
 b+'?width=1280&thumbtime=8',
 b+'?width=1280&thumbtime=11',
 b+'?width=1280&thumbtime=14',
 b+'?width=1280&start=1',
 b+'?width=1280&start=8',
 b+'?width=1280&thumbtime=00:00:02',
 b+'?width=1280&thumbtime=00:00:10',
 b+'?width=1280',
]
canvas=Image.new('RGB',(4*350,3*245),'#0f1012');dr=ImageDraw.Draw(canvas)
for i,u in enumerate(paths):
 try:
  r=requests.get(u,timeout=35,headers={'User-Agent':'StrangeButVerified/1.0 (video source licensing review)'})
  fp=D/f'frame_{i}.jpg'
  fp.write_bytes(r.content)
  print('FETCH',i,r.status_code,r.headers.get('content-type'),len(r.content),hashlib.md5(r.content).hexdigest(),r.url[:150],flush=True)
  if r.status_code!=200 or not r.headers.get('content-type','').startswith('image/'):continue
  im=Image.open(fp).convert('RGB')
  print('IMAGE',i,im.size,flush=True)
  im.thumbnail((340,213));x=(i%4)*350;y=(i//4)*245
  canvas.paste(im,(x+(350-im.width)//2,y));dr.text((x+6,y+219),f'{i}: '+u.split('?')[-1],fill='white')
 except Exception as e:print('ERROR',i,repr(e)[:140],flush=True)
 time.sleep(.3)
canvas.save(D/'FRAME_TIME_TEST.jpg')
