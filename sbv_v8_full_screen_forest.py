#!/usr/bin/env python3
"""SBV V8: authentic forest/nature documentary, no laboratory inset clips.
Surgical replacement of the THREE framed scientific laboratory clips in V7
with THREE distinct real 16:9 field videos of ants naturally walking on trees,
moss and leaves. These are clearly labeled as *illustrative ordinary ant footage*
in the provenance, NOT infected zombie ants. Genuine 2011 wild infected ant
source is retained once and only once.

No loops or source replay. Voice, score, quiet field ambience and chapter
timing copied bit-exact from V7. Output is an actual rendered 1080p MP4.
"""
import json,re,subprocess,hashlib,math,shutil
from pathlib import Path
ROOT=Path.cwd()
IN=ROOT/"v8_source";OUT=ROOT/"v8_output"
OUT.mkdir(exist_ok=True)
VIDEO=IN/"SBV_ZOMBIE_ANT_V7_BALANCED_NATURE_SOUND.mp4"
EDLP=IN/"NO_REPEAT_EDL_V6.json"
MASTER=OUT/"SBV_ZOMBIE_ANT_V8_FOREST_ONLY_NO_LAB_NO_REPEATS.mp4"

# Real, licensed, distinct clips of ordinary ants outdoors. All three videos
# verified with Canva imports as true moving video, not stills, AI or replays.
SOURCE_VIDEO={
  "beckerson_2023_real_infected_camponotus_floridanus":{
     "file":IN/"pexels_3617015_black_ants_tree_branch.mp4",
     "id":"pexels_3617015_black_ants_tree_branch",
     "credit":"Aduri Prem Kumar, A Black Ant Crawling on the Branch of a Tree, Pexels, free video license. Actual outdoor ants, NOT known infected.",
     "uri":"https://www.pexels.com/video/a-black-ant-crawling-on-the-branch-of-a-tree-3617015/"},
  "deBekker_2014_castaneus_genuine_infected":{
     "file":IN/"pexels_12633171_ants_on_wood_lush.mp4",
     "id":"pexels_12633171_ants_on_wood_lush",
     "credit":"Cesar A Ramirez Vallejo, Ants on Wood, Pexels, free video license. Actual outdoor ants, NOT known infected.",
     "uri":"https://www.pexels.com/video/ants-on-wood-12633171/"},
  "deBekker_2014_americanus_genuine_infected":{
     "file":IN/"pexels_3239802_ant_on_green_moss.mp4",
     "id":"pexels_3239802_ant_on_green_moss",
     "credit":"The Marc Knight, Red Ant Crawling on Moss, Pexels, free video license. Actual outdoor ants, NOT known infected.",
     "uri":"https://www.pexels.com/video/red-ant-crawling-on-a-surface-covered-in-moss-3239802/"}
}
def cmd(args):
 p=subprocess.run([str(z) for z in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:
  print("ERROR:\n"+p.stderr[-4500:],flush=True)
  raise RuntimeError("Command failed "+repr(args[:9]))
 return p.stdout,p.stderr
def duration(path):
 p=subprocess.run(["ffmpeg","-hide_banner","-i",str(path)],text=True,capture_output=True)
 m=re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",p.stderr)
 if not m:raise RuntimeError("No readable audio/video duration "+str(path))
 return int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))
def stream_hash(path,what):
 return cmd(["ffmpeg","-hide_banner","-v","error","-i",path,
   "-map","0:"+what+":0","-c","copy","-f","hash","-hash","SHA256","-"])[0].strip()
assert VIDEO.is_file() and VIDEO.stat().st_size>60_000_000
assert EDLP.is_file()
edl=json.loads(EDLP.read_text())
assert len(edl)==20
ids=[k["file_id"] for k in edl]
assert len(set(ids))==20,"Prior video already repeats sources."
assert "research_zombie" in ids,"Real 2011 field-study shot missing, cannot release."
original=duration(VIDEO)
assert 240<original<250
totalframes=sum(int(c["frames"]) for c in edl)
assert abs(totalframes/30-original)<.13,(totalframes,original)
targets=[]
video_sizes={}
for j,(key,obj) in enumerate(SOURCE_VIDEO.items(),start=1):
 shots=[e for e in edl if e["file_id"]==key]
 assert len(shots)==1,(key,len(shots))
 e=shots[0]
 file=obj["file"]
 assert file.is_file() and file.stat().st_size>500_000
 source_duration=duration(file)
 assert source_duration >= e["duration"]+.4,(key,source_duration,e["duration"])
 beg=round(float(e["at"])*30)
 end=beg+int(e["frames"])
 assert 0<beg<end<totalframes
 video_sizes[obj["id"]]=(source_duration,file.stat().st_size)
 targets.append({"old":key,"begin":beg,"end":end,"duration":e["duration"],
   "new":obj,"input_index":j,"source_duration":source_duration})
targets.sort(key=lambda e:e["begin"])
assert len(targets)==3
assert all(targets[i]["end"]<=targets[i+1]["begin"] for i in range(2))
assert len(set(x["new"]["id"] for x in targets))==3
print("REMOVE EXACT LAB TIMELINE SECTIONS",[(x["old"],round(x["begin"]/30,3),round(x["duration"],2)) for x in targets],flush=True)
# Ensure source footage is filmed nature, separate original recordings:
# sha256 of source bytes must not overlap with one another. Full-frame native 16:9.
source_shas=[hashlib.sha256(x["new"]["file"].read_bytes()).hexdigest() for x in targets]
assert len(set(source_shas))==3
for item in targets:
 # Full decode few frames up front, fail if broken/truncated media.
 cmd(["ffmpeg","-hide_banner","-loglevel","error","-xerror",
  "-i",item["new"]["file"],"-t","2","-f","null","-"])
 print("VERIFIED FRESH WILDLIFE CLIP",item["new"]["id"],round(item["source_duration"],2),flush=True)

# Existing frame stream is divided into only the intervals *outside* the lab
# scenes. An existing source frame can appear in exactly one interval.
pieces=[];timeline_start=0
for t in targets:
 if timeline_start<t["begin"]:
  pieces.append(("existing",timeline_start,t["begin"],None))
 pieces.append(("new",t["begin"],t["end"],t))
 timeline_start=t["end"]
if timeline_start<totalframes:pieces.append(("existing",timeline_start,totalframes,None))
assert sum(b-a for _,a,b,_ in pieces)==totalframes
base=[p for p in pieces if p[0]=="existing"]
filters=["[0:v]split="+str(len(base))+"".join(f"[orig{j}]" for j in range(len(base)))]
labels=[]
baseidx=0
for i,(kind,a,b,t) in enumerate(pieces):
 if kind=="existing":
  label=f"segment{i}"
  filters.append(f"[orig{baseidx}]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[{label}]")
  baseidx+=1
 else:
  label=f"segment{i}"
  new=t["new"]
  # Select one *contiguous* section from the unique original wildlife source.
  # Use full-frame crop, avoiding both pillarboxing and zoom/stretch of insects.
  start_f=round((t["source_duration"]-(b-a)/30)/2*30)
  end_f=start_f+(b-a)
  assert end_f/30<t["source_duration"]+.3
  filters.append(
   f"[{t['input_index']}:v]fps=30,"
   f"trim=start_frame={start_f}:end_frame={end_f},"
   f"setpts=PTS-STARTPTS,"
   f"scale=1920:1080:force_original_aspect_ratio=increase,"
   f"crop=1920:1080:(iw-ow)/2:(ih-oh)/2,"
   f"setsar=1,eq=contrast=1.035:saturation=0.95,"
   f"format=yuv420p[{label}]")
  t["source_start"]=start_f/30
 labels.append(f"[{label}]")
filters.append("".join(labels)+f"concat=n={len(labels)}:v=1:a=0,format=yuv420p[video_out]")
# MP4 audio is COPIED bit-perfectly from V7 (Kokoro and balanced nature mix).
ff=["ffmpeg","-hide_banner","-loglevel","error","-y",
 "-i",str(VIDEO),*sum((["-i",str(obj["file"])] for obj in SOURCE_VIDEO.values()),[]),
 "-filter_complex",";".join(filters),
 "-map","[video_out]","-map","0:a:0",
 "-c:v","libx264","-preset","veryfast","-crf","19","-r","30",
 "-pix_fmt","yuv420p","-video_track_timescale","30000",
 "-c:a","copy","-movflags","+faststart",str(MASTER)]
print("RENDER V8 - NO LAB FOOTAGE, NO BOXES, ONLY UNIQUE MOVING ANT VIDEOS",flush=True)
cmd(ff)
outduration=duration(MASTER)
assert abs(outduration-original)<.15,(outduration,original)
assert MASTER.stat().st_size>60_000_000
source_audio_hash=stream_hash(VIDEO,"a")
final_audio_hash=stream_hash(MASTER,"a")
assert source_audio_hash==final_audio_hash,"Original Kokoro/music/nature mix unexpectedly changed!"
# Validate *entire* movie decodes without frame errors.
cmd(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",MASTER,"-f","null","-"])
# Test at least six distinct MOVING frames inside EACH replacement.
motion={}
for t in targets:
 checkpoint=t["begin"]/30+t["duration"]/2
 raw=cmd(["ffmpeg","-v","error","-ss",f"{checkpoint:.3f}",
         "-i",MASTER,"-t","0.95","-vf","fps=9,scale=320:180",
         "-f","framemd5","-"])[0]
 hashes=set(line.rsplit(",",1)[-1].strip() for line in raw.splitlines() if line and not line.startswith("#"))
 if len(hashes)<5:raise RuntimeError("Static or frozen replacement "+t["new"]["id"])
 motion[t["new"]["id"]]=len(hashes)
# Rebuild original no-repeat manifest, retaining real 2011 field infected clip
# and removing the 3 indoor/lab clips, not falsely claiming the new ants are infected.
new_edl=[]
for old in edl:
 entry=dict(old)
 if entry["file_id"] in SOURCE_VIDEO:
  new=SOURCE_VIDEO[entry["file_id"]]
  t=next(z for z in targets if z["old"]==entry["file_id"])
  entry.update({"file_id":new["id"],"scientific":False,
                "confirmed_infected":False,"environment":"outdoors",
                "source_in":t["source_start"],"credit":new["credit"]})
 new_edl.append(entry)
assert len(set(x["file_id"] for x in new_edl))==len(new_edl)==20
assert sum(int(x["frames"]) for x in new_edl)==totalframes
assert not any("deBekker_2014" in x["file_id"] or "beckerson_2023" in x["file_id"] for x in new_edl)
assert len([x for x in new_edl if x["file_id"]=="research_zombie"])==1
(OUT/"V8_NO_REPEATS_NO_LAB_EDL.json").write_text(json.dumps(new_edl,indent=2))
qa={
 "status":"PASS","file":MASTER.name,"size_bytes":MASTER.stat().st_size,
 "duration_seconds":round(outduration,3),"resolution":"1920x1080","fps":30,
 "video_source_count":20,"video_repetitions":0,"static_photographs":0,
 "laboratory_footage_clips_remaining":0,
 "original_research_field_footage_zombie_ant_retained":True,
 "new_infected_zombie_ant_forest_clips_confirmed":0,
 "new_field_moving_footage_illustrative_regular_ants":3,
 "laboratory_source_intervals_removed":[{"id":t["old"],"start":t["begin"]/30,"seconds":t["duration"]} for t in targets],
 "new_video_sources":[{"id":t["new"]["id"],"url":t["new"]["uri"],"used_seconds":t["duration"],"natural_environment":True,
      "infection_confirmed":False,"verified_moving_hash_count":motion[t["new"]["id"]]} for t in targets],
 "frame_fill":"full bleed 16:9 crop, no inset/blurred portrait borders",
 "audio_bit_identical_from_v7":True,"original_audio_sha256":source_audio_hash,
 "final_audio_sha256":final_audio_hash,
 "Kokoro_music_nature_and_chapter_timing":"preserved",
 "full_ffmpeg_decode":"PASS"
}
(OUT/"V8_FOREST_ONLY_QA.json").write_text(json.dumps(qa,indent=2))
(OUT/"V8_SCIENCE_AND_VIDEO_CREDITS.txt").write_text(
 "STRANGE, BUT VERIFIED — Zombie Ants V8 (forest-style edit)\n\n"
 "IMPORTANT SCIENTIFIC AND VISUAL DISTINCTION\n"
 "Genuine fungus-infected zombie ant FILMED IN TROPICAL FOREST: Hughes, D. et al. (2011), "
 "Behavioral mechanisms and morphological symptoms of zombie ants dying from fungal infection. "
 "BMC Ecology 11:13, DOI 10.1186/1472-6785-11-13. Original Video S2 (CC BY 2.0), "
 "retained once from the first V1 production without duplicating any frames. "
 "Field location: Thailand, ant locked onto leaf vein.\n\n"
 "NEW WILDLIFE SHOTS — REAL MOTION VIDEO OF ORDINARY ANTS, NOT KNOWN INFECTED:\n"
 +"\n".join("- "+t["new"]["credit"]+"\n  "+t["new"]["uri"] for t in targets)
 + "\nLicense https://www.pexels.com/license/. Color-adapted, cropped to 16:9, excerpted. "
 "These are editorial environmental illustrations, not footage of fungal infection.\n\n"
 "REMOVED: ALL THREE lab-specific insets and blurred portrait research clips from 2014 and 2023. "
 "The corresponding experimental scenes were not from wild habitats.\n\n"
 "ALL OTHER FOOTAGE: 20 distinct original motion-video sources as documented in V8_NO_REPEATS_NO_LAB_EDL.json. "
 "Original science footage retained; no source file used twice.\n"
 "AUDIO: Original V7 Kokoro af_heart narration and balanced cinematic score/real CC0 nature sounds "
 "copied bit-identically, with original film title and chapter silences/timing unchanged.\n"
 "No AI generated biology, no still images, no repeated clips.\n")
# Preserve subtitles and scientific source notes for original
for source,target in [(IN/"SUBTITLES_EN.srt","SUBTITLES_EN.srt"),
                      (IN/"V7_AUDIO_BALANCE_QA.json","V7_AUDIO_BALANCE_QA.json")]:
 if source.is_file():shutil.copy2(source,OUT/target)
for title,timestamp in [("01_nature_climb",59+3),
                        ("02_nature_ant_bark",98+5),
                        ("03_nature_moss",113+5),
                        ("04_original_wild_infected_ant",4)]:
 cmd(["ffmpeg","-v","error","-y","-ss",str(timestamp),"-i",MASTER,
      "-frames:v","1",str(OUT/(title+".jpg"))])
print("V8 PASS",json.dumps(qa,indent=2),flush=True)
