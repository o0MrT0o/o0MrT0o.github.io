#!/usr/bin/env python3
"""SBV V5: replace two illustrative ant shots in V4 with two authentic
Ophiocordyceps-infected ants from de Bekker et al. 2014 scientific videos.
Never loop or repeat footage. Preserve V4's music, Kokoro voice and chapters.
"""
import array, hashlib, json, math, os, re, shutil, subprocess
from pathlib import Path

ROOT=Path.cwd()
OLD=ROOT/"v4_input"/"SBV_ZOMBIE_ANT_V4_CINEMATIC_NATURE_FINAL.mp4"
EDLFILE=ROOT/"v3_reference"/"NO_REPEAT_EDL.json"
CRED=ROOT/"v4_input"/"CREDITS_AND_SOURCES.txt"
NEW1=ROOT/"new_science"/"REAL_OPHIOCORDYCEPS_INFECTED_C_CASTANEUS_DEATH_GRIP.mp4"
NEW2=ROOT/"new_science"/"REAL_OPHIOCORDYCEPS_INFECTED_C_AMERICANUS_DEATH_GRIP.mp4"
OUT=ROOT/"v5_output";OUT.mkdir(exist_ok=True)
MASTER=OUT/"SBV_ZOMBIE_ANT_V5_REAL_ZOMBIE_ANTS_NO_REPEATS.mp4"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for fn in [OLD,EDLFILE,NEW1,NEW2]:
    if not fn.is_file():raise RuntimeError("Missing required input: "+str(fn))
def execute(args,show=False):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:
        print(p.stderr[-5000:],flush=True)
        raise RuntimeError("Command failed: "+str(args[:12])+"\n"+p.stderr[-2000:])
    if show:print("OK",str(args[:8]),flush=True)
    return p.stdout,p.stderr
def run(args,show=False):return execute(args,show)[0]
def duration(path):
    # Portable imageio-ffmpeg contains FFmpeg, not necessarily ffprobe.
    p=subprocess.run(["ffmpeg","-hide_banner","-i",str(path)],capture_output=True,text=True)
    m=re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",p.stderr)
    if not m:raise RuntimeError("Cannot establish video duration: "+str(path)+" "+p.stderr[-300:])
    return int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))
def stream_hash(path):
    stdout,_=execute(["ffmpeg","-v","error","-i",str(path),"-map","0:a:0","-c:a","copy","-f","hash","-hash","SHA256","-"])
    return stdout.strip()
def shasum(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for p in iter(lambda:f.read(4*1024*1024),b""):h.update(p)
    return h.hexdigest()

edl=json.loads(EDLFILE.read_text())
assert len(edl)==20,len(edl)
keys=[x["file_id"] for x in edl]
assert len(keys)==len(set(keys)), "V3 EDL already has repeated footage"
original_duration=duration(OLD)
assert 230<original_duration<270,original_duration
duration_1=duration(NEW1);duration_2=duration(NEW2)
assert 18<duration_1<25,duration_1
assert 58<duration_2<72,duration_2
# The original V4 picture uses exactly V3's shot timings, therefore two
# distinct stock segments can be replaced without changing scene boundaries.
# Both replacements occur inside chapter 3 (THE DEATH GRIP) and neither crosses
# an on-screen film/chapter title transition.
replace_key_1="fire_ants"
replace_key_2="carcass_ants"
shots={}
for key in [replace_key_1,replace_key_2]:
    found=[x for x in edl if x["file_id"]==key]
    assert len(found)==1,("Required distinct stock shot missing",key,found)
    shots[key]=found[0]
s1=shots[replace_key_1];s2=shots[replace_key_2]
assert s1["chapter"]==s2["chapter"]==3, shots
assert s1["at"]+s1["duration"]<=s2["at"]+0.001
F=30
A0=int(round(s1["at"]*F));A1=A0+int(s1["frames"])
B0=int(round(s2["at"]*F));B1=B0+int(s2["frames"])
END=sum(int(x["frames"]) for x in edl)
assert 0<A0<A1<=B0<B1<END,(A0,A1,B0,B1,END)
R1=A1-A0;R2=B1-B0
assert R1/F<duration_1-0.15
assert R2/F<duration_2-0.15
assert abs(END/F-original_duration)<0.12,(END/F,original_duration)
print("AUDITED ORIGINAL",len(edl),"source files,",END,"video frames",original_duration,flush=True)
print("REPLACING",replace_key_1,s1["at"],R1/F,"with real infected castaneus (duration",duration_1,")",flush=True)
print("REPLACING",replace_key_2,s2["at"],R2/F,"with real infected americanus (duration",duration_2,")",flush=True)

# Keep source frames contiguous. The 20-second 16:9 research clip fills the screen.
# The second primary research file is portrait 360x640: never stretch it or
# crop out the real ant. Show its original video over a softly blurred moving
# backdrop derived from that SAME TIME RANGE. This isn't a still photo.
start_1=max(0, (duration_1-R1/F)/2)
start_2=max(0, (duration_2-R2/F)/2)
s1_frame=int(round(start_1*F));s2_frame=int(round(start_2*F))
tag="GENUINE LABORATORY FOOTAGE  /  DE BEKKER ET AL. 2014"
# Original V4 video is split into unaffected segments, pixel-by-pixel and
# in order. All its segments are disjoint in time: no replay.
adjacent=(B0==A1)
if adjacent:
    parts=[
      "[0:v]split=2[base0][base2]",
      f"[base0]trim=start_frame=0:end_frame={A0},setpts=PTS-STARTPTS[p0]",
      f"[base2]trim=start_frame={B1}:end_frame={END},setpts=PTS-STARTPTS[p2]",
    ]
else:
    parts=[
      "[0:v]split=3[base0][base1][base2]",
      f"[base0]trim=start_frame=0:end_frame={A0},setpts=PTS-STARTPTS[p0]",
      f"[base1]trim=start_frame={A1}:end_frame={B0},setpts=PTS-STARTPTS[p1]",
      f"[base2]trim=start_frame={B1}:end_frame={END},setpts=PTS-STARTPTS[p2]",
    ]
parts += [
 f"[1:v]fps=30,trim=start_frame={s1_frame}:end_frame={s1_frame+R1},setpts=PTS-STARTPTS,"
 "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,format=yuv420p[science1]",
 f"[2:v]fps=30,trim=start_frame={s2_frame}:end_frame={s2_frame+R2},"
 "setpts=PTS-STARTPTS,split=2[vn_bg][vn_fg]",
 "[vn_bg]scale=1920:1080:force_original_aspect_ratio=increase,"
 "crop=1920:1080,gblur=sigma=35:steps=2,"
 "eq=brightness=-0.13:saturation=0.82[bgportrait]",
 "[vn_fg]scale=608:1080:force_original_aspect_ratio=decrease,setsar=1,format=yuv420p[fgportrait]",
 "[bgportrait][fgportrait]overlay=x=(W-w)/2:y=(H-h)/2:shortest=1[science2]",
]
parts.append(
 ("[p0][science1][science2][p2]concat=n=4:v=1:a=0," if adjacent else
  "[p0][science1][p1][science2][p2]concat=n=5:v=1:a=0,")
 + "format=yuv420p[outvideo]")
ff=[
 "ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(OLD),
 "-i",str(NEW1),"-i",str(NEW2),"-filter_complex",";".join(parts),
 "-map","[outvideo]","-map","0:a:0",
 "-c:v","libx264","-preset","veryfast","-crf","20",
 "-pix_fmt","yuv420p","-r","30","-video_track_timescale","30000",
 "-c:a","copy","-movflags","+faststart",str(MASTER)
]
print("RENDER REAL SCIENCE INSERTS",flush=True)
execute(ff)
out_duration=duration(MASTER)
assert abs(original_duration-out_duration)<0.12,(original_duration,out_duration)
# Preserve bitwise original AAC audio: songs, natural field recordings,
# full cinematic title and ALL Kokoro chapter pauses, unchanged.
source_audio_hash=stream_hash(OLD);out_audio_hash=stream_hash(MASTER)
if source_audio_hash!=out_audio_hash:
    raise RuntimeError("Audio stream altered unexpectedly: "+source_audio_hash+" != "+out_audio_hash)
# Strict full decode test catches corrupted frames or bad shot joins.
execute(["ffmpeg","-v","error","-xerror","-i",str(MASTER),"-f","null","-"])
assert MASTER.stat().st_size>45*1024*1024
# Video frames actually move in BOTH added science segments.
new_frames_md5={}
for number,(name,at) in enumerate([
  ("castaneus",float(s1["at"])+min(2.0,R1/F/3)),
  ("americanus",float(s2["at"])+min(2.0,R2/F/3))
]):
    out=run(["ffmpeg","-hide_banner","-v","error","-ss",str(at),"-i",str(MASTER),
    "-t","0.9","-vf","fps=8,scale=320:180","-f","framemd5","-"])
    digests=set(line.rsplit(",",1)[-1].strip() for line in out.splitlines() if line and not line.startswith("#"))
    assert len(digests)>=4, "Possible frozen new video: "+name
    new_frames_md5[name]=len(digests)
# EDL is rebuilt with 2 unique primary research videos instead of 2 unrelated
# ant stock sources. No source repeats and no overlapping source time.
newedl=[]
for x in edl:
    n=dict(x)
    if n["file_id"]==replace_key_1:
        n["file_id"]="deBekker_2014_castaneus_genuine_infected"
        n["scientific"]=True
        n["credit"]="de Bekker et al. 2014 BMC Evolutionary Biology 14:166 CC BY 4.0"
        n["source_in"]=round(start_1,3)
    elif n["file_id"]==replace_key_2:
        n["file_id"]="deBekker_2014_americanus_genuine_infected"
        n["scientific"]=True
        n["credit"]="de Bekker et al. 2014 BMC Evolutionary Biology 14:166 CC BY 4.0"
        n["source_in"]=round(start_2,3)
    newedl.append(n)
assert len(newedl)==len(set(x["file_id"] for x in newedl))==20
assert sum(int(z["frames"]) for z in newedl)==END
(OUT/"V5_NO_REPEAT_EDL.json").write_text(json.dumps(newedl,indent=2))
qa={
 "status":"PASS",
 "file":MASTER.name,
 "duration_seconds":out_duration,"size_bytes":MASTER.stat().st_size,
 "resolution":"1920x1080", "fps":30,
 "genuine_infected_ant_sources":3,
 "new_authentic_zombie_ant_sources":2,
 "no_repeat_original_source_count":20,
 "repeated_source_count":0,"still_images":0,
 "added_science":[
  {"source":"de Bekker 2014 Camponotus castaneus","source_original_length_s":duration_1,
   "used_duration_s":round(R1/F,3),"timeline_at_s":s1["at"]},
  {"source":"de Bekker 2014 Camponotus americanus","source_original_length_s":duration_2,
   "used_duration_s":round(R2/F,3),"timeline_at_s":s2["at"],"portrait_proportions_preserved":True}],
 "audio":{"unchanged_bit_exact":True,"source_stream_sha256":source_audio_hash,
          "output_stream_sha256":out_audio_hash,
          "kokoro_af_heart":True,"music_and_real_nature_sound_preserved":True},
 "chapter_title_timing":"same as V4 (no retime)",
 "source_visual_no_repeat":"PASS",
 "added_clips_motion_hashes":new_frames_md5,
 "full_ffmpeg_decode":"PASS"
}
(OUT/"QA_V5_MORE_REAL_FOOTAGE.json").write_text(json.dumps(qa,indent=2))
credits=(
 "STRANGE, BUT VERIFIED -- Ophiocordyceps Documentary V5, MORE REAL RESEARCH FOOTAGE\n\n"
 "NEW PRIMARY RESEARCH 1: de Bekker et al. (2014) Species-specific ant brain manipulation "
 "by a specialized fungal parasite. BMC Evolutionary Biology 14, 166. CC BY 4.0. "
 "DOI: 10.1186/s12862-014-0166-3. Original supplementary video MOESM2_ESM.mov. "
 "Converted to MP4 and edited/cropped for documentary use.\n"
 "NEW PRIMARY RESEARCH 2: same article, original supplementary video MOESM3_ESM.mov. "
 "Converted to MP4. Original portrait proportions preserved with a blurred extension of "
 "the SAME MOVING SOURCE at the same time (not a repeated excerpt).\n"
 "RESEARCH FOOTAGE FROM V4: Hughes et al. (2011), BMC Ecology 11:13, CC BY 2.0, "
 "DOI: 10.1186/1472-6785-11-13.\n"
 "OTHER ANT/FOREST FOOTAGE: licensed Pexels stock, DIFFERENT species, illustrative only.\n"
 "MUSIC/NATURE AUDIO: copied bit-identically from V4; see V4 AUDIO_LICENSES.json.\n"
 "VIDEO: 2 previously illustrative clips fully removed, replaced with genuine "
 "infected-ant lab motion footage. No footage repeated, no static photographs.\n")
(OUT/"CREDITS_AND_SCIENTIFIC_SOURCES.txt").write_text(credits)
src_sub=ROOT/"v4_input"/"SUBTITLES_EN.srt"
src_v4_qa=ROOT/"v4_input"/"QA_V4.json"
if src_sub.is_file():shutil.copyfile(src_sub,OUT/"SUBTITLES_EN.srt")
if src_v4_qa.is_file():shutil.copyfile(src_v4_qa,OUT/"V4_BASE_QA.json")
for name,timepos in [
 ("opening_unchanged",2.0),("the_death_grip_new_castaneus",s1["at"]+R1/F/2),
 ("real_infected_americanus",s2["at"]+R2/F/2),
 ("closing_unchanged",min(out_duration-5,230))
]:
    execute(["ffmpeg","-v","error","-y","-ss",str(timepos),"-i",str(MASTER),
       "-frames:v","1",str(OUT/(name+".jpg"))])
print("V5 FINAL QA PASS",json.dumps(qa,indent=2),flush=True)
