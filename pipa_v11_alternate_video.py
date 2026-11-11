#!/usr/bin/env python3
"""Download only legitimate public preview media for private, non-distributable editorial evaluation."""
import subprocess,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
D=Path("pipa_v11_sources");D.mkdir(exist_ok=True)
sources=[("new_Dailymotion_baby_pockets","https://www.dailymotion.com/video/x69bac9"),("new_Rumble_ecoscope","https://rumble.com/v6t6yul-the-surinam-toad-pipa-pipa.html")]
def run(args,timeout=150):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 print("CMD",args[:5],"status",p.returncode,"ERR",p.stderr[-500:],flush=True)
 return p
manifest=[]
for name,url in sources:
 rec={"name":name,"url":url}
 inf=run(["yt-dlp","--skip-download","--dump-single-json","--no-warnings","--no-playlist",url],90)
 if inf.returncode==0:
  j=json.loads(inf.stdout)
  rec.update({key:j.get(key) for key in ("title","uploader","duration","width","height","license","description") if key!="description"})
  rec["description"]=(j.get("description") or "")[:400]
 else:
  rec["error"]=inf.stderr[-250:]
  manifest.append(rec);continue
 f=D/(name+".mp4")
 get=run(["yt-dlp","--no-playlist","--no-warnings","--retries","2","-f","bv*[height<=1080]+ba/b[height<=1080]/best","--merge-output-format","mp4","-o",str(f),url],180)
 if get.returncode or not f.exists():
  rec["download_error"]=get.stderr[-500:];manifest.append(rec);continue
 info=run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(f)],50)
 if info.returncode==0:
  rec["ffprobe"]=json.loads(info.stdout)
 dur=float(rec["ffprobe"]["format"]["duration"]);rec["bytes"]=f.stat().st_size
 N=30
 sheet=Image.new("RGB",(5*320,6*222),"#182028");d=ImageDraw.Draw(sheet);font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",17)
 for i in range(N):
  t=dur*(i+.3)/N
  jpg=D/f"{name}_frame_{i:02d}.jpg"
  z=run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",str(f),"-frames:v","1","-vf","scale=310:175:force_original_aspect_ratio=decrease",str(jpg)],40)
  if z.returncode:continue
  with Image.open(jpg) as frame:sheet.paste(frame,(i%5*320+5,i//5*222))
  d.text((i%5*320+8,i//5*222+181),f"{t:.1f}s",font=font,fill="white")
 sheet.save(D/(name+"_CONTACT.jpg"),quality=88)
 manifest.append(rec)
 print("CANDIDATE",json.dumps(rec,ensure_ascii=False)[:950],flush=True)
(D/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print("AUDIT DONE",flush=True)
