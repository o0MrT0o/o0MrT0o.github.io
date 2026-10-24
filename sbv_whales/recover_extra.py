from pathlib import Path
import subprocess,requests,hashlib,json
from PIL import Image, ImageDraw
folder=Path('whale_extra');folder.mkdir(exist_ok=True)
urls=[
 ('commons','https://commons.wikimedia.org/wiki/Special:Redirect/file/Bubble_net_feeding.webm'),
]
manifest=[]
for name,url in urls:
 dest=folder/(name+'.webm')
 try:
  with requests.get(url,timeout=60,stream=True,headers={'User-Agent':'SBVResearchVideoBot/1.0 (+educational; http://example.com)'}) as r:
   print('URL',name,r.status_code,r.url,r.headers.get('Content-Length'),flush=True)
   r.raise_for_status()
   with dest.open('wb') as out:
    for chunk in r.iter_content(1<<20):out.write(chunk)
  p=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate:format=duration','-of','json',str(dest)],capture_output=True,text=True)
  manifest.append({'name':name,'url':url,'size':dest.stat().st_size,'probe':json.loads(p.stdout),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
  print('PROBE',manifest[-1],flush=True)
  for t in range(0,42,3):
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(dest),'-frames:v','1','-vf','scale=240:-2',str(folder/f'commons_{t:02d}.jpg')],check=True)
 except Exception as e:print('ERROR',name,repr(e),flush=True)
try:
 u='https://videos.fisheries.noaa.gov/detail/video/3911325489001/b-roll%3A-humpback-whales-and-behavior'
 command=['yt-dlp','--no-playlist','--socket-timeout','20','--format','best[height<=1080]/best','--output',str(folder/'noaa_behavior.%(ext)s'),u]
 p=subprocess.run(command,timeout=160,text=True,capture_output=True)
 print('NOAA_DLP',p.returncode,p.stdout[-1000:],p.stderr[-1200:],flush=True)
 for f in folder.glob('noaa_behavior.*'):
  q=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height:format=duration','-of','json',str(f)],capture_output=True,text=True)
  print('NOAA_MEDIA',f.name,f.stat().st_size,q.stdout,flush=True)
except Exception as e:print('NOAA_ERR',repr(e),flush=True)
frames=sorted(folder.glob('commons_*.jpg'))
if frames:
 w,h=240,350
 c=Image.new('RGB',(w*7,h*2),'#111')
 d=ImageDraw.Draw(c)
 for i,f in enumerate(frames):
  im=Image.open(f).convert('RGB'); im.thumbnail((240,315))
  x=(i%7)*w;y=(i//7)*h;c.paste(im,(x,y))
  d.text((x+8,y+320),f.stem,fill='white')
 c.save(folder/'commons_contact.jpg',quality=91)
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
