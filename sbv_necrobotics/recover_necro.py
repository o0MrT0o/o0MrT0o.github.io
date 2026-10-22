import requests,xml.etree.ElementTree as ET,tarfile,io,subprocess,traceback
from pathlib import Path
out=Path('sources');out.mkdir(exist_ok=True)
log=[]
def event(*a):
 s=' '.join(str(x) for x in a);print(s,flush=True);log.append(s)
def download(url,timeout=90):
 event('GET',url)
 r=requests.get(url,timeout=timeout,headers={'User-Agent':'Mozilla/5.0 (educational research)'})
 event('status',r.status_code,'bytes',len(r.content),'mime',r.headers.get('content-type'))
 r.raise_for_status()
 return r.content
try:
 x=download('https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC9561765')
 event(x[:1200])
 root=ET.fromstring(x)
 for item in root.findall('.//link'):
  if item.attrib.get('format') in ['tgz','tar.gz']:
   url=item.attrib['href'].replace('ftp://ftp.ncbi.nlm.nih.gov/','https://ftp.ncbi.nlm.nih.gov/')
   buf=download(url,120)
   with tarfile.open(fileobj=io.BytesIO(buf),mode='r:gz') as t:
    media=[a for a in t.getmembers() if a.name.lower().endswith(('.mp4','.webm','.mov'))]
    event('media files',[(m.name,m.size) for m in media])
    for m in media:
     dest=out/Path(m.name).name
     with t.extractfile(m) as src,open(dest,'wb') as dst:
      while chunk:=src.read(1<<20):dst.write(chunk)
except Exception as e:event('OA_ERROR',repr(e));traceback.print_exc()
if not list(out.glob('*.mp4')):
 try:
  xml=download('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9561765/fullTextXML',30)
  root=ET.fromstring(xml)
  for a in root.iter():
   h=a.attrib.get('{http://www.w3.org/1999/xlink}href','')
   if '.mp4' in h:event('EUROPEPMC HREF',h)
 except Exception as e:event('EPMC_ERROR',repr(e))
for f in sorted(out.glob('*.mp4')):
 p=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate:format=duration','-of','json',str(f)],capture_output=True,text=True)
 event('PROBE',f.name, f.stat().st_size, p.stdout[:700])
Path('recovery_log.txt').write_text('\n'.join(log))
if not list(out.glob('*.mp4')):event('NO_VIDEO_EXTRACTED')
