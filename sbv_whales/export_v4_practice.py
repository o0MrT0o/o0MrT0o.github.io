from pathlib import Path
import requests,subprocess,json
p=Path('v4_source_clips');p.mkdir(exist_ok=True)
f=p/'whole_practice.mp4'
url='https://ndownloader.figshare.com/files/60552604'
with requests.get(url,stream=True,timeout=170) as r:
 r.raise_for_status()
 with f.open('wb') as out:
  for chunk in r.iter_content(1<<20):out.write(chunk)
print('SOURCE SIZE',f.stat().st_size,flush=True)
ranges=[
 ("practice_hook",37,15),
 ("practice_ring",24,16),
 ("practice_second",106,42),
 ("practice_final",184,25)]
metadata=[]
for name,start,duration in ranges:
 target=p/(name+'.mp4')
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(f),'-t',str(duration),'-an','-vf','fps=30','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
 x=subprocess.run(cmd,text=True,capture_output=True)
 print('CLIP',name,x.returncode,target.stat().st_size if target.exists() else None,x.stderr[-500:],flush=True)
 metadata.append({'name':name,'source_time':start,'duration':duration,'filename':str(target),'ffmpeg_exit':x.returncode})
(p/'clip_manifest.json').write_text(json.dumps({'license':'CC BY 4.0','source':'https://doi.org/10.6084/m9.figshare.30932569.v1','clips':metadata},indent=2))
f.unlink()
