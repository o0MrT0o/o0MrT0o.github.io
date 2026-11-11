#!/usr/bin/env python3
"""Download actual licensed public-domain USGS volcanic whirlwinds and eruption footage for editorial inspection."""
from pathlib import Path
import subprocess,json,urllib.request,shutil,math,os
from PIL import Image,ImageDraw,ImageFont
root=Path("sbv_volcano_source");root.mkdir(exist_ok=True)
HOST="https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/"
srcs=[
("2025_volcanic_whirlwind_and_lava",HOST+"media/video/20250117_ground_video.mp4","https://www.usgs.gov/media/videos/january-17-2025-kilauea-summit-eruption-video"),
("2023_lava_vortex",HOST+"media/video/20230607whirlwind.mp4","https://www.usgs.gov/media/videos/kilauea-summit-whirlwind-halemaumau-june-7-2023"),
("2018_fissure_whirlwind",HOST+"atoms/video/multimediaFile-2351.mp4","https://www.usgs.gov/media/videos/kilauea-volcano-whirlwind-above-fissure-8"),
]
def call(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 print("CMD",cmd[:9],"RET",p.returncode,"ERROR",p.stderr[-600:],flush=True)
 if p.returncode:raise RuntimeError(p.stderr[-800:])
 return p.stdout
report=[]
for label,url,page in srcs:
 rec={"label":label,"source_url":url,"source_page":page,"license":"USGS Public Domain"}
 raw=root/(label+"_source.mp4")
 try:
  headers={"User-Agent":"Mozilla/5.0 (Video editor verifying USGS public-domain media)"}
  req=urllib.request.Request(url,headers=headers)
  with urllib.request.urlopen(req,timeout=130) as resp,open(raw,"wb") as fout:
   shutil.copyfileobj(resp,fout)
  print("DOWNLOADED",label,raw.stat().st_size,flush=True)
  inf=json.loads(call(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_type,width,height,codec_name","-of","json",str(raw)]))
  rec["probe"]=inf
  dur=float(inf["format"]["duration"])
  # Save 1280-wide true footage clips for offline scene choice. Do not save original high-bitrate files in artifact.
  intervals=[(0,min(28,dur),"early")]
  if dur>65:
   intervals.append((max(0,dur-42),min(42,dur),"late"))
  elif dur>35:
   intervals.append((dur/2,min(23,dur/2),"late"))
  for st,length,suffix in intervals:
   target=root/(f"{label}_{suffix}_proxy.mp4")
   call(["ffmpeg","-hide_banner","-v","error","-y","-ss",str(round(st,2)),"-i",str(raw),"-t",str(round(length,2)),
         "-vf","scale=1280:-2:flags=lanczos,setsar=1,fps=30","-c:v","libx264","-preset","ultrafast",
         "-crf","25","-pix_fmt","yuv420p","-an","-movflags","+faststart",str(target)])
   rec.setdefault("proxies",[]).append({"filename":target.name,"start":st,"length":length,"bytes":target.stat().st_size})
  imw,imh=320,200;cols=5;rows=5
  sheet=Image.new("RGB",(imw*cols,imh*rows),(14,20,26));draw=ImageDraw.Draw(sheet)
  font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",16)
  for i in range(25):
   t=dur*((i+.35)/25)
   p=root/(label+"_preview_"+str(i).zfill(2)+".jpg")
   call(["ffmpeg","-hide_banner","-v","error","-y","-ss",f"{t:.2f}","-i",str(raw),"-frames:v","1",
    "-vf","scale=300:155:force_original_aspect_ratio=decrease","-q:v","4",str(p)])
   with Image.open(p) as img:
    img=img.convert("RGB");x=i%cols*imw;y=i//cols*imh
    sheet.paste(img,(x+(imw-img.width)//2,y))
    draw.text((x+8,y+161),f"{t:.1f}s",font=font,fill="white")
   p.unlink()
  sheet.save(root/(label+"_SOURCE_CONTACT.jpg"),quality=88)
  raw.unlink()
  rec["status"]="OK"
 except Exception as e:
  rec["status"]="FAILED";rec["error"]=str(e)[:1000]
  print("DOWNLOAD_OR_QA_FAILED",label,str(e)[:500],flush=True)
  if raw.exists():raw.unlink()
 report.append(rec)
 (root/"SOURCE_QA.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
print("RESULT",[(x["label"],x["status"]) for x in report],flush=True)
if not any(x["status"]=="OK" for x in report):raise SystemExit("NO_SOURCE_VIDEO")
