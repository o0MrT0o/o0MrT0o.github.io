#!/usr/bin/env python3
"""Strict real-video/zero-replayed-clips documentary renderer for Strange But Verified."""
import hashlib,json,math,os,shutil,subprocess,time,urllib.request
from pathlib import Path

ROOT=Path.cwd();MEDIA=ROOT/"footage";OUT=ROOT/"documentary";PARTS=ROOT/"documentary_parts"
for d in (MEDIA,OUT,PARTS):d.mkdir(exist_ok=True)
FPS=30;W=1920;H=1080
STUDY_BASE="https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2F1472-6785-11-13/MediaObjects/"
def pex(id,fps):return f"https://videos.pexels.com/video-files/{id}/{id}-hd_1920_1080_{fps}fps.mp4"
def pex720(id,fps):return f"https://videos.pexels.com/video-files/{id}/{id}-hd_1280_720_{fps}fps.mp4"
S={
 "research_zombie":(STUDY_BASE+"12898_2011_173_MOESM2_ESM.MP4","Hughes et al. 2011, BMC Ecology, CC BY 2.0",True),
 "research_healthy":(STUDY_BASE+"12898_2011_173_MOESM1_ESM.MP4","Hughes et al. 2011, BMC Ecology, CC BY 2.0",True),
 "ants_on_leaves":(pex("7085345",25),"Olena Ilinska, Pexels, unrelated ant footage",False),
 "ant_plant":(pex("3809370",30),"Ozone Jeydin, Pexels, unrelated ant footage",False),
 "ants_swarming":(pex("5019583",30),"Cesar A Ramirez Vallejo, Pexels, unrelated ant footage",False),
 "weaver_ants":(pex("4113098",30),"My Walking Diary, Pexels, weaver ants",False),
 "leafcutter":(pex("4570611",30),"Gilmer Diaz Estela, Pexels, leafcutter ants",False),
 "leaf_carrier":(pex("13539737",30),"Cesar A Ramirez Vallejo, Pexels, leaf-carrying ant",False),
 "grass_ants":(pex("4168987",25),"Wendy Laplume, Pexels, unrelated ants",False),
 "fire_ants":(pex("5469107",24),"K, Pexels, unrelated fire ants",False),
 "carcass_ants":(pex("4200220",30),"Aarif Patel, Pexels, unrelated ants",False),
 "black_ants":(pex("10008763",30),"Peggy Anke, Pexels, unrelated black ants",False),
 "ant_colony1":(pex("5469094",24),"K, Pexels, unrelated red ant colony",False),
 "ant_colony2":(pex("5019581",30),"Cesar A Ramirez Vallejo, Pexels, unrelated ant colony",False),
 "small_colony":(pex("2454368",30),"Joel Dunn, Pexels, unrelated ant colony",False),
 "mushrooms":(pex("9768059",30),"Cesar Casanova, Pexels, unrelated mushrooms",False),
 "mushroom_timelapse":(pex("3229028",24),"Chris Gonzalez, Pexels, unrelated mushroom species",False),
 "moss":(pex720("3239843",50),"The Marc Knight, Pexels, moss-covered forest logs",False),
 "forestlog":(pex("5738798",24),"Pat Whelen, Pexels, live forest log footage",False),
 "red_mushroom":(pex720("3239815",50),"The Marc Knight, Pexels, fly agaric (not Ophiocordyceps)",False),
}
STORY=[
 ["research_zombie","ants_on_leaves","ant_plant"],
 ["research_healthy","ants_swarming","weaver_ants"],
 ["leafcutter","leaf_carrier","grass_ants"],
 ["fire_ants","carcass_ants","black_ants"],
 ["ant_colony1","ant_colony2","small_colony"],
 ["mushrooms","mushroom_timelapse","moss"],
 ["forestlog","red_mushroom"],
]
assert len(set(sum(STORY,[])))==sum(map(len,STORY))==len(S), "A source is reused in the montage!"
def shell(cmd,quiet=False):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode!=0:raise RuntimeError("Command "+str(cmd[:8])+" failed:\n"+p.stderr[-1800:])
 if not quiet:print("OK",str(cmd[:5]),flush=True)
 return p.stdout.strip()
def ffprobe(path):
 o=shell(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)],True)
 v=json.loads(o);duration=float(v.get("format",{}).get("duration",0))
 videos=[t for t in v["streams"] if t["codec_type"]=="video"]
 if not videos or duration<2.7:raise RuntimeError("Not moving video or too short: "+str(path))
 return duration
def download(url,path):
 err=None
 for retry in range(3):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36","Accept":"*/*"})
   with urllib.request.urlopen(req,timeout=85) as response,open(path,"wb") as f:
    shutil.copyfileobj(response,f,1024*1024)
   if path.stat().st_size<25000:raise RuntimeError("file too small")
   return
  except Exception as e:
   err=str(e);print("download error",url[:110],repr(err),retry,flush=True)
   if path.exists():path.unlink()
   time.sleep(1)
 raise RuntimeError("Failed media download: "+url+" error: "+str(err))

footage={}
for key,(url,credit,scientific) in S.items():
 path=MEDIA/(key+".mp4")
 if not path.exists():download(url,path)
 length=ffprobe(path)
 footage[key]={"path":path,"length":length,"credit":credit,"research":scientific,"url":url,
               "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
 print("VALID VIDEO",key,round(length,2),"s",path.stat().st_size,"bytes",flush=True)
# No two video files may contain the same bytes even when renamed!
hashes=[v["sha256"] for v in footage.values()]
assert len(hashes)==len(set(hashes)), "The same recorded video was supplied under two filenames"
wav=ROOT/"output"/"SBV_ZOMBIE_ANT_KOKORO_AF_HEART_MASTER.wav"
marksfile=ROOT/"output"/"chapter_timing.json"
scriptfile=ROOT/"sbv_chapters.json"
if not wav.exists() or not marksfile.exists() or not scriptfile.exists():raise RuntimeError("Narrator artifact and chapter script needed")
marks=json.loads(marksfile.read_text());chapters=json.loads(scriptfile.read_text())
assert len(marks)==len(chapters)==len(STORY)
voice_length=float(shell(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(wav)],True))
assert 160<voice_length<370,voice_length
endframe=round(voice_length*FPS)
edl=[];prior=0
for c,ids in enumerate(STORY):
 actual_names=[q for q in ids if q in footage]
 assert len(actual_names)==len(ids)
 chap_end=round((marks[c+1]["start_sec"] if c+1<len(marks) else voice_length)*FPS)
 target=chap_end-prior
 caps={k:max(0,int((footage[k]["length"]-0.25)*FPS)) for k in ids}
 if sum(caps.values())<target:raise RuntimeError(f"Chapter {c}: unique footage shortage {sum(caps.values())/FPS:.2f} < {target/FPS:.2f}")
 # Water-fill duration fairly, up to each source's *unused* complete original recording limit.
 # One contiguous, distinct source section per footage file in the entire film.
 sizes={k:0 for k in ids}
 left=target
 while left>0:
  candidates=[k for k in ids if sizes[k]<caps[k]]
  if not candidates:raise RuntimeError("unique-frames constraint violated")
  # Place additional seconds into the least-used clip first: good natural pacing.
  k=min(candidates,key=lambda q:(sizes[q]/min(caps[q],int(20*FPS)), ids.index(q)))
  chunk=min(left,caps[k]-sizes[k],FPS)
  sizes[k]+=chunk;left-=chunk
 for k in ids:
  frames=sizes[k]
  if frames<30:raise RuntimeError(f"Reject unnaturally short shot: {k} {frames/FPS:.2f}s")
  # take one contiguous sequence of footage; never return to the same recording later.
  available=caps[k]/FPS
  target_seconds=frames/FPS
  from_sec=max(0,(footage[k]["length"]-target_seconds)/2)
  edl.append({"chapter":c,"file_id":k,"source_in":round(from_sec,4),"frames":frames,
   "duration":frames/FPS,"at":prior/FPS,"credit":footage[k]["credit"],"scientific":footage[k]["research"]})
  prior+=frames
assert prior==endframe,(prior,endframe)
assert len(set(x["file_id"] for x in edl))==len(edl)==len(S)
assert abs(sum(x["duration"] for x in edl)-voice_length)<0.05
(OUT/"NO_REPEAT_EDL.json").write_text(json.dumps(edl,indent=2))
print("HARD AUDIT",len(edl),"unique source videos, NO SOURCE REPLAY, total",round(prior/FPS,2),flush=True)

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LABEL_RESEARCH="ORIGINAL FIELD STUDY  /  HUGHES ET AL. 2011"
LABEL_STOCK="ILLUSTRATIVE  /  DIFFERENT SPECIES"
# Only dynamic movie footage is allowed: each chapter is composed of native video frames.
for i,ed in enumerate(edl):
 k=ed["file_id"];path=footage[k]["path"]
 label=LABEL_RESEARCH if ed["scientific"] else LABEL_STOCK
 # No full-screen chapter cards or images; minimal temporary source identifier over moving video.
 vf=(f"scale=1920:1080:force_original_aspect_ratio=decrease,"
     f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x121913,setsar=1,"
     f"fps=30,eq=contrast=1.04:saturation=0.9,format=yuv420p,"
     f"drawtext=fontfile={FONT}:text='{label}':fontsize=18:"
     f"fontcolor=white@0.85:x=42:y=36:box=1:boxcolor=black@0.25:"
     f"boxborderw=7:enable='between(t,0,1.7)'")
 out=PARTS/f"{i:03}.mp4"
 shell(["ffmpeg","-hide_banner","-loglevel","error","-y",
       "-ss",str(ed["source_in"]),"-i",str(path),
       "-an","-vf",vf,"-frames:v",str(ed["frames"]),"-c:v","libx264",
       "-preset","superfast","-crf","22","-pix_fmt","yuv420p",
       "-video_track_timescale","30000","-r","30",str(out)],True)
 if (i+1)%4==0:print("VIDEO CUTS",i+1,"/",len(edl),flush=True)
concat=OUT/"concat.txt"
concat.write_text("".join("file '"+str((PARTS/f"{i:03}.mp4").resolve())+"'\n" for i in range(len(edl))))

def srt_time(t):
 n=max(0,int(round(t*1000)));hr,n=divmod(n,3600000);mi,n=divmod(n,60000);se,ms=divmod(n,1000)
 return f"{hr:02}:{mi:02}:{se:02},{ms:03}"
def groups(text):
 import re
 w=re.sub(r"\s+"," ",text).split();p=[];c=[]
 for z in w:
  if len(c)>=10 or len(" ".join(c+[z]))>68 and len(c)>=4:
   p.append(" ".join(c));c=[]
  c.append(z)
 if c:p.append(" ".join(c))
 return p
subs=[];counter=1
for c,(ch,mark) in enumerate(zip(chapters,marks)):
 assert ch["name"]==mark["chapter"],(ch["name"],mark["chapter"])
 blocks=groups(ch["text"])
 st=float(mark["start_sec"]);en=float(mark["end_sec"])
 weights=[max(1,len(b)) for b in blocks];summ=sum(weights)
 cur=st
 for j,b in enumerate(blocks):
  final=en if j==len(blocks)-1 else cur+(en-st)*weights[j]/summ
  # Readable two-line max, and optionally enable SRT at YouTube upload, not burned into footage.
  words=b.split()
  if len(b)>43:
   mid=min(range(2,len(words)-1),key=lambda k:abs(len(" ".join(words[:k]))-len(b)/2))
   b=" ".join(words[:mid])+"\n"+" ".join(words[mid:])
  subs.append(f"{counter}\n{srt_time(cur)} --> {srt_time(final)}\n{b}\n\n")
  counter+=1;cur=final
(OUT/"SUBTITLES_EN.srt").write_text("".join(subs))

# Two licensed real sound recordings, neither fabricated.
AUDIO={
 "music":("https://upload.wikimedia.org/wikipedia/commons/6/6d/John_Bartmann_-_dark-highway-master.ogg",
          "John Bartmann - dark-highway-master.ogg - CC0 1.0"),
 "forest":("https://upload.wikimedia.org/wikipedia/commons/0/0a/20090610_0_ambience.ogg",
           "nille - 20090610 0 ambience.ogg - public domain"),
}
for name,(url,credit) in AUDIO.items():
 path=MEDIA/(name+".ogg")
 if not path.exists():download(url,path)
 shell(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],True)
print("SCORE AND FOREST RECORDING VERIFIED",flush=True)
master=OUT/"SBV_ZOMBIE_ANT_DOCUMENTARY_NO_REPEATS_MASTER.mp4"
# The forest ambience is deliberately used only once (not looped).
# Music is four minutes and is played once, not looped; voice sets final duration.
fa="[1:a]aresample=48000,volume=1.0[voice];[2:a]aresample=48000,volume=0.105,afade=t=in:st=0:d=2[music];[3:a]aresample=48000,volume=0.085,afade=t=in:st=0:d=3[forest];[voice][music][forest]amix=inputs=3:duration=first:dropout_transition=2,loudnorm=I=-15:TP=-1.5:LRA=9[final]"
shell(["ffmpeg","-hide_banner","-loglevel","error","-y","-safe","0","-f","concat","-i",str(concat),
 "-i",str(wav),"-i",str(MEDIA/"music.ogg"),"-i",str(MEDIA/"forest.ogg"),
 "-filter_complex",fa,"-map","0:v:0","-map","[final]",
 "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-r","30",
 "-c:a","aac","-b:a","192k","-ar","48000",
 "-movflags","+faststart","-t",f"{voice_length:.5f}",str(master)])
# Machine verification: exact output exists; every video frame decodes.
shell(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",str(master),"-f","null","-"],True)
info=json.loads(shell(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(master)],True))
video=next(x for x in info["streams"] if x["codec_type"]=="video")
audio=next(x for x in info["streams"] if x["codec_type"]=="audio")
assert (video["width"],video["height"])==(1920,1080)
assert audio["codec_name"]=="aac"
assert float(info["format"]["duration"])>170
assert master.stat().st_size>10000000
qa={"status":"PASS","file":master.name,"duration_sec":float(info["format"]["duration"]),
 "size_bytes":master.stat().st_size,"resolution":"1920x1080","fps":30,
 "video_source_files":len(S),"used_source_files":len(edl),
 "source_clip_repeat_count":0,"source_time_overlap_count":0,
 "visuals":"100% authentic moving video files, no still image, no generated footage",
 "narration":"Kokoro-82M v1.0, af_heart speed 0.88, original wave reused",
 "subtitles":"separate SRT, optional - no permanent YouTube-style captions",
 "music":"John Bartmann dark-highway-master CC0 1.0 (no loop)",
 "ambience":"nille forest natural field recording public domain (no loop)",
 "machine_full_decode":"PASS",
 "audio_codec":"AAC","video_codec":"H264"}
(OUT/"QA_NO_REPEATS.json").write_text(json.dumps(qa,indent=2))
sources=["Hughes, Andersen, Hywel-Jones, Himaman, Billen, Boomsma (2011), BMC Ecology 11:13, https://doi.org/10.1186/1472-6785-11-13, CC BY 2.0, trimmed/adapted with original research credit.","All non-research insect and fungus footage is of unrelated species, sourced from Pexels, cut/color-adjusted for editorial educational use. https://www.pexels.com/license/"]
sources.extend(k+": "+v["credit"]+" | "+v["url"] for k,v in footage.items())
sources.extend("Audio "+k+": "+v[1]+" | "+v[0] for k,v in AUDIO.items())
sources.extend(["Science: Fredericksen et al. (2017) PNAS https://doi.org/10.1073/pnas.1711673114 ; findings paraphrased, no copyrighted microscopy figures displayed.","Science: Mangold et al. (2019) Journal of Experimental Biology."])
(OUT/"SOURCE_RIGHTS_AND_CREDITS.txt").write_text("\n".join(sources)+"\n")
print("SUCCESS",json.dumps(qa,indent=2),flush=True)
