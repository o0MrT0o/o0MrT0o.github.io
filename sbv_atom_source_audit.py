#!/usr/bin/env python3
"""Acquire/inspect authentic original experimental footage for a private documentary edit."""
import requests,subprocess,os,re,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from bs4 import BeautifulSoup
D=Path("atom_video_source");D.mkdir(exist_ok=True)
s=requests.Session();s.headers.update({"User-Agent":"StrangeButVerifiedSourceAudit/1.0 (science documentary research; contact: source-audit@example.org)","Accept":"*/*"})
records=[]
def probe(p):
 r=subprocess.run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(p)],capture_output=True,text=True)
 if r.returncode:return {"error":r.stderr[-400:]}
 j=json.loads(r.stdout)
 v=next((z for z in j["streams"] if z.get("codec_type")=="video"),{})
 return {"width":v.get("width"),"height":v.get("height"),"duration":j["format"].get("duration"),"bytes":p.stat().st_size}
def download(name,url,limit=90_000_000):
 record={"name":name,"url":url}
 try:
  print("GET",name,url,flush=True)
  with s.get(url,stream=True,timeout=(25,80),allow_redirects=True) as r:
   record.update({"http_status":r.status_code,"ctype":r.headers.get("Content-Type"),"content_length":r.headers.get("Content-Length")})
   r.raise_for_status()
   if int(r.headers.get("Content-Length",0))>limit:raise RuntimeError("Too large")
   p=D/f"{name}.mp4" if name!="rubidium_mot" else D/"rubidium_mot.webm"
   n=0
   with p.open("wb") as o:
    for ch in r.iter_content(1024*1024):
     if not ch:continue
     n+=len(ch)
     if n>limit:raise RuntimeError("stream too large")
     o.write(ch)
   if n<40000:raise RuntimeError("too small")
   record["filepath"]=str(p);record["probe"]=probe(p)
   if "error" in record["probe"]:p.unlink(missing_ok=True)
 except Exception as e:record["error"]=str(e)[:400]
 records.append(record)
 print("RESULT",json.dumps(record)[:700],flush=True)
try:
 u="https://commons.wikimedia.org/w/api.php"
 payload=s.get(u,params={"action":"query","titles":"File:Open Quantum Rubidium MOT.webm","prop":"imageinfo","iiprop":"url|extmetadata","format":"json"},timeout=50).json()
 page=next(iter(payload["query"]["pages"].values()))
 inf=page["imageinfo"][0]
 license_short=inf.get("extmetadata",{}).get("LicenseShortName",{}).get("value")
 print("WIKIMEDIA",inf["url"],license_short,flush=True)
 download("rubidium_mot",inf["url"])
 records[-1]["license"]=license_short
except Exception as e:print("WIKIMEDIA ERROR",str(e)[:400],flush=True)
download("single_potassium_atom_illinois","https://publish.illinois.edu/gadwaylab/files/2021/03/atom1.mp4")
download("atom_trap_transport_illinois","https://publish.illinois.edu/gadwaylab/files/2021/02/motTransfer.mp4")
for label,url in [("nist_ions","https://www.nist.gov/video/ions-trap")]:
 try:
  html=s.get(url,timeout=30).text
  soup=BeautifulSoup(html,"html.parser")
  urls=set()
  for src in re.findall(r'["\']([^"\']+\.(?:mp4|webm)(?:\?[^"\']*)?)',html,re.I):
   if src.startswith("//"):src="https:"+src
   if src.startswith("/"):src="https://www.nist.gov"+src
   if src.startswith("http"):urls.add(src.replace("&amp;","&"))
  print("NIST VIDEO URL CANDIDATES",list(urls)[:10],flush=True)
  if urls: download("nist_ion_trap",sorted(urls)[0])
 except Exception as e:print("NIST ERROR",str(e)[:250])
(D/"SOURCE_MANIFEST.json").write_text(json.dumps(records,indent=2))
files=[D/x["filepath"].split("/")[-1] for x in records if x.get("filepath") and (D/x["filepath"].split("/")[-1]).is_file()]
for file in files:
 info=probe(file)
 try:
  dur=float(info.get("duration",0))
  ts=[dur*(i+.3)/12 for i in range(12)]
  sheet=Image.new("RGB",(4*350,3*255),"#141920");d=ImageDraw.Draw(sheet)
  for i,t in enumerate(ts):
   pic=D/f"{file.stem}_frame_{i:02d}.jpg"
   r=subprocess.run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",str(file),"-frames:v","1","-vf","scale=330:205:force_original_aspect_ratio=decrease",str(pic)],capture_output=True,text=True)
   if r.returncode or not pic.exists():continue
   with Image.open(pic) as im:sheet.paste(im,(i%4*350+10,i//4*255))
   d.text((i%4*350+10,i//4*255+211),f"{t:.2f}s",fill="white")
  sheet.save(D/f"{file.stem}_CONTACT.jpg",quality=87)
 except Exception as e:print("SHEET ERROR",file,str(e)[:220])
print("AUDIT COMPLETE",len(files),"source video files",flush=True)
