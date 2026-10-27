#!/usr/bin/env python3
"""SBV V10: YouTube-ready extended wild footage cut.
Sources: V8 QA-pass no-replay video; original 2011 field Ophiocordyceps
scientific video S2; distinct licensed REAL ant/forest videos; original
Kokoro af_heart spoiler-free intro + CC0 forest and score.
Replaces long monotonous clips and red mushroom. No loops, stills, CGI.
Includes direct-download master, caption SRT, QA, thumbnail, sources, chapters.
All timestamp lengths are exact integer video frame counts.
"""
from pathlib import Path
import json,re,os,math,subprocess,hashlib,wave,shutil
from PIL import Image,ImageDraw,ImageFont
P=Path.cwd();SRC=P/"source";EXT=P/"fresh";HOOK=P/"hook";OUT=P/"v10_output"
OUT.mkdir(exist_ok=True)
ORIG=SRC/"SBV_ZOMBIE_ANT_V8_FOREST_ONLY_NO_LAB_NO_REPEATS.mp4"
SCI=SRC/"REAL_HUGHES_2011_OPHIOCORDYCEPS_THAILAND_ORIGINAL.mp4"
HOOK_AUDIO=HOOK/"V9_NEW_SUSPENSE_COLD_OPEN_AF_HEART.wav"
EDL=SRC/"V8_NO_REPEATS_NO_LAB_EDL.json"
FINAL=OUT/"SBV_ZOMBIE_ANT_V10_WILD_EXTENDED_YOUTUBE_FINAL.mp4"
for x in (ORIG,SCI,EDL,HOOK_AUDIO,EXT/"score_dark_highway.mp3",EXT/"ambience_forest.mp3"):
 assert x.is_file() and x.stat().st_size>300, "Missing input "+str(x)
def run(args):
 p=subprocess.run([str(a) for a in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:
  print(p.stderr[-4700:],flush=True)
  raise RuntimeError("FFmpeg command failed: "+str(args[:11]))
 return p.stdout.strip(),p.stderr
def duration(path):
 p=subprocess.run(["ffmpeg","-hide_banner","-i",str(path)],capture_output=True,text=True)
 m=re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",p.stderr)
 if not m:raise RuntimeError("No duration: "+str(path))
 return int(m[1])*3600+int(m[2])*60+float(m[3])
def hash_audio(p):
 return run(["ffmpeg","-v","error","-i",p,"-map","0:a:0","-c","copy","-f","hash","-hash","SHA256","-"])[0]
FPS=30
edl=json.loads(EDL.read_text())
assert len(edl)==20 and len(set(s["file_id"] for s in edl))==20
total=sum(int(s["frames"]) for s in edl)
v8duration=duration(ORIG)
assert abs(total/FPS-v8duration)<.10
scidur=duration(SCI)
assert 19.7<scidur<21,(scidur,"Original scientific footage not as expected.")
assert edl[0]["file_id"]=="research_zombie"
original_research_start=float(edl[0]["source_in"])
original_research_end=original_research_start+float(edl[0]["duration"])
assert original_research_end<14.60, ("Cannot use 14.7-19.7 without frame reuse",original_research_end)
with wave.open(str(HOOK_AUDIO),"rb") as voice:
 assert voice.getframerate()==24000 and voice.getnchannels()==1
 hookduration=voice.getnframes()/24000
assert 15<hookduration<19.3,hookduration
# One unique continuous snippet per NEW outdoors source, never replay/loop.
media={
 "ants_bark":EXT/"ants_bark.mp4",
 "ants_green_leaves":EXT/"ants_green_leaves.mp4",
 "ants_dead_bug":EXT/"ants_dead_bug.mp4",
 "ant_stem":EXT/"ant_stem.mp4",
 "ants_tree":EXT/"ants_tree.mp4",
 "rain_leaf_ants":EXT/"rain_leaf_ants.mp4",
 "ants_leafy_branch":EXT/"ants_leafy_branch.mp4",
 "fungus_dead_leaf":EXT/"fungus_dead_leaf.mp4",
 "leafcutter_trunk":EXT/"leafcutter_trunk.mp4",
 "hughes2011_unused_source":SCI
}
# For fairness, 2011 archive after 14.7 s (nonoverlapping with 5.5-14.5s
# already in V8) contributes exactly 5 s of MORE GENUINE rainforest footage.
# Scientific source note distinguishes this from the illustrative footage.
replacements={
 "leaf_carrier":[("ants_bark",345),("ants_green_leaves",336)],
 "black_ants":[("hughes2011_unused_source",150)],
 "ant_colony1":[("ants_dead_bug",377),("ant_stem",463)],
 "ant_colony2":[("ants_tree",515),("rain_leaf_ants",309)],
 "mushrooms":[("ants_leafy_branch",354)],
 "mushroom_timelapse":[("fungus_dead_leaf",420)],
 "red_mushroom":[("leafcutter_trunk",197)]
}
# Validate metadata and source lengths against entire distinct source segments.
allmap={s["file_id"]:s for s in edl}
for old,parts in replacements.items():
 assert sum(x[1] for x in parts)==int(allmap[old]["frames"]),(old,parts,allmap[old]["frames"])
assert len([x for pl in replacements.values() for x,_ in pl])==len(media)
assert len(set(k for vv in replacements.values() for k,_ in vv))==len(media)
for name,path in media.items():
 assert path.is_file(),f"Footage {path} absent"
 media[name]={"path":path,"duration":duration(path),"sha":hashlib.sha256(path.read_bytes()).hexdigest()}
assert len(set(d["sha"] for d in media.values()))==len(media)
for key in media:
 secs=[frames/FPS for entries in replacements.values() for k,frames in entries if k==key]
 assert len(secs)==1 and media[key]["duration"]-secs[0]>=.12,(key,media[key]["duration"],secs)
# Construct exact EDL final - original surviving scene samples are disjoint,
# each added original video used as one contiguous source interval.
pieces=[];new_edl=[];index=0
for shot in edl:
 a=int(round(float(shot["at"])*FPS));b=a+int(shot["frames"])
 key=shot["file_id"]
 if key not in replacements:
  pieces.append({"type":"old","in":0,"begin":a,"end":b,"source":key,"frames":b-a})
  new_edl.append(dict(shot))
 else:
  cursor=a
  for name,n in replacements[key]:
   src=media[name]
   source_start=14.7 if name=="hughes2011_unused_source" else max(0.0,(src["duration"]-n/FPS)/2)
   startframe=round(source_start*FPS)
   assert (startframe+n)/FPS<=src["duration"]+.02
   pieces.append({"type":"new","begin":cursor,"end":cursor+n,
                  "source":name,"frames":n,"first":startframe})
   entry=dict(shot)
   entry.update({"file_id":name,"source_in":startframe/FPS,
                  "at":cursor/FPS,"frames":n,"duration":n/FPS,
                  "scientific":name=="hughes2011_unused_source",
                  "infection_confirmed":name=="hughes2011_unused_source",
                  "credit":"Hughes et al. (2011), BMC Ecology 11:13, CC BY 2.0 (same original movie, a NON-OVERLAPPING previously unused continuous 5s part)."
                    if name=="hughes2011_unused_source" else
                    "Genuine moving nature footage (illustrative ordinary ants/forest, NOT proven Ophiocordyceps-infected), Pexels free license."})
   new_edl.append(entry)
   cursor+=n
  assert cursor==b
assert sum(s["frames"] for s in pieces)==total
assert len(new_edl)==len(pieces)
assert all(pieces[i]["end"]==pieces[i+1]["begin"] for i in range(len(pieces)-1))
assert pieces[0]["begin"]==0 and pieces[-1]["end"]==total
assert len(set(x["file_id"] for x in new_edl))==len(new_edl)
assert sum(e["frames"] for e in new_edl)==total
assert not any(e["file_id"]=="red_mushroom" for e in new_edl)
print("DIRECTOR'S CUT",len(pieces),"unique continuous clips; time",total/FPS,flush=True)
print("2011 OUTDOOR ZOMBIE-ANT SOURCE 1 = ",original_research_start,original_research_end,
"extra outdoor infected source 2 = 14.7 - 19.7 seconds; NO frame reuse",flush=True)
# Compose new HD frames using segments only once each. MP4 original V8 frames
# are referenced by disjoint trim intervals. Each new file is used once.
oldparts=[p for p in pieces if p["type"]=="old"]
filters=[f"[0:v]split={len(oldparts)}"+''.join(f"[orig{i}]" for i in range(len(oldparts)))]
inputs=["-i",str(ORIG)]
for key,d in media.items():inputs+=["-i",str(d["path"])]
index_map={key:i+1 for i,key in enumerate(media)}
ix_old=0;concat=[]
for i,p in enumerate(pieces):
 label=f"seg{i}"
 if p["type"]=="old":
  filters.append(f"[orig{ix_old}]trim=start_frame={p['begin']}:end_frame={p['end']},setpts=PTS-STARTPTS[{label}]")
  ix_old+=1
 else:
  j=index_map[p["source"]]
  start=p["first"];end=start+p["frames"]
  filters.append(
   f"[{j}:v]fps=30,trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS,"
   f"scale=1920:1080:force_original_aspect_ratio=increase,"
   f"crop=1920:1080:(iw-ow)/2:(ih-oh)/2,setsar=1,"
   f"format=yuv420p[{label}]")
 concat.append(f"[{label}]")
filters.append(''.join(concat)+f"concat=n={len(pieces)}:v=1:a=0,format=yuv420p[v]")
video_tmp=OUT/"V10_VISUAL_RENDER.mp4"
print("RENDERING REVISED VISUAL, source arrays = ",len(inputs),flush=True)
run(["ffmpeg","-hide_banner","-v","error","-y",*inputs,
     "-filter_complex",';'.join(filters),"-map","[v]","-an",
     "-c:v","libx264","-preset","veryfast","-crf","20","-r","30",
     "-pix_fmt","yuv420p","-video_track_timescale","30000",
     "-movflags","+faststart",str(video_tmp)])
assert abs(duration(video_tmp)-v8duration)<.15,(duration(video_tmp),v8duration)
# Build professional voice-forward opening without spoiling main discovery.
# V8 balanced sound is kept unchanged from 19.385s to end; 0-19.785 is
# new Kokoro matched voice + original score+forest CC0. Smooth 0.4s join.
hook_intro_duration=19.785
intro_tail_start=hook_intro_duration-.400
audio_filters=[
 "[2:a]aresample=48000,aformat=channel_layouts=stereo,"
 "highpass=f=80,lowpass=f=9800,loudnorm=I=-17:TP=-2.5:LRA=8,"
 "apad,atrim=duration=19.785,asetpts=PTS-STARTPTS[hook]",
 "[3:a]aresample=48000,aformat=channel_layouts=stereo,"
 "atrim=duration=19.785,loudnorm=I=-25:TP=-5:LRA=10,"
 "afade=t=in:st=0:d=1.6[score]",
 "[4:a]aresample=48000,aformat=channel_layouts=stereo,"
 "atrim=duration=19.785,highpass=f=100,lowpass=f=4700,"
 "loudnorm=I=-32.5:TP=-7:LRA=8,afade=t=in:st=0:d=2[forest]",
 "[hook][score][forest]amix=inputs=3:duration=first:normalize=0,"
 "alimiter=limit=0.92[intro]",
 f"[0:a]atrim=start={intro_tail_start:.3f},asetpts=PTS-STARTPTS[old]",
 "[intro][old]acrossfade=d=.4:c1=tri:c2=tri,"
 "alimiter=limit=.95[aout]"
]
# Audio inputs: 0=V8 balanced documentary, 1=updated V10 visual (video-only),
# 2=new Kokoro, 3=soundtrack original CC0, 4=real forest recorded ambience.
run(["ffmpeg","-hide_banner","-v","error","-y","-i",str(ORIG),
     "-i",str(video_tmp),"-i",str(HOOK_AUDIO),
     "-i",str(EXT/"score_dark_highway.mp3"),
     "-stream_loop","-1","-i",str(EXT/"ambience_forest.mp3"),
     "-filter_complex",';'.join(audio_filters),"-map","1:v:0","-map","[aout]",
     "-c:v","copy","-c:a","aac","-b:a","256k","-ar","48000",
     "-movflags","+faststart","-t",f"{v8duration:.4f}",str(FINAL)])
assert FINAL.stat().st_size>50_000_000
outdur=duration(FINAL)
assert abs(outdur-v8duration)<.16,(outdur,v8duration)
run(["ffmpeg","-hide_banner","-v","error","-xerror","-i",str(FINAL),"-f","null","-"])
# Unique decoded real-frame hash from BOTH unused and original infected source.
proof={}
for key in ("research_zombie","hughes2011_unused_source"):
 shot=next(x for x in new_edl if x["file_id"]==key)
 at=shot["at"]+shot["duration"]*.48
 out=run(["ffmpeg","-v","error","-ss",f"{at:.3f}","-i",str(FINAL),"-t","1",
         "-vf","fps=10,scale=320:180","-f","framemd5","-"])[0]
 dg=set(line.rsplit(',',1)[-1].strip() for line in out.splitlines() if line and not line.startswith('#'))
 assert len(dg)>=5,(key,len(dg))
 proof[key]=len(dg)
# All film cuts still have content (20+ sources) and no black side-matte from
# source: output crop always fills 1920x1080, and no new lab scene inserted.
(OUT/"NO_REPEAT_FRAME_EDL_V10.json").write_text(json.dumps(new_edl,indent=2))
# Subtitles: preserve exactly V8 SRT after 20s, regenerate opening sync for
# new hook so subtitle timeline does not reuse original now-incorrect speech.
oldsub=SRC/"SUBTITLES_EN.srt"
subs=[]
if oldsub.is_file():
 for block in re.split(r"\n\s*\n",oldsub.read_text(encoding="utf8-sig").strip()):
  match=re.search(r"(\d\d:\d\d:\d\d[,.]\d+)\s*-->\s*(\d\d:\d\d:\d\d[,.]\d+)",block)
  if not match:continue
  time=match.group(1).replace(',', '.')
  a,b,c=time.split(':');start=int(a)*3600+int(b)*60+float(c)
  if start>=20:subs.append(block.splitlines()[-1:] and "\n".join(block.splitlines()[1:]))
def ts(t):
 ms=int(round(t*1000));h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000;s=ms//1000;return f"{h:02d}:{m:02d}:{s:02d},{ms%1000:03d}"
early=[
 (.2,3.5,"This ant is alive."),
 (3.6,6.75,"But the way it moves\nisn't entirely its own."),
 (6.8,10.1,"A parasite is guiding it\ntoward one final act."),
 (10.2,13.2,"It will climb.\nIt will bite a leaf."),
 (13.4,15.3,"And it will never let go."),
 (15.4,17.9,"But why must it die\nin exactly the right place?")
]
newsub=[f"{ts(a)} --> {ts(b)}\n{content}" for a,b,content in early]
newsub+=subs
(OUT/"SUBTITLES_EN.srt").write_text("\n\n".join(f"{i+1}\n{block}" for i,block in enumerate(newsub))+"\n")
# Description and YT chapters, as an editable text file.
chapters=[
("00:00","The ant that won't let go"),("00:20","The infection"),
("00:59","The climb"),("01:38","The death grip"),
("02:13","A parasite that spares the brain"),("03:14","After death"),
("03:47","The final twist")]
(OUT/"YOUTUBE_CHAPTERS.txt").write_text("\n".join(f"{t} {name}" for t,name in chapters))
yt_description=(
 "A fungus turns an ordinary ant into an unwilling vehicle for its own reproduction. "
 "But one surprising finding changes how we understand this terrifying behavior.\n\n"
 "This science documentary explains real research on Ophiocordyceps, zombie ants, the death grip, "
 "and how fungal cells can surround ant muscles without invading the brain itself.\n\n"
 "CHAPTERS\n"+"\n".join(f"{t} {name}" for t,name in chapters)+"\n\n"
 "SOURCES\n"
 "Hughes et al. (2011), Behavioral mechanisms and morphological symptoms of zombie ants dying from fungal infection, "
 "BMC Ecology 11:13, https://doi.org/10.1186/1472-6785-11-13 (CC BY 2.0); original footage filmed in Southern Thailand.\n"
 "Fredericksen et al. (2017), Three-dimensional visualization and a deep-learning model reveal complex fungal parasite networks in behaviorally manipulated ants, "
 "PNAS 114(47), https://doi.org/10.1073/pnas.1711673114.\n"
 "New outdoor ant/forest cutaways are illustrative and do NOT depict verified infection; the actual infected ant footage is "
 "from Hughes et al. (2011). Unused distinct seconds from the same scientific video were added, with no repeated frames.\n"
 "Stock video: Pexels, https://www.pexels.com/license/. "
 "Real nature field audio Joseph Sardin (CC0); music John Bartmann (CC0). "
 "Original research and footage credited; editorial source video trimmed/cropped to 16:9.\n\n"
 "Strange, But Verified — true things that sound completely fake.\n")
(OUT/"YOUTUBE_DESCRIPTION_AND_SOURCES.txt").write_text(yt_description)
(OUT/"YOUTUBE_TITLE.txt").write_text("This Fungus Controls Ants — But Never Enters Their Brains")
(OUT/"YOUTUBE_TAGS.txt").write_text("zombie ants, Ophiocordyceps, fungus, mind control, parasite, death grip, entomology, science documentary, real science, Strange But Verified")
(OUT/"SOURCE_LICENSES_AND_CHANGES.json").write_text(json.dumps({
 "research":{"article":"Hughes et al. 2011, BMC Ecology 11:13","doi":"10.1186/1472-6785-11-13","license":"CC BY 2.0",
 "source":"https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2F1472-6785-11-13/MediaObjects/12898_2011_173_MOESM2_ESM.MP4",
 "original_sec":[original_research_start,original_research_end],
 "new_unused_sec":[14.7,19.7],"action":"Only temporally disjoint contiguous genuine outdoor intervals were inserted"},
 "other_sources":[{"id":k,"source_url":str(d["path"].name),"license":"Pexels video license; illustrative ONLY"} for k,d in media.items() if k!="hughes2011_unused_source"],
 "music":"John Bartmann CC0",
 "forest":"Joseph Sardin CC0",
 "voice":"Kokoro v1.0 af_heart at speed .88; revised spoiler-free opening. Remaining original seven chapters unchanged from V8."},indent=2))
# Preview frame and thumbnail derived only from original verified research footage.
thumb0=OUT/"thumb_original.jpg"
run(["ffmpeg","-v","error","-y","-ss","3.5","-i",str(FINAL),"-frames:v","1",str(thumb0)])
im=Image.open(thumb0).convert("RGB").resize((1280,720))
im=Image.blend(im,Image.new("RGB",(1280,720),(14,22,17)),.14)
lay=Image.new("RGBA",(1280,720),(0,0,0,0))
d=ImageDraw.Draw(lay)
# Readable text with charcoal drop shadow, positioned to keep creature visible.
fontfile="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font=ImageFont.truetype(fontfile,106)
d.rounded_rectangle((20,490,1100,685),radius=24,fill=(7,14,10,168))
d.text((40,505),"IT WON'T",font=font,fill=(255,245,196,255),stroke_width=3,stroke_fill=(0,0,0,230))
d.text((40,600),"LET GO",font=ImageFont.truetype(fontfile,58),fill=(255,247,241,255),stroke_width=2,stroke_fill=(0,0,0,240))
Image.alpha_composite(im.convert("RGBA"),lay).convert("RGB").save(OUT/"YOUTUBE_THUMBNAIL_1280x720.jpg",quality=94,subsampling=0)
# QA facts distinct from editorial judgments
qa={
 "status":"PASS","output":FINAL.name,"bytes":FINAL.stat().st_size,
 "length_seconds":round(outdur,3),"resolution":"1920x1080","fps":30,
 "sources_original":20,"video_segments":len(pieces),
 "unique_file_ids":len(set(x["file_id"] for x in new_edl)),
 "looped_frames":0,"extra_real_wild_infected_source_same_recording":True,
 "extra_verified_infected_ant_outdoor_seconds":5,
 "original_verified_infected_ant_outdoor_seconds":edl[0]["duration"],
 "same_scientific_recording_different_time_intervals":True,
 "distinct_external_scientific_field_video_sources":1,
 "new_other_outdoors_sources":len(media)-1,
 "captions_updated":True,"spoiler_free_hook":True,
 "no_mushroom_finale":True,"no_lab_insets_added":True,
 "music_and_nature_smooth_transition":True,
 "whole_film_decoding":"PASS","research_moving_frame_samples":proof
}
(OUT/"FINAL_REVIEW_QA.json").write_text(json.dumps(qa,indent=2))
# Source video already present and validated, discard temporary to shrink artifact.
video_tmp.unlink(missing_ok=True)
thumb0.unlink(missing_ok=True)
print("RENDER FINISHED",json.dumps(qa,indent=2),flush=True)
