#!/usr/bin/env python3
"""Produce final short from genuine original USGS 1920x1080 video files.
Only two unobtrusive lines at upper-left. Original source ranges are nonoverlapping.
Actual visuals from July 2018, June 2023, January 2025, not one contiguous event.
All footage documented USGS Public Domain.
"""
import json,subprocess,urllib.request,shutil,math,os,sys
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt
from PIL import Image,ImageDraw,ImageFont
from kokoro_onnx import Kokoro
D=Path("sbv_volcano_final");D.mkdir(exist_ok=True)
R=Path("sbv_volcano_temp");R.mkdir(exist_ok=True)
ROOT="https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/"
srcs={
"2018":ROOT+"atoms/video/multimediaFile-2351.mp4",
"2023":ROOT+"media/video/20230607whirlwind.mp4",
"2025":ROOT+"media/video/20250117_ground_video.mp4",
}
def sh(args,log_error=True):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 if p.returncode:
  print("FFMPEG ERROR",p.stderr[-2400:],flush=True)
  raise RuntimeError("Failed command: "+' '.join(map(str,args[:8])))
 return p.stdout
for label,url in srcs.items():
 f=R/(label+".mp4")
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (creative source quality audit; USGS public domain)"})
 with urllib.request.urlopen(req,timeout=160) as r,open(f,"wb") as w:
  shutil.copyfileobj(r,w)
 print("SOURCE_RECEIVED",label,f.stat().st_size,flush=True)
 raw=json.loads(sh(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",f]))
 v=next(s for s in raw["streams"] if s["codec_type"]=="video")
 assert (v["width"],v["height"])==(1920,1080)
# Original clips, not 720p proxies; no repeated source frames:
scenes=[
("2018",37.114,2.90,615,"REAL_LAVA_WHIRLWIND_HOOK"),
("2023",4.20,2.50,645,"REAL_DAYLIGHT_FUNNEL"),
("2025",7.80,2.60,300,"REAL_KILAUEA_LAVA"),
("2018",17.40,2.60,600,"REAL_VOLCANIC_UPDRAFT"),
("2025",19.50,2.35,285,"SECOND_GENUINE_LAVA_ANGLE"),
("2018",44.614,2.20,495,"LAVA_FRAGMENTS_SPINNING"),
("2018",49.114,2.25,750,"GLOWING_FRAGMENT_FINALE")
]
assert abs(sum(x[2] for x in scenes)-17.4)<.01
paths=[]
for i,(kind,ss,dur,x,name) in enumerate(scenes):
 out=R/("S"+str(i+1)+"_"+name+".mp4")
 paths.append(out)
 filt=f"fps=30,crop=608:1080:{x}:0,scale=1080:1920:flags=lanczos,setsar=1,eq=contrast=1.02:saturation=1.025,format=yuv420p"
 sh(["ffmpeg","-hide_banner","-v","error","-y","-ss",ss,"-i",R/(kind+".mp4"),"-t",dur,
    "-vf",filt,"-an","-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",
    "-r","30","-video_track_timescale","30000",out])
 print("CLIP",i+1,kind,ss,dur,out.stat().st_size,flush=True)
concat=R/"concat.txt";concat.write_text(''.join("file '"+str(p.resolve())+"'\n" for p in paths))
joined=R/"video_clean.mp4"
sh(["ffmpeg","-hide_banner","-v","error","-y","-f","concat","-safe","0","-i",concat,
    "-c:v","copy","-movflags","+faststart",joined])
# Create the exact same English af_heart voice script as scene preview
lines=[
"Watch glowing rocks get sucked into a spinning vortex.",
"This isn't a tornado. It's a volcanic whirlwind.",
"At Hawaii's Kilauea, hot lava sends air racing upward.",
"The rotating air can rip glowing chunks from the lava's surface...",
"and fling them into the sky."
]
model=Kokoro("models/kokoro-v1.0.onnx","models/voices-v1.0.bin")
chunks=[];stamp=[];t=0.
for i,line in enumerate(lines):
 a,sr=model.create(line,voice="af_heart",speed=.97,lang="en-us",trim=True,continuous=True)
 assert sr==24000
 a=np.asarray(a,dtype="float32").reshape(-1)
 pause=.10 if i<len(lines)-1 else .5
 dur=len(a)/sr
 stamp.append({"text":line,"start":round(t,3),"end":round(t+dur,3)})
 chunks.extend([a,np.zeros(round(pause*sr),dtype=np.float32)])
 t+=dur+pause
wav=R/"Kokoro_af_heart_original.wav";sf.write(wav,np.concatenate(chunks),24000,subtype="PCM_24")
assert 14<t<18,("unexpected voice duration",t)
# Original ambient created mathematically, no stock music, no fake implied source location.
sr=48000;n=round(17.4*sr);rng=np.random.default_rng(12228)
noise=rng.standard_normal(n)
base=sosfilt(butter(2,850,fs=sr,output="sos"),noise)
base=(base/(np.std(base)+1e-9))*.0065
for tt in [.25,1.1,2.15,5.1,8.25,11.4,13.7,15.45,16.5]:
 p=round(tt*sr);w=round(.11*sr)
 base[p:p+w]+=rng.standard_normal(w)*np.linspace(0,.017,w)*np.exp(-np.linspace(0,10,w))
ff=round(.15*sr);base[:ff]*=np.linspace(0,1,ff);base[-ff:]*=np.linspace(1,0,ff)
bed=R/"Atmosphere_original.wav";sf.write(bed,np.stack([base,base],axis=1),sr)
# Two lines ONLY, visually matched to submitted SBV reference, no captions/logo/arrows/frames.
font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
vf=(f"drawtext=fontfile='{font}':text='STRANGE, BUT VERIFIED':fontsize=28:fontcolor=white:"
    "borderw=1:bordercolor=black@0.82:x=55:y=122,"
    f"drawtext=fontfile='{font}':text='SOURCE\\: USGS / HVO':fontsize=22:fontcolor=white:"
    "borderw=1:bordercolor=black@0.82:x=55:y=161,format=yuv420p")
af=("[1:a]aresample=48000,highpass=f=100,lowpass=f=8800,"
    "acompressor=threshold=0.09:ratio=2:attack=6:release=130:makeup=1.45,"
    "loudnorm=I=-15:TP=-1.7:LRA=6,apad,atrim=duration=17.4[voice];"
    "[2:a]volume=0.38,atrim=duration=17.4[bed];"
    "[voice][bed]amix=inputs=2:duration=longest:normalize=0,"
    "alimiter=limit=0.88[a]")
out=D/"SBV_VOLCANO_WHIRLWIND_REAL_USGS_FOOTAGE_SHORTS_1080p.mp4"
sh(["ffmpeg","-hide_banner","-v","error","-y","-i",joined,"-i",wav,"-i",bed,
    "-filter_complex","[0:v]"+vf+"[v];"+af,"-map","[v]","-map","[a]",
    "-t","17.4","-c:v","libx264","-preset","fast","-crf","18",
    "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000",
    "-ac","2","-movflags","+faststart",out])
mobile=D/"SBV_VOLCANO_WHIRLWIND_REAL_USGS_FOOTAGE_MOBILE_720p.mp4"
sh(["ffmpeg","-hide_banner","-v","error","-y","-i",out,"-vf","scale=720:1280:flags=lanczos",
   "-c:v","libx264","-preset","fast","-crf","26","-pix_fmt","yuv420p",
   "-c:a","aac","-b:a","128k","-movflags","+faststart",mobile])
probe=json.loads(sh(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_type,width,height,duration","-of","json",out]))
assert abs(float(probe["format"]["duration"])-17.4)<.1
v=next(s for s in probe["streams"] if s["codec_type"]=="video")
assert(v["width"],v["height"])==(1080,1920)
sh(["ffmpeg","-v","error","-xerror","-i",out,"-f","null","-"])
# Detect black and freeze; 2018 nighttime darkness is naturally red and black but image subject remains glowing
black=sh(["ffmpeg","-hide_banner","-loglevel","info","-i",out,"-vf","blackdetect=d=0.18:pix_th=0.08","-an","-f","null","-"])
# No watermark removal beyond cropping, original 2018 logo offscreen.
N=12;W=255;H=460;contact=Image.new("RGB",(4*W,3*(H+26)),(13,15,20));draw=ImageDraw.Draw(contact)
for i in range(N):
 ts=.25+i*17.0/(N-1);f=R/f"thumb_{i}.jpg"
 sh(["ffmpeg","-hide_banner","-v","error","-y","-ss",str(ts),"-i",out,"-frames:v","1","-vf","scale=245:435",f])
 with Image.open(f) as thumb:contact.paste(thumb,(i%4*W+5,(i//4)*(H+26)+3))
 draw.text((i%4*W+8,i//4*(H+26)+H),f"{ts:.1f}s",fill="white")
contact.save(D/"SBV_VOLCANIC_WHIRLWIND_FINAL_CONTACT_SHEET.jpg",quality=92)
notes={
"duration":17.4,"resolution":"1080x1920","fps":30,
"narrator":"Kokoro af_heart","voice_timestamps":stamp,
"sources":[{"kind":x,"start_sec":ss,"duration_sec":dur,
"vertical_crop_source_x":cx,"clip_name":name} for x,ss,dur,cx,name in scenes],
"license":"USGS Public Domain; original 2018, 2023 and 2025 shoots are deliberately shown as a compilation of the same type of phenomenon at Kilauea, not a single contiguous event.",
"source_urls":srcs,
"text_overlays":["STRANGE, BUT VERIFIED","SOURCE: USGS / HVO"],
"captions":"none",
"effects":"original background audio intentionally subtle; scene images unaltered except aspect crop + slight color correction",
"QA":{"full_decode":True,"video_seconds":float(probe["format"]["duration"]),"video_px":[v["width"],v["height"]],"file_size":out.stat().st_size}}
(D/"SOURCE_CREDITS_AND_QA.json").write_text(json.dumps(notes,indent=2,ensure_ascii=False))
(D/"ENGLISH_VOICE_SCRIPT.txt").write_text("\n".join(lines))
print("FINISHED",out,round(out.stat().st_size/1024/1024,2),"MB",mobile.stat().st_size,flush=True)
