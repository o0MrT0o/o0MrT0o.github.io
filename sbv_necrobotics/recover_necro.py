import requests,zipfile,io,subprocess,traceback,hashlib
from pathlib import Path
out=Path('sources');out.mkdir(exist_ok=True)
log=[]
def say(*a):
 s=' '.join(map(str,a));print(s,flush=True);log.append(s)
def dl(url,timeout=120):
 say('GET',url)
 r=requests.get(url,timeout=timeout,headers={'User-Agent':'SBV/1.0 academic-media-check'})
 say('STATUS',r.status_code,'SIZE',len(r.content),'MIME',r.headers.get('Content-Type'))
 r.raise_for_status();return r.content
try:
 data=dl('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9561765/supplementaryFiles',180)
 if not zipfile.is_zipfile(io.BytesIO(data)):raise RuntimeError('Not ZIP: '+repr(data[:200]))
 with zipfile.ZipFile(io.BytesIO(data)) as archive:
  allnames=archive.namelist();say('ZIP_ENTRIES',allnames[:80])
  for n in allnames:
   if n.lower().endswith(('.mp4','.mov','.webm')) and not n.endswith('/'):
    target=out/Path(n).name
    target.write_bytes(archive.read(n));say('EXTRACTED',str(target),target.stat().st_size)
except Exception as e:say('EPMC_ZIP_ERROR',repr(e));traceback.print_exc()
if not list(out.glob('*.mp4')):
 for n in ['ADVS-9-2201174-s001.mp4','ADVS-9-2201174-s003.mp4','ADVS-9-2201174-s004.mp4','ADVS-9-2201174-s005.mp4']:
  try:
   u='https://pmc.ncbi.nlm.nih.gov/articles/PMC9561765/bin/'+n
   data=dl(u,70)
   if len(data)>100000 and b'ftyp' in data[:100]:
    (out/n).write_bytes(data);say('DIRECT_OK',n)
  except Exception as e:say('DIRECT_ERROR',n,repr(e))
for f in sorted(out.glob('*')):
 if f.is_file():
  say('FILE',f.name,f.stat().st_size,hashlib.sha256(f.read_bytes()).hexdigest())
  try:
   p=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate:format=duration','-of','json',str(f)],capture_output=True,text=True,timeout=15)
   say('PROBE',p.returncode,p.stdout[:700],p.stderr[:200])
  except Exception as e:say('PROBE_ERROR',repr(e))
Path('recovery_log.txt').write_text('\n'.join(log))
