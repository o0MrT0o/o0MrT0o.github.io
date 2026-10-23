import requests,subprocess,pathlib,hashlib,json
sources={
"Y24_explanation":"https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/video/2024_Jul_24_Hydrothermal_Explosion_Biscuit_Basin.mp4",
"Y25_geyser":"https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/video/Biscuit_video.mp4",
"Y26_explosion":"https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/video/20260613_050945-051015.mp4",
"Y26_spouting":"https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/video/20260618_102430-102500_pool_geysering.mp4",
}
out=pathlib.Path('yellowstone_sources');out.mkdir(exist_ok=True);result={}
for name,url in sources.items():
 rec={'url':url};result[name]=rec
 try:
  h=requests.head(url,timeout=25,allow_redirects=True);rec['status']=h.status_code;rec['advertised_bytes']=h.headers.get('Content-Length');print(name,'HEAD',h.status_code,h.headers.get('Content-Length'),flush=True)
  if h.status_code!=200:continue
  if int(h.headers.get('Content-Length','0'))>200_000_000:rec['skipped']='too large';continue
  dest=out/(name+'.mp4')
  with requests.get(url,stream=True,timeout=100) as rr:
   rr.raise_for_status()
   with dest.open('wb') as fd:
    for chunk in rr.iter_content(1024*1024):fd.write(chunk)
  rec['actual_bytes']=dest.stat().st_size;rec['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
  p=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,avg_frame_rate:format=duration','-of','json',str(dest)],capture_output=True,text=True,timeout=30)
  rec['ffprobe']=json.loads(p.stdout) if p.returncode==0 else p.stderr[-500:]
  print(name,'PROBE',rec['ffprobe'],flush=True)
 except Exception as e:rec['error']=str(e);print(name,'ERROR',repr(e),flush=True)
(out/'manifest.json').write_text(json.dumps(result,indent=2))
