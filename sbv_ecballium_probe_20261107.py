import requests,zipfile,io,json,os,subprocess,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
D=Path('ecballium_media');D.mkdir(exist_ok=True); O=Path('probe_output');O.mkdir(exist_ok=True)
agent='Mozilla/5.0 (compatible; research video retrieval for educational documentary)'
S=requests.Session();S.headers.update({'User-Agent':agent})
def grab(url,path,max_mb=150):
 try:
  r=S.get(url,timeout=110,stream=True);print('GET',r.status_code,r.headers.get('content-type'),url,flush=True);r.raise_for_status()
  with open(path,'wb') as f:
   z=0
   for chunk in r.iter_content(1024*1024):
    if chunk:f.write(chunk);z+=len(chunk)
    if z>max_mb*1048576:raise RuntimeError('over max size')
  if path.stat().st_size<40000:raise RuntimeError('too small')
  print('Downloaded bytes',path.stat().st_size,flush=True);return True
 except Exception as e:
  print('FAILED',type(e).__name__,str(e)[:250],flush=True);path.unlink(missing_ok=True);return False
url="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11648854/supplementaryFiles"
zippath=D/'supplementary.zip'
if grab(url,zippath):
 try:
  with zipfile.ZipFile(zippath) as z:
   print('ARCHIVE files',[(i.filename,i.file_size) for i in z.infolist()],flush=True)
   for i in z.infolist():
    suffix=Path(i.filename).suffix.lower()
    if suffix in ['.avi','.mov','.mp4'] and i.file_size<120000000:
     name=Path(i.filename).name
     dest=D/name
     with z.open(i) as src,open(dest,'wb') as dst:shutil.copyfileobj(src,dst)
 except Exception as e:print('BAD ZIP',repr(e),flush=True)
for n,ext in [('03','.avi'),('02','.mov'),('01','.mov')]:
 target=D/f'pnas.2410420121.sm{n}{ext}'
 if target.exists():continue
 urls=[
 f'https://pmc.ncbi.nlm.nih.gov/articles/instance/11648854/bin/pnas.2410420121.sm{n}{ext}',
 f'https://www.pnas.org/doi/suppl/10.1073/pnas.2410420121/suppl_file/pnas.2410420121.sm{n}{ext}'
 ]
 for u in urls:
  if grab(u,target):break
# also try Manchester press video only to test quality, NOT for actual reuse
probe={}
def run(cmd):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-1500:])
 return p.stdout
for path in sorted(D.iterdir()):
 if path.suffix.lower() not in ('.avi','.mov','.mp4'):continue
 try:
  j=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
  vid=next((x for x in j['streams'] if x['codec_type']=='video'),None)
  if not vid:continue
  dur=float(j['format']['duration'])
  probe[path.name]={'width':vid['width'],'height':vid['height'],'fps':vid.get('avg_frame_rate'),'duration':dur,'codec':vid['codec_name'],'bytes':path.stat().st_size}
  frames=[0.1,.5,1,2,3,5,8,12,16,20,30]
  if dur<30:frames=[round(dur*x,2) for x in [.03,.10,.18,.27,.38,.49,.60,.70,.8,.87,.95]]
  imgs=[]
  for idx,t in enumerate(frames):
   p=O/f'{path.stem}_{idx:02d}.png'
   try:
    run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(path),'-frames:v','1',str(p)])
    with Image.open(p) as im:imgs.append((t,im.convert('RGB').copy()))
   except Exception as e:print('FRAME_ERR',path.name,t,str(e)[:100])
  montage=Image.new('RGB',(4*320,3*260),'#17191d');draw=ImageDraw.Draw(montage)
  for k,(t,im) in enumerate(imgs[:12]):
   im.thumbnail((315,220));x=(k%4)*320;y=(k//4)*260;montage.paste(im,(x+(320-im.width)//2,y))
   draw.text((x+8,y+225),f'{path.stem} @ {t:.2f}s',fill='white')
  montage.save(O/f'CONTACT_{path.stem}.jpg',quality=87)
 except Exception as e:print('FILE_ERR',path.name,repr(e),flush=True)
(O/'PROBE.json').write_text(json.dumps(probe,indent=2))
print('PROBE',json.dumps(probe,indent=2),flush=True)
if not probe:raise RuntimeError('No useful motion footage could be retrieved')
