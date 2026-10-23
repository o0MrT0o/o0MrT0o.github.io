import requests,zipfile,io,json,subprocess,pathlib
out=pathlib.Path('sbv_candidate_quality');out.mkdir(exist_ok=True)
res={}
for pmcid in ['PMC4922196','PMC12956967']:
 entry=[];res[pmcid]=entry
 u=f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/supplementaryFiles?includeInlineImage=no'
 try:
  rr=requests.get(u,timeout=150)
  print('FETCH',pmcid,rr.status_code,len(rr.content),rr.headers.get('content-type'),flush=True)
  rr.raise_for_status()
  with zipfile.ZipFile(io.BytesIO(rr.content)) as z:
   for info in z.infolist():
    if not info.filename.lower().endswith(('.mp4','.avi','.mov','.webm','.m4v')):continue
    data=z.read(info.filename);p=out/(pmcid+'_'+pathlib.Path(info.filename).name);p.write_bytes(data)
    c=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate:format=duration','-of','json',str(p)],capture_output=True,text=True,timeout=25)
    v=json.loads(c.stdout) if c.returncode==0 else {'err':c.stderr}
    entry.append({'name':p.name,'size':len(data),'probe':v})
    print('VIDEO',pmcid,p.name,len(data),v,flush=True)
    if len(entry)>=12:break
 except Exception as e:print('ERR',pmcid,repr(e),flush=True);entry.append({'error':repr(e)})
(out/'manifest.json').write_text(json.dumps(res,indent=2))
