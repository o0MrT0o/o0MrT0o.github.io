#!/usr/bin/env python3
"""V6: ONE additional peer-reviewed genuine Ophiocordyceps-infected ant video,
Beckerson, Krider, Mohammad & de Bekker (2023), Animal Behaviour 203.
Real infected C. floridanus exhibiting "staggers" (supplementary Video S1).
Replaces one illustrative source in THE CLIMB. V5 sound stream is preserved bit-exact.
Strict: zero repeated source-time intervals, zero photos, original chapter timings unchanged.
"""
from pathlib import Path
import json, re, hashlib, subprocess, shutil, math
from dataclasses import asdict

P=Path.cwd()
ROOT=P/"v6_sources";ROOT.mkdir(exist_ok=True)
OUT=P/"v6_output";OUT.mkdir(exist_ok=True)
V5=ROOT/"SBV_ZOMBIE_ANT_V5_REAL_ZOMBIE_ANTS_NO_REPEATS.mp4"
EDL=ROOT/"V5_NO_REPEAT_EDL.json"
NEW=ROOT/"Beckerson_2023_Ophiocordyceps_infected_ant_staggering.mp4"
MASTER=OUT/"SBV_ZOMBIE_ANT_V6_EXTRA_REAL_STAGGERING_FOOTAGE.mp4"
for x in (V5,EDL,NEW):
 if not x.is_file() or x.stat().st_size<200:
  raise RuntimeError(f"Required verified source missing: {x}")

def call(args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode!=0:raise RuntimeError("FFmpeg failed: "+str(args[:9])+"\n"+p.stderr[-3500:])
 return p.stdout,p.stderr

def duration(x):
 p=subprocess.run(["ffmpeg","-hide_banner","-i",str(x)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 m=re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",p.stderr)
 if not m:raise RuntimeError("Could not read media duration: "+str(x)+" "+p.stderr[-450:])
 return int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))

def stream_hash(path):
 return call(["ffmpeg","-hide_banner","-v","error","-i",str(path),"-map","0:a:0","-c:a","copy","-f","hash","-hash","SHA256","-"])[0].strip()

edl=json.loads(EDL.read_text())
assert len(edl)==20 and len(set(x["file_id"] for x in edl))==20
video_d=duration(V5)
source_d=duration(NEW)
assert 10<source_d<25, f"Unexpected study video duration: {source_d}"
fps=30
totalframes=sum(int(x["frames"]) for x in edl)
assert abs(totalframes/fps-video_d)<0.12
# The paper's original video 1 shows fungus-infected C. floridanus staggering, NOT
# aflatrem-injected controls. Other supplementary clips are not inserted as infection.
# Seek a stock-only shot in THE CLIMB chapter, avoiding existing science and titles.
choices=[x for x in edl if x["chapter"]==2 and
 x["file_id"] in ("leafcutter","leaf_carrier","grass_ants") and
 x["duration"]<=source_d-0.4 and x["duration"]>=5.5]
if not choices:
 choices=[x for x in edl if x["chapter"] in (1,2) and not x.get("scientific") and
   x["duration"]<=source_d-0.4 and x["duration"]>=5.5]
if not choices:
 raise RuntimeError("No short illustrative scene fits a new nonrepeated research clip")
# Prefer the introductory normal-ant clip to strengthen actual infected footage.
choices.sort(key=lambda x:(x["chapter"]!=2,x["file_id"] not in ("leafcutter","leaf_carrier"),abs(x["duration"]-source_d*.8)))
replaced=choices[0]
a=int(round(replaced["at"]*fps))
b=a+int(replaced["frames"])
assert 20<a<b<totalframes-15
assert b-a<=int((source_d-.2)*fps)
print("V5 sec",video_d,"REAL SCIENCE VIDEO sec",source_d,flush=True)
print("REPLACE STOCK",json.dumps(replaced),flush=True)
start_from=max(0.,(source_d-(b-a)/fps)/2)
# Preserve original scientific frames and aspect ratio, with an ambient moving
# backdrop generated FROM THE SAME VIDEO AT THE SAME INSTANT (no fake photo).
src_begin=round(start_from*fps)
length=b-a
vf=[
 "[0:v]split=2[orig0][orig1]",
 f"[orig0]trim=start_frame=0:end_frame={a},setpts=PTS-STARTPTS[before]",
 f"[orig1]trim=start_frame={b}:end_frame={totalframes},setpts=PTS-STARTPTS[after]",
 f"[1:v]fps=30,trim=start_frame={src_begin}:end_frame={src_begin+length},setpts=PTS-STARTPTS,split=2[srcbg][srcfg]",
 "[srcbg]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
 "gblur=sigma=28:steps=2,eq=brightness=-0.1:saturation=0.9[movingbg]",
 "[srcfg]scale=1920:1080:force_original_aspect_ratio=decrease,setsar=1,format=yuv420p[movingfg]",
 "[movingbg][movingfg]overlay=x=(W-w)/2:y=(H-h)/2:shortest=1[research]",
 "[before][research][after]concat=n=3:v=1:a=0,format=yuv420p[out]"
]
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(V5),"-i",str(NEW),
 "-filter_complex",";".join(vf),"-map","[out]","-map","0:a:0",
 "-c:v","libx264","-preset","veryfast","-crf","20","-r","30",
 "-pix_fmt","yuv420p","-video_track_timescale","30000",
 "-c:a","copy","-movflags","+faststart",str(MASTER)]
print("START V6 SCIENTIFIC DOCUMENTARY RENDER",flush=True)
call(cmd)
outd=duration(MASTER)
if abs(outd-video_d)>0.12:raise RuntimeError(f"Audio/video duration changed {video_d} -> {outd}")
if MASTER.stat().st_size<40_000_000:raise RuntimeError("Rendered MP4 smaller than expected")
old_a=stream_hash(V5);new_a=stream_hash(MASTER)
if old_a!=new_a:raise RuntimeError(f"V5 music or Kokoro audio altered: {old_a} vs {new_a}")
call(["ffmpeg","-v","error","-xerror","-i",str(MASTER),"-f","null","-"])
# Check that this research video really supplies changing film frames rather
# than a static slide / still photo.
frames_hash=call(["ffmpeg","-v","error","-ss",str((a+int(length*.3))/fps),
                  "-i",str(MASTER),"-t","0.8","-vf","fps=9,scale=320:180",
                  "-f","framemd5","-"])[0]
unique_digest=set(line.rsplit(",",1)[-1].strip() for line in frames_hash.splitlines()
 if line and not line.startswith("#"))
if len(unique_digest)<5:raise RuntimeError("New inserted segment has little or no motion")
# EDL: remove one stock source; replace with 2023 science. Same 20 total,
# original 2011 & 2014 source ranges unchanged and never repeated.
newedl=[]
for e in edl:
 entry=dict(e)
 if e["file_id"]==replaced["file_id"]:
  entry.update({"file_id":"beckerson_2023_real_infected_camponotus_floridanus",
   "scientific":True,"source_in":start_from,
   "credit":"Beckerson W.C., Krider C., Mohammad U.A. and de Bekker C. (2023), Animal Behaviour 203, 225-240; DOI 10.1016/j.anbehav.2023.06.011; CC BY 4.0. Supplemental Video S1 (mmc2.mp4)."})
 newedl.append(entry)
assert len(set(x["file_id"] for x in newedl))==len(newedl)==20
assert sum(int(x["frames"]) for x in newedl)==totalframes
(OUT/"NO_REPEAT_EDL_V6.json").write_text(json.dumps(newedl,indent=2))
qa={
 "status":"PASS",
 "output_file":MASTER.name,
 "size_bytes":MASTER.stat().st_size,
 "duration_sec":round(outd,3),
 "resolution":"1920x1080","fps":30,
 "moving_video_sources":len(newedl),"reused_clip_count":0,
 "genuine_infected_ant_source_count":4,
 "new_source":"Beckerson et al. (2023), genuinely Ophiocordyceps-infected Camponotus floridanus with staggering behavior, supplemental video S1.",
 "new_original_clip_seconds":round(source_d,3),
 "new_time_used_seconds":round(length/fps,3),
 "replaced_stock_source":replaced["file_id"],
 "insert_time_seconds":round(a/fps,3),
 "added_clip_motion_unique_hashes":len(unique_digest),
 "original_v5_kokoro_and_music_bitalike":old_a==new_a,
 "original_audio_sha256":old_a,
 "new_audio_sha256":new_a,
 "chapter_titles_and_pauses_unchanged":True,
 "no_stills_or_generated_biology":True,
 "full_mp4_decode":"PASS"
}
(OUT/"QA_V6_REAL_OPHIOCORDYCEPS.json").write_text(json.dumps(qa,indent=2))
credits=(
 "Strange, But Verified - Zombie Ants V6\n"
 "New REAL fungus-infected ant research footage: Beckerson, W.C., Krider, C., Mohammad, U.A., "
 "and de Bekker, C. (2023). 28 minutes later: investigating the role of aflatrem-like "
 "compounds in Ophiocordyceps parasite manipulation of zombie ants. Animal Behaviour 203:225-240. "
 "DOI: 10.1016/j.anbehav.2023.06.011. Open access CC BY 4.0 "
 "https://creativecommons.org/licenses/by/4.0/\n"
 "Video source: https://ars.els-cdn.com/content/image/1-s2.0-S0003347223001616-mmc2.mp4 "
 "(Supplementary Video S1, actual Ophiocordyceps-infected Camponotus floridanus staggering; "
 "trimmed/cropped for documentary presentation).\n"
 "Other primary footage: Hughes et al. BMC Ecology 2011 CC BY 2.0; de Bekker et al. "
 "BMC Evolutionary Biology 2014 CC BY 4.0.\n"
 "All Pexels footage: noninfected / illustrative unrelated species. "
 "Two older illustrative scenes were removed in V5, and another in V6. "
 "No photos, no repeated sequences, no generative fungus/ant video.\n"
 "Music, field-recorded forest sounds, original Kokoro af_heart, chapter timing "
 "and cinematic title: IDENTICAL from V5 (bit-exact AAC stream). See V4 source credits.\n")
(OUT/"CREDITS_SCIENTIFIC_SOURCES_V6.txt").write_text(credits)
for source,target in [
 ("v5_input/SUBTITLES_EN.srt","SUBTITLES_EN.srt"),
 ("v5_input/QA_V5_MORE_REAL_FOOTAGE.json","QA_BASE_V5.json")]:
 src=P/source
 if src.is_file():shutil.copy2(src,OUT/target)
# The pre-rendered V5 source was modified only in a scientific chapter.
for name,at in [("01_original_film_title",21),("02_new_real_ophio_staggering",(a+b)/2/fps),
 ("03_real_de_bekker_2014",108)]:
 call(["ffmpeg","-hide_banner","-v","error","-y","-ss",str(at),"-i",str(MASTER),
       "-frames:v","1",str(OUT/(name+".jpg"))])
print("V6 PASS",json.dumps(qa,indent=2),flush=True)
