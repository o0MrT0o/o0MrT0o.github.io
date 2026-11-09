#!/usr/bin/env python3
"""Audit licensing and real Surinam-toad birth video candidates for SVB TikTok.
Never accept synthetic video, unverified third-party broadcasters' copyright, or unlicensed footage."""
from pathlib import Path
import json,subprocess,requests,os,re,shutil
from PIL import Image,ImageDraw
D=Path("surinam_source_audit"); D.mkdir(exist_ok=True)
Y="https://www.youtube.com/watch?v=0XtaTJe-ItE"
def sh(cmd,timeout=120):
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
 print("COMMAND",cmd[:4],"RET",r.returncode,"STDERR",r.stderr[-500:],flush=True)
 return r
videos=[
 ("quom_cc",Y),
 ("birth_animal", "https://www.youtube.com/watch?v=v4PVmxkrLKM")
]
manifest={"youtube":[],"commons":[]}
for label,url in videos:
 r=sh(["yt-dlp","--no-playlist","--skip-download","--dump-single-json","--no-warnings",url],timeout=65)
 if r.returncode:
  manifest["youtube"].append({"label":label,"status":"metadata_failed","error":r.stderr[-300:]})
  continue
 j=json.loads(r.stdout)
 license=j.get("license") or j.get("license_info")
 d={k:j.get(k) for k in ("id","title","uploader","upload_date","duration","width","height","license","availability","live_status")}
 d["label"]=label
 manifest["youtube"].append(d)
 print("LICENSE_METADATA",json.dumps(d),flush=True)
 # Only attempt reuse where YouTube explicitly declares Creative Commons attribution.
 if license and "creative commons" in str(license).lower() and label=="quom_cc":
  target=D/"quom_cc_authentic_candidate.mp4"
  cmd=["yt-dlp","--no-playlist","--no-warnings","--retries","2",
        "-f","bestvideo[height<=1080]+bestaudio/best[height<=1080]","--merge-output-format","mp4",
        "-o",str(target),url]
  rd=sh(cmd,timeout=180)
  if rd.returncode==0 and target.exists():
   d["downloaded"]=True;d["size"]=target.stat().st_size
   p=sh(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height,codec_name","-of","json",str(target)])
   d["ffprobe"]=json.loads(p.stdout) if p.returncode==0 else {}
  else:d["download_error"]=rd.stderr[-400:]
# Alternative Commons video discovery: ask MediaWiki for "Surinam toad" videos.
for term in ['Pipa pipa filetype:video','"Surinam toad" video','"Pipa pipa" video']:
 try:
  data=requests.get("https://commons.wikimedia.org/w/api.php",
    params={"action":"query","generator":"search","gsrsearch":term,
      "gsrnamespace":6,"gsrlimit":30,"prop":"imageinfo","iiprop":"url|mime|extmetadata","format":"json"},
    timeout=25,headers={"User-Agent":"StrangeButVerified creator video source review/1.0 (attribution research)"}).json()
  results=[]
  for z in data.get("query",{}).get("pages",{}).values():
   inf=z.get("imageinfo",[{}])[0]
   if inf.get("mime","").startswith("video/") or z.get("title","").lower().endswith((".webm",".ogv",".mp4",".mov")):
    e=inf.get("extmetadata",{})
    results.append({"title":z["title"],"url":inf.get("url"),"mime":inf.get("mime"),
      "license":e.get("LicenseShortName",{}).get("value",""),
      "attribution":re.sub('<[^>]*>','',e.get("Artist",{}).get("value",""))[:250]})
  manifest["commons"].append({"term":term,"results":results})
  print("COMMONS",term,len(results),results,flush=True)
 except Exception as e:
  manifest["commons"].append({"term":term,"error":str(e)[:220]})
  print("COMMONS_ERROR",term,str(e)[:220],flush=True)
# Contact sheet if downloaded
for src in D.glob("*.mp4"):
 try:
  cmd=["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(src)]
  duration=float(subprocess.check_output(cmd,text=True).strip())
  tlist=[duration*(i+0.2)/12 for i in range(12)]
  contact=Image.new("RGB",(4*340,3*240),(20,20,24))
  draw=ImageDraw.Draw(contact)
  for i,t in enumerate(tlist):
   f=D/f"thumb_{i:02}.jpg"
   p=sh(["ffmpeg","-v","error","-y","-ss",str(t),"-i",str(src),"-frames:v","1",str(f)])
   if p.returncode or not f.exists():continue
   with Image.open(f) as img:
    img.thumbnail((326,207));x=i%4*340;y=i//4*240
    contact.paste(img,(x+(340-img.width)//2,y))
    draw.text((x+8,y+211),f"{t:.1f} s",fill="white")
  contact.save(D/"SOURCE_CONTACT.jpg",quality=85)
 except Exception as e: print("CONTACT_ERROR",str(e)[:300],flush=True)
(D/"SOURCE_AUDIT.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print("AUDIT_DONE",json.dumps(manifest,ensure_ascii=False)[:6000],flush=True)
