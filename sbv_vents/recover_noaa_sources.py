from pathlib import Path
from urllib.parse import urljoin
import requests,subprocess,json,hashlib,re,io
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw
out=Path('source_media');out.mkdir(exist_ok=True)
sources={
 'moytirra':'https://oceanexplorer.noaa.gov/multimedia/edu-themes-vents-and-volcanoes-media-video-multimedia-moytirra/',
 'smallsmoker':'https://oceanexplorer.noaa.gov/multimedia/okeanos-explorations-22voyage-to-the-ridge-gallery-media-ex2205-dive02-smoker/',
 'extinct':'https://oceanexplorer.noaa.gov/multimedia/edu-themes-vents-and-volcanoes-media-video-multimedia-extinctchimney/',
 'underwater_volcano':'https://oceanexplorer.noaa.gov/multimedia/video-playlist-ex1605-uw-volcano/',
 'ventshrimp':'https://oceanexplorer.noaa.gov/multimedia/video-shorts-ex1104-ventshrimp/',
 'oases':'https://oceanexplorer.noaa.gov/multimedia/video-playlist-ex1605-vents/'
}
s=requests.Session();s.headers.update({'User-Agent':'Mozilla/5.0 (educational film research)'})
manifest=[]
for key,page in sources.items():
 item={'key':key,'source_page':page,'clips':[]}
 try:
  res=s.get(page,timeout=32);res.raise_for_status(); soup=BeautifulSoup(res.text,'html.parser')
  anchors=[(a.get_text(' ',strip=True),urljoin(res.url,a.get('href',''))) for a in soup.select('a[href]')]
  candidates=[(name,url) for name,url in anchors if '.mp4' in url.lower()]
  hd=[(name,url) for name,url in candidates if re.search(r'HD version',name,re.I)]
  pick=hd[-1] if hd else (candidates[-1] if candidates else None)
  if pick is None: raise Exception('no downloadable mp4 '+str(anchors[-12:]))
  item['video_url']=pick[1];print('SOURCE',key,pick,flush=True)
  f=out/(key+'.mp4')
  with s.get(pick[1],stream=True,timeout=160) as dl:
   dl.raise_for_status()
   with f.open('wb') as w:
    for b in dl.iter_content(1024*1024): w.write(b)
  q=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate:format=duration','-of','json',str(f)],capture_output=True,text=True,timeout=22)
  if q.returncode:raise Exception('probe '+q.stderr[-500:])
  info=json.loads(q.stdout); item['probe']=info;duration=float(info['format']['duration']);item['bytes']=f.stat().st_size
  # Fixed cuts from independently distinct real source segments
  clip_len=min(17.,max(8.,duration/5))
  count=5 if duration>75 else 4
  for i in range(count):
   t=max(0.,(duration-clip_len)*(i/(count-1)))
   dest=out/(key+f'_{i:02d}.mp4')
   cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t:.2f}','-i',str(f),'-t',f'{clip_len:.2f}','-an','-vf','fps=30,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1','-c:v','libx264','-preset','veryfast','-crf','24','-maxrate','2100k','-bufsize','4200k','-pix_fmt','yuv420p',str(dest)]
   p=subprocess.run(cmd,capture_output=True,text=True,timeout=115)
   if p.returncode!=0: print('CLIPERROR',key,i,p.stderr[-500:],flush=True);continue
   item['clips'].append({'name':dest.name,'source_start':round(t,2),'duration':clip_len,'bytes':dest.stat().st_size})
  # only keep originals if ffmpeg extracted proxy samples
  if item['clips']:f.unlink()
  print('DONE',key,'seconds',duration,'CLIPS',len(item['clips']),flush=True)
 except Exception as e: item['error']=str(e);print('ERROR',key,repr(e),flush=True)
 manifest.append(item)
(out/'sources_manifest.json').write_text(json.dumps(manifest,indent=2))
# contact sheet first frame per clip across all sources
clips=sorted(out.glob('*_??.mp4'));W,H=275,178
can=Image.new('RGB',(W*5,H*((len(clips)+4)//5)),(8,10,16));d=ImageDraw.Draw(can)
for i,path in enumerate(clips):
 x=subprocess.run(['ffmpeg','-loglevel','error','-ss','2','-i',str(path),'-frames:v','1','-vf','scale=275:155','-f','image2pipe','-vcodec','mjpeg','pipe:1'],capture_output=True)
 if x.returncode==0 and x.stdout:
  im=Image.open(io.BytesIO(x.stdout)).convert('RGB');can.paste(im,(i%5*W,i//5*H))
 d.text((i%5*W+4,i//5*H+156),path.stem,fill='white')
can.save(out/'source_contacts.jpg',quality=87)
print('RESULT',len(clips),'clips',sum(x.stat().st_size for x in clips),'bytes',flush=True)
