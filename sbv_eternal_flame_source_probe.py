from pathlib import Path
import requests,subprocess,json
from PIL import Image,ImageDraw
D=Path('eternal_flame_source');D.mkdir(exist_ok=True)
O=Path('eternal_flame_probe');O.mkdir(exist_ok=True)
import urllib.parse,os,time
filename='Burning_Eternal_Flame_Falls_Chestnut_Ridge_Park_NY_2025-09.webm'
base='https://upload.wikimedia.org/wikipedia/commons/transcoded/b/b6/'+filename+'/'+filename+'.'
urls=[
 base+'1080p.vp9.webm',
 base+'720p.vp9.webm',
 'https://commons.wikimedia.org/wiki/Special:Redirect/file/'+filename+'?width=1920',
 'https://commons.wikimedia.org/wiki/Special:FilePath/'+filename+'?width=1280',
 'https://upload.wikimedia.org/wikipedia/commons/b/b6/'+filename,
 base+'480p.vp9.webm',
 'https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/'+urllib.parse.quote(filename)+'&width=1280',
 base+'360p.vp9.webm',
]
try:
 api=requests.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','titles':'File:'+filename,'prop':'videoinfo','viprop':'derivatives|url','format':'json'},timeout=18,headers={'User-Agent':'StrangeButVerifiedCreator/1.0 (educational)'})
 print('COMMONS_API',api.status_code,api.text[:1200],flush=True)
except Exception as e:print('API_FAILED',repr(e),flush=True)
def sh(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-500:])
 return p.stdout
src=D/'FlameFallsCCBY.webm'
for url in urls:
 time.sleep(.2)
 try:
  with requests.get(url,timeout=50,stream=True,headers={'User-Agent':'StrangeButVerified/1.0 (educational media review)'}) as r:
   print('GET',r.status_code,r.headers.get('Content-Type'),r.headers.get('Content-Length'),url,flush=True)
   r.raise_for_status()
   size=0
   with open(src,'wb') as f:
    for b in r.iter_content(1048576):
     if b:
      size+=len(b)
      if size>80_000_000:raise RuntimeError('Too large for 80MB source audit')
      f.write(b)
  if size>500000:break
 except Exception as e:print('FAIL',type(e).__name__,str(e)[:180],flush=True);src.unlink(missing_ok=True)
else:raise RuntimeError('No usable transcode')
j=json.loads(sh(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(src)]))
v=next(x for x in j['streams'] if x['codec_type']=='video')
dur=float(j['format']['duration'])
meta={'source':'CC BY 4.0 G Edward Johnson September 2025','source_url':url,
      'native_video':'7680x4320 original, Wikimedia 1080p VP9 transcode used for preview',
      'width':v['width'],'height':v['height'],'duration':dur,'fps':v.get('avg_frame_rate'),'bytes':size}
print('VERIFIED',meta,flush=True)
c=Image.new('RGB',(4*380,3*255),'#111');d=ImageDraw.Draw(c)
for i,t in enumerate([.2,1.2,2.3,3.4,4.5,5.5,6.5,7.5,8.5,9.5,11,13]):
 t=min(t,dur-.3)
 f=O/f'frame_{i}.jpg'
 sh(['ffmpeg','-hide_banner','-v','error','-y','-ss',str(t),'-i',str(src),'-frames:v','1',str(f)])
 with Image.open(f) as im:
  im.thumbnail((375,220));x=(i%4)*380;y=(i//4)*255;c.paste(im,(x+(380-im.width)//2,y))
  d.text((x+8,y+228),f'Footage {t:.1f}s',fill='white')
c.save(O/'ETERNAL_FLAME_ORIGINAL_CONTACT.jpg',quality=88)
(O/'FOOTAGE_QA.json').write_text(json.dumps(meta,indent=2))
