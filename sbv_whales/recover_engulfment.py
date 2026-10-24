import requests,zipfile,io,pathlib,subprocess,json,hashlib
from PIL import Image,ImageDraw
p=pathlib.Path('engulfment');p.mkdir(exist_ok=True)
u='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7449129/supplementaryFiles?includeInlineImage=no'
with requests.get(u,timeout=190) as r:
 print('ZIP',r.status_code,len(r.content),r.headers.get('Content-Type'),flush=True);r.raise_for_status();z=r.content
with zipfile.ZipFile(io.BytesIO(z)) as a:
 names=a.namelist();print('NAMES',names[:100],flush=True)
 for n in names:
  if n.lower().endswith(('.wmv','.mp4','.mov','.avi','.mkv')):
   b=a.read(n); target=p/pathlib.Path(n).name; target.write_bytes(b)
   print('VIDEO',target.name,len(b),flush=True)
   q=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height,codec_name:format=duration','-of','json',str(target)],capture_output=True,text=True)
   print('PROBE',q.stdout,flush=True)
   if len(b)>200_000_000:continue
   inf=json.loads(q.stdout);dur=float(inf['format']['duration'])
   thumbs=[]
   for t in range(0,int(dur),max(3,int(dur/30))):
    out=p/f'f_{t:03d}.jpg'
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-ss',str(t),'-i',str(target),'-frames:v','1','-vf','scale=270:-2',str(out)]
    rr=subprocess.run(cmd,capture_output=True)
    if rr.returncode==0:
     im=Image.open(out).convert('RGB');thumbs.append((t,im))
   if thumbs:
    w=270;h=185;C=Image.new('RGB',(w*6,h*((len(thumbs)+5)//6)),(15,15,15));D=ImageDraw.Draw(C)
    for i,(t,im) in enumerate(thumbs):
     x=i%6*w;y=i//6*h;im.thumbnail((270,155));C.paste(im,(x,y));D.text((x+5,y+157),f'{t}s',fill='white')
    C.save(p/'contact.jpg',quality=83)
