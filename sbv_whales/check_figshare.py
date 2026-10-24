import requests,json,subprocess,pathlib,os
p=pathlib.Path('new_research_2026');p.mkdir(exist_ok=True)
u='https://api.figshare.com/v2/collections/8213611/articles'
r=requests.get(u,timeout=35);print('STATUS',r.status_code,r.text[:400],flush=True);r.raise_for_status()
articles=r.json(); (p/'articles.json').write_text(json.dumps(articles,indent=2))
for a in articles[:30]:
 id=a['id'];q=requests.get(f'https://api.figshare.com/v2/articles/{id}',timeout=35)
 if q.status_code!=200:continue
 v=q.json(); print('ARTICLE',id,v.get('title'),'LICENSE',v.get('license'),flush=True)
 for f in v.get('files',[]):
  print('FILE',f.get('name'),'SIZE',f.get('size'),'URL',f.get('download_url'),flush=True)
  if f.get('size',0)>200_000_000:continue
  if not (f.get('name','').lower().endswith(('.mp4','.webm','.mov'))):continue
  dest=p/pathlib.Path(f['name']).name
  with requests.get(f['download_url'],stream=True,timeout=120) as rr:
   rr.raise_for_status()
   with dest.open('wb') as out:
    for ch in rr.iter_content(1<<20):out.write(ch)
  info=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height:format=duration','-of','json',str(dest)],text=True,capture_output=True)
  print('PROBE',dest.name,info.stdout,flush=True)
