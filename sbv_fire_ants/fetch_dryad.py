from pathlib import Path
import requests,json,zipfile,subprocess,io,os,shutil
ROOT=Path("."); src=ROOT/"sbv_fire_ants"/"source";src.mkdir(parents=True,exist_ok=True)
api="https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.d51c5b0cv"
r=requests.get(api,timeout=45);r.raise_for_status();data=r.json()
(ROOT/"sbv_fire_ants"/"dryad_metadata.json").write_text(json.dumps(data,indent=2))
files=data.get("files",[])
print("DATASET",data.get("title"),"FILES",len(files),flush=True)
for f in files:
 name=f.get("path") or f.get("filename") or f.get("name") or "unknown"
 dl=f.get("download") or f.get("download_url") or f.get("url")
 if not dl:
  print("NO_DOWNLOAD",name, f.keys(),flush=True);continue
 if not any(s in name.lower() for s in ("supplementary","video","movie","zip","mp4","mov","avi")):continue
 out=src/Path(name).name
 print("DOWNLOADING",name,dl,flush=True)
 with requests.get(dl,stream=True,timeout=180) as rr:
  rr.raise_for_status()
  with out.open("wb") as w:
   for c in rr.iter_content(1<<20):
    if c:w.write(c)
 print("SAVED",out,out.stat().st_size,flush=True)
for z in list(src.glob("*.zip")):
 dest=src/(z.stem+"_extracted");dest.mkdir(exist_ok=True)
 try:
  with zipfile.ZipFile(z) as zz:zz.extractall(dest)
 except Exception as e: print("ZIP_ERROR",z,e,flush=True)
vids=[]
for p in src.rglob("*"):
 if p.is_file() and p.suffix.lower() in (".mp4",".mov",".avi",".m4v"):
  q=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height","-of","json",str(p)],capture_output=True,text=True)
  try: meta=json.loads(q.stdout);stream=meta["streams"][0];dur=float(meta["format"]["duration"])
  except Exception:continue
  vids.append({"path":str(p),"duration":dur,"width":stream.get("width"),"height":stream.get("height"),"size":p.stat().st_size})
(ROOT/"sbv_fire_ants"/"video_manifest.json").write_text(json.dumps(vids,indent=2))
print("VIDEOS",json.dumps(vids,indent=2),flush=True)
