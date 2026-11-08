from pathlib import Path
from PIL import Image,ImageDraw
import requests,subprocess,json,math,statistics,time
D=Path("headless_sources");D.mkdir(exist_ok=True)
O=Path("headless_qc");O.mkdir(exist_ok=True)
src=[
 ("2017_actual_Enypniastes","https://oceanexplorer.noaa.gov/wp-content/uploads/2026/04/Headless-Chicken-Monster-Fact-Video-720p.mp4","Enypniastes eximia, Gulf of Mexico 2017, NOAA Ocean Exploration"),
 ("2026_other_swimming_seacucumber","https://oceanexplorer.noaa.gov/wp-content/uploads/2026/09/ex2606-dive03-seacuke.mp4","Unspecified swimming sea cucumber, American Samoa 2026, NOAA Ocean Exploration"),
 ("2023_other_swimming_seacucumber","https://oceanexplorer.noaa.gov/wp-content/uploads/2023/07/dive05-seacuke-1280x720-1.mp4","Unspecified swimming sea cucumber, Alaska 2023, NOAA Ocean Exploration"),
 ("2025_other_swimming_seacucumber","https://oceanexplorer.noaa.gov/wp-content/uploads/2026/10/ex2502-dive08-0326-seacuke_1920x1080.mp4","Yellow family Synallactidae sea cucumber, Hawaii 2025, NOAA Ocean Exploration")
]
def shell(*cmd):
 p=subprocess.run(list(cmd),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:raise RuntimeError(' '.join(cmd[:8])+': '+p.stderr[-800:])
 return p.stdout
rows=[]
for tag,url,desc in src:
 p=D/f'{tag}.mp4'
 for trial in range(3):
  try:
   with requests.get(url,timeout=100,stream=True,headers={'User-Agent':'Mozilla/5.0'}) as r:
    print('GET',r.status_code,r.headers.get('Content-Type'),r.headers.get('Content-Length'),tag,flush=True);r.raise_for_status()
    with p.open('wb') as f:
     n=0
     for chunk in r.iter_content(1024*1024):
      if chunk:f.write(chunk);n+=len(chunk)
      if n>100_000_000:raise RuntimeError('File > 100 MB')
   if n<1_000_000:raise RuntimeError('Video unexpectedly small')
   break
  except Exception as e:
   print('Download error',tag,repr(e),flush=True);p.unlink(missing_ok=True)
   if trial==2:raise
 j=json.loads(shell('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)))
 v=next(x for x in j['streams'] if x['codec_type']=='video')
 duration=float(j['format']['duration'])
 sheet=Image.new('RGB',(4*380,3*270),'#111827');draw=ImageDraw.Draw(sheet)
 frames=[]
 for i in range(12):
  t=duration*(.04 + i*.073)
  f=O/f'{tag}_{i:02d}.jpg'
  shell('ffmpeg','-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',str(p),'-frames:v','1',str(f))
  with Image.open(f) as im:
   img=im.convert('RGB');img.thumbnail((376,241))
   x=(i%4)*380;y=(i//4)*270
   sheet.paste(img,(x+(380-img.width)//2,y))
   draw.text((x+9,y+244),f'{t:.2f}s',fill='white')
  frames.append({'time':round(t,3),'file':f.name})
 sheet.save(O/f'{tag}_CONTACT.jpg',quality=88)
 metadata={'tag':tag,'description':desc,'url':url,'width':v['width'],'height':v['height'],'fps':v.get('avg_frame_rate'),
 'duration':duration,'codec':v['codec_name'],'filesize':p.stat().st_size,'frames':frames}
 rows.append(metadata)
 print('CHECKED',json.dumps({k:metadata[k] for k in ['tag','width','height','duration','fps','filesize']}),flush=True)
(O/'VIDEO_AUDIT.json').write_text(json.dumps(rows,indent=2))
print('PASS FOUR INDEPENDENT NOAA VIDEOS',flush=True)
