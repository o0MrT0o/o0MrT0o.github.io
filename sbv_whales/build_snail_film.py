from pathlib import Path
import requests,subprocess,json,re,os,sys,zipfile
from PIL import Image,ImageDraw
p=Path('snail_film');p.mkdir(exist_ok=True)
sources=[
 ('commons_leuco.ogv','https://upload.wikimedia.org/wikipedia/commons/5/55/Leucochloridium.ogv'),
 ('smithsonian.mp4','https://insider.si.edu/wp-content/uploads/2014/11/Leucochloridium-paradoxum-2.mp4'),
 ('ambrette.ogv','https://upload.wikimedia.org/wikipedia/commons/2/26/Ambrette_commune_001.ogv'),
]
for name,url in sources:
 f=p/name
 try:
  with requests.get(url,timeout=120,stream=True,headers={'User-Agent':'StrangeButVerifiedProduction/1.0 contact: production@example.com'}) as r:
   print('FETCH',name,r.status_code,r.headers.get('content-type'),flush=True);r.raise_for_status()
   with f.open('wb') as out:
    for c in r.iter_content(1024*1024):out.write(c)
  q=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height:format=duration','-of','json',str(f)],capture_output=True,text=True)
  print('PROBE',name,q.stdout,flush=True)
 except Exception as e: print('SOURCE_FAIL',name,repr(e),flush=True)
