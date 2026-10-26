#!/usr/bin/env python3
"""Strange, But Verified: authentic-footage documentary editor.
No fake science footage; strict source validation; chapters from approved Kokoro source.
"""
from __future__ import annotations
import ast, hashlib, json, math, os, random, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT=Path.cwd()
SRC=ROOT/"media_zombie_ant"
SEG=ROOT/"video_segments"
OUT=ROOT/"video_output"
for d in (SRC,SEG,OUT):d.mkdir(exist_ok=True)
random.seed(20261026)
SOURCES={
 "research_zombie": {
  "url":"https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2F1472-6785-11-13/MediaObjects/12898_2011_173_MOESM2_ESM.MP4",
  "credit":"Hughes et al., BMC Ecology 2011 - CC BY 2.0",
  "scientific":True, "required":True },
 "research_healthy":{
  "url":"https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2F1472-6785-11-13/MediaObjects/12898_2011_173_MOESM1_ESM.MP4",
  "credit":"Hughes et al., BMC Ecology 2011 - CC BY 2.0",
  "scientific":True, "required":True },
 "real_ants_leaves":{
  "url":"https://videos.pexels.com/video-files/7085345/7085345-hd_1920_1080_25fps.mp4",
  "credit":"Olena Ilinska - Pexels - illustrative footage",
  "scientific":False, "required":False },
 "real_ant_plant":{
  "url":"https://videos.pexels.com/video-files/3809370/3809370-hd_1920_1080_30fps.mp4",
  "credit":"Ozone Jeydin - Pexels - illustrative footage",
  "scientific":False, "required":False },
 "leafcutter_ants":{
  "url":"https://videos.pexels.com/video-files/4570611/4570611-hd_1920_1080_30fps.mp4",
  "credit":"Gilmer Diaz Estela - Pexels - illustrative footage",
  "scientific":False, "required":False },
 "mushrooms_other_species":{
  "url":"https://videos.pexels.com/video-files/3229028/3229028-hd_1920_1080_24fps.mp4",
  "credit":"Chris Gonzalez - Pexels - OTHER FUNGAL SPECIES, illustrative",
  "scientific":False, "required":False },
 "ant_colony":{
  "url":"https://videos.pexels.com/video-files/5469094/5469094-hd_1920_1080_24fps.mp4",
  "credit":"K - Pexels - illustrative footage",
  "scientific":False, "required":False },
}
def run(args,check=True,quiet=False):
 p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode and check:
  raise RuntimeError("Command failed: "+" ".join(map(str,args[:8]))+"\n"+p.stderr[-2800:])
 if not quiet: print("CMD",str(args[:5]),"return",p.returncode,flush=True)
 return p

def probe(path):
 p=run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(path)],quiet=True)
 data=json.loads(p.stdout)
 if not any(s.get("codec_type")=="video" for s in data.get("streams",[])):raise ValueError("Missing video")
 duration=float(data.get("format",{}).get("duration",0))
 if duration<3:raise ValueError("Video shorter than 3s")
 return duration

def download(source_id,meta):
 dest=SRC/(source_id+".mp4")
 if dest.exists():
  try:return dest,probe(dest)
  except Exception:dest.unlink()
 err=""
 for attempt in range(3):
  try:
   req=urllib.request.Request(meta["url"],headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36","Accept":"*/*"})
   with urllib.request.urlopen(req,timeout=65) as r,open(dest,"wb") as out:
    shutil.copyfileobj(r,out,1024*1024)
   if dest.stat().st_size<30000:raise ValueError("tiny download")
   dur=probe(dest)
   print("DOWNLOADED",source_id,dest.stat().st_size,round(dur,2),flush=True)
   return dest,dur
  except Exception as e:
   err=str(e);print("FETCH",source_id,"attempt",attempt+1,err[:220],flush=True)
   if dest.exists():dest.unlink()
   time.sleep(2)
 if meta["required"]:raise RuntimeError("Required primary research footage failed: "+source_id+" "+err)
 return None,None

available={}
for key,meta in SOURCES.items():
 file,duration=download(key,meta)
 if file:available[key]={"path":file,"duration":duration,**meta}
if len(available)<4:raise RuntimeError("Insufficient diverse authentic footage; refusing to create placeholder MP4")
voice=ROOT/"output"/"SBV_ZOMBIE_ANT_KOKORO_AF_HEART_MASTER.wav"
timing=ROOT/"output"/"chapter_timing.json"
if not voice.exists() or not timing.exists():raise RuntimeError("Kokoro must successfully synthesize audio first")
chapters=json.loads(timing.read_text())
# Re-use EXACT speech script from previous, already-approved continuous-chapter Kokoro generator
tree=ast.parse((ROOT/"narrate.py").read_text(encoding="utf8"))
chapnode=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="chapters" for t in n.targets))
approved=ast.literal_eval(chapnode.value)
assert len(approved)==len(chapters)==7
for (name,script),record in zip(approved,chapters):assert name==record["chapter"]
voice_len=float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(voice)],quiet=True).stdout.strip())
if not 175 < voice_len < 370:raise RuntimeError("Unexpected Kokoro voice duration: "+str(voice_len))
print("NARRATION LENGTH",voice_len,flush=True)

# True 16:9 source layout, without stretching. No synthetic images.
W,H,FPS=1920,1080,30
preferences=[
 ["research_zombie","real_ant_plant","research_zombie","real_ants_leaves"],
 ["research_healthy","ant_colony","real_ants_leaves","leafcutter_ants","real_ant_plant"],
 ["real_ant_plant","research_healthy","real_ants_leaves","ant_colony","leafcutter_ants"],
 ["research_zombie","real_ant_plant","research_zombie","research_healthy","real_ants_leaves"],
 ["real_ants_leaves","research_healthy","ant_colony","research_zombie","leafcutter_ants"],
 ["mushrooms_other_species","real_ants_leaves","research_zombie","ant_colony","mushrooms_other_species"],
 ["research_zombie","real_ant_plant","research_zombie","mushrooms_other_species"]
]
chapter_titles=["THE INFECTION BEGINS","INSIDE THE HOST","THE FINAL CLIMB","THE DEATH GRIP","THE IMPOSSIBLE DISCOVERY","AFTER DEATH","THE FINAL TWIST"]
def pick(prefs,i):
 valid=[x for x in prefs if x in available]
 if not valid:return "research_zombie"
 return valid[i%len(valid)]
def filter_for(sc,chapter_name="",research=False):
 if sc["scientific"]:
  label="RESEARCH FOOTAGE  -  HUGHES ET AL. 2011"
 else:
  label="ILLUSTRATIVE FOOTAGE  -  NOT AN INFECTED ANT"
 font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
 # subtle dark border on sides for 4:3 primary footage, never distort it
 vf="scale=1920:1080:force_original_aspect_ratio=decrease," \
    "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x07100c,setsar=1,fps=30,format=yuv420p"
 vf+=f",drawtext=fontfile={font}:text='{label}':fontsize=19:fontcolor=white@0.92:x=40:y=35:box=1:boxcolor=black@0.35:boxborderw=10"
 if chapter_name:
  vf+=f",drawtext=fontfile={font}:text='{chapter_name}':fontsize=36:fontcolor=white:x=44:y=95:shadowcolor=black@0.8:shadowx=2:shadowy=2:enable='lt(t,2.1)'"
 return vf

# Build precisely the duration of actual narration. Edits every 3.4-5.3s.
edits=[]; cursor=0.0
for ci,record in enumerate(chapters):
 chapter_start=float(record["start_sec"])
 chapter_end=float(record["end_sec"])
 if cursor<chapter_start-0.1:
  cursor=chapter_start
 while cursor < chapter_end-0.20:
  shot_no=len(edits)
  length=min(4.15+(shot_no%5)*0.25,chapter_end-cursor)
  if length<0.65:break
  key=pick(preferences[ci],shot_no)
  asset=available[key]
  max_start=max(0.0,asset["duration"]-length-0.03)
  start=(shot_no*3.107+(ci+1)*1.83)%max(max_start,0.001)
  edits.append(dict(source=key,source_start=round(start,2),length=round(length,3),
   chapter=ci,chapter_title=chapter_titles[ci] if cursor-chapter_start<0.45 else "",
   at=round(cursor,3)))
  cursor+=length
 # chapter pauses bridged with non-intrusive healthy ant / forest footage
 if ci < len(chapters)-1:
  next_start=float(chapters[ci+1]["start_sec"])
  if next_start>cursor:
   key=pick(["real_ants_leaves","real_ant_plant","mushrooms_other_species","research_healthy"],ci)
   asset=available[key]
   edits.append(dict(source=key,source_start=0.0,length=round(next_start-cursor,3),chapter=ci,chapter_title="",at=round(cursor,3)))
   cursor=next_start
end_delta=voice_len-cursor
if end_delta>0.10:
 edits.append(dict(source="research_zombie",source_start=3.0,length=round(end_delta+0.05,3),chapter=6,chapter_title="",at=round(cursor,3)))
if len(edits)<25:raise RuntimeError("Scene map too short")
print("CUTS",len(edits),flush=True)
for i,ed in enumerate(edits):
 source=available[ed["source"]]
 seg=SEG/f"{i:04d}.mp4"
 vf=filter_for(source,ed["chapter_title"])
 # exact frames avoid concat stream drift
 frames=round(ed["length"]*FPS)
 args=["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(ed["source_start"]),
       "-i",str(source["path"]),"-an","-vf",vf,"-frames:v",str(frames),"-c:v","libx264",
       "-preset","veryfast","-crf","24","-pix_fmt","yuv420p","-r","30",
       "-video_track_timescale","30000",str(seg)]
 run(args,quiet=True)
 if (i+1)%10==0:print("RENDERED",i+1,"/",len(edits),flush=True)
(OUT/"edl.json").write_text(json.dumps(edits,indent=2))
(OUT/"sources.json").write_text(json.dumps({k:{kk:vv for kk,vv in v.items() if kk not in ("path",)} for k,v in available.items()},indent=2,default=str))
manifest=OUT/"concat.txt"
manifest.write_text("".join(f"file '{SEG/f'{i:04d}.mp4'}'\n" for i in range(len(edits))))

# Caption spans calculated from Kokoro chapter timing; 2 lines max, no black background.
def blocks(text,max_words=10,max_chars=66):
 words=re.sub(r"\s+"," ",text.strip()).split()
 parts=[];group=[]
 for w in words:
  if len(group)>=max_words or (len(" ".join(group))+len(w)+1>max_chars and len(group)>=4):
   parts.append(" ".join(group));group=[]
  group.append(w)
 if group:parts.append(" ".join(group))
 return parts
def fmt(t):
 ms=max(0,int(round(t*1000)))
 h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f"{h:02}:{m:02}:{s:02},{ms:03}"
cues=[];seq=1
for (_,script),rec in zip(approved,chapters):
 spans=blocks(script)
 weights=[max(5.0,len(s)**0.85) for s in spans]
 total=sum(weights);at=float(rec["start_sec"]);duration=float(rec["end_sec"])-at
 for j,(span,wt) in enumerate(zip(spans,weights)):
  end=at+duration*wt/total if j<len(spans)-1 else float(rec["end_sec"])
  words=span.split()
  if len(span)>43:
   mid=min(range(2,len(words)-1),key=lambda k:abs(len(" ".join(words[:k]))-len(span)/2))
   span=" ".join(words[:mid])+"\n"+" ".join(words[mid:])
  cues.append((at,end,span))
  at=end
srt=OUT/"captions_en.srt"
srt.write_text("".join(f"{i}\n{fmt(a)} --> {fmt(b)}\n{txt}\n\n" for i,(a,b,txt) in enumerate(cues,1)),encoding="utf8")
# burn captions; no filled subtitle box. Normalized original Kokoro voice.
master=OUT/"SBV_ZOMBIE_ANT_KOKORO_AF_HEART_MASTER.mp4"
subtitle_filter=f"subtitles={srt}:force_style='FontName=DejaVu Sans,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00202020,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=65'"
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-safe","0","-f","concat","-i",str(manifest),
     "-i",str(voice),"-map","0:v:0","-map","1:a:0",
     "-vf",subtitle_filter,"-af","loudnorm=I=-15:TP=-1.5:LRA=9",
     "-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","192k","-ar","48000",
     "-r","30","-t",f"{voice_len:.3f}","-movflags","+faststart",str(master)])
run(["ffmpeg","-v","error","-xerror","-i",str(master),"-f","null","-"],quiet=True)
pr=run(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate","-of","json",str(master)],quiet=True)
qa=json.loads(pr.stdout);qa["source_count"]=len(available);qa["shot_count"]=len(edits);qa["caption_cues"]=len(cues);qa["voice"]="Kokoro 82M v1.0 af_heart speed 0.88";qa["source_rights"]="BMC Ecology CC BY 2.0 and Pexels License";qa["full_decode"]="PASS";qa["real_image_only"]=True
(OUT/"qa.json").write_text(json.dumps(qa,indent=2))
(OUT/"CREDITS.txt").write_text(
 "STRANGE, BUT VERIFIED - THE FUNGUS THAT TURNS ANTS INTO ZOMBIES\n\n"+
 "Research footage from Hughes, Andersen, Hywel-Jones, Himaman, Billen, Boomsma (2011), BMC Ecology 11:13, DOI 10.1186/1472-6785-11-13, CC BY 2.0. https://creativecommons.org/licenses/by/2.0/\n"+
 "Video edited, cut, cropped / padded and captioned for this documentary.\n\n"+
 "All other shots are real-world illustrative footage of other ant/fungus species and are labeled as illustrative in the film.\n"+
 "\n".join(f"{k}: {v['credit']}" for k,v in available.items())+
 "\n\nNarration: Kokoro-82M v1.0 af_heart, original synthesized voice.\nNo BBC footage, AI-generated animal footage or copyrighted academic figures were used.\n\n"+
 "Scientific references: Fredericksen et al. PNAS (2017) 10.1073/pnas.1711673114; Mangold et al. JEB (2019).\n")
print("MASTER",master,"bytes",master.stat().st_size,"duration",qa.get("format",{}).get("duration"),flush=True)
