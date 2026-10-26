#!/usr/bin/env python3
"""SBV zombie-ant V4: cinematic title + real CC0 forest/birds/crickets, 2-score mix.
Remixes verified V3 picture *without reusing or extending any source video*.
Adds no photos, animations, logos or unrelated video. The 20-source edit stays intact.
"""
from pathlib import Path
import array, hashlib, json, math, os, shutil, subprocess, time, urllib.request, wave
P=Path.cwd(); DIR=P/"v4_work"; OUT=P/"v4_output"
DIR.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
ORIGINAL=P/"v3_source"/"SBV_ZOMBIE_ANT_PITALA_STYLE_CHAPTERS_NO_REPEAT_FINAL.mp4"
OLD_EDL=P/"v3_source"/"NO_REPEAT_EDL.json"
OLD_QA=P/"v3_source"/"QA_REVISED_MASTER.json"
OLD_TIMINGS=P/"v3_source"/"VERIFIED_CHAPTER_AUDIO_TIMINGS.json"
AUDIO_SRC=P/"output"
MASTER=OUT/"SBV_ZOMBIE_ANT_V4_CINEMATIC_NATURE_FINAL.mp4"
def run(cmd,quiet=False):
 p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:
  print(p.stderr[-6000:],flush=True)
  raise RuntimeError(f"Command error {p.returncode}: {' '.join(str(x) for x in cmd[:8])}")
 if not quiet:print("OK",str(cmd[:6]),flush=True)
 return p.stdout.strip()
def probe(file):
 d=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(file)],True))
 return d, float(d["format"]["duration"])
assert ORIGINAL.is_file() and OLD_EDL.is_file() and OLD_QA.is_file() and OLD_TIMINGS.is_file()
oldqa=json.loads(OLD_QA.read_text())
assert oldqa["status"]=="PASS" and oldqa["source_reuse"]==0
edl=json.loads(OLD_EDL.read_text())
assert len(edl)==20 and len(set(k["file_id"] for k in edl))==20,"Repeated visuals would violate request."
dvid,duration=probe(ORIGINAL)
assert 235<duration<270
assert any(s["codec_type"]=="video" and s["width"]==1920 and s["height"]==1080 for s in dvid["streams"])
print("VERIFIED V3 VIDEO",duration,"sec, unique sources:",len(edl),flush=True)
timings=json.loads(OLD_TIMINGS.read_text())
assert len(timings)==7
title_start=float(timings[1]["pause_start"])
title_end=float(timings[1]["narration_start"])
assert 3.9<title_end-title_start<5
# Assemble EXACT Kokoro chapter WAVs, from original 2026-10-26 render, with
# existing V3 wordless gaps. Never re-synthesize or speed up the narrator.
voice=DIR/"kokoro_v4_pauses.wav"
sr=24000
with wave.open(str(voice),"wb") as o:
 o.setnchannels(1);o.setsampwidth(3);o.setframerate(sr)
 for chapter,t in enumerate(timings):
  gap=float(t["gap_sec"])
  n0=round(gap*sr)
  if n0:o.writeframesraw(bytes(n0*3))
  file=AUDIO_SRC/(t["source_wav"])
  assert file.is_file(),str(file)
  with wave.open(str(file),"rb") as w:
   assert w.getnchannels()==1 and w.getsampwidth()==3 and w.getframerate()==sr
   o.writeframesraw(w.readframes(w.getnframes()))
_,vlen=probe(voice)
assert abs(vlen-duration)<0.2,(vlen,duration)
print("KOKORO AUDIO ALIGNED",vlen,flush=True)

ASSETS={
"forest":([
 "https://bigsoundbank.com/UPLOAD/mp3/0100.mp3",
],"Joseph Sardin - Forest - original recorded nature/forest field recording - CC0 - https://bigsoundbank.com/forest-s0100.html",25),
"birds":([
 "https://opengameart.org/sites/default/files/birds-isaiah658_0.ogg",
 "https://opengameart.org/sites/default/files/birds-isaiah658.ogg",
],"isaiah658 - Ambient Bird Sounds - original field recording - CC0 - https://opengameart.org/content/ambient-bird-sounds",5),
"crickets":([
 "https://opengameart.org/sites/default/files/crickets_3.mp3",
 "https://opengameart.org/sites/default/files/crickets_1.mp3",
],"Wolfgang_ - Crickets Ambient Noise (CC0) - https://opengameart.org/content/crickets-general-calm-ambient-music",6),
"wind":([
 "https://opengameart.org/sites/default/files/Birds%20and%20Wind%20-%20Ambient_1.ogg",
],"Spring Spring - Birds and Wind Ambient - CC0 - https://opengameart.org/content/birds-and-wind-ambient-birds-wind-and-synth",8),
"score1":([
 "https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/UDu2MITfQLDYrPAQl83OVpBn4ahW10HvNtHRn3kl.mp3",
],"John Bartmann - dark-highway-master - CC0",125),
"score2":([
 "https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/veCj5PdYajKUZxwu9Juf5HL19kRsXBDmuN28gJWS.mp3",
],"John Bartmann - dark-dyne-master - CC0",125),
}
def download(url,dest):
 err=None
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; SBV-Documentary-Editor/1.0)","Accept":"*/*"})
   with urllib.request.urlopen(req,timeout=70) as response,open(dest,"wb") as o:
    shutil.copyfileobj(response,o,1024*1024)
   if dest.stat().st_size<10000:raise RuntimeError("Audio download is implausibly tiny.")
   return
  except Exception as e:
   err=str(e);print("RETRY",url[:100],attempt,err[:100],flush=True)
   if dest.exists():dest.unlink()
   time.sleep(2)
 raise RuntimeError(f"Unable to fetch source: {url}: {err}")
sources={}; meta={}
for key,(urls,credits,min_dur) in ASSETS.items():
 f=DIR/(key+".raw")
 err=[]
 for url in urls:
  try:
   if not f.exists():download(url,f)
   d,s=probe(f)
   if s<min_dur:raise RuntimeError(f"Audio shorter than required: {s}s vs {min_dur}s")
   if not any(x.get("codec_type")=="audio" for x in d["streams"]):raise RuntimeError("Not an audio file")
   sha=hashlib.sha256(f.read_bytes()).hexdigest()
   meta[key]={"source":url,"license":credits,"duration":round(s,3),"sha256":sha}
   sources[key]=f
   print("AUDIO SOURCE VERIFIED",key,round(s,2),"s",f.stat().st_size,sha[:9],flush=True)
   break
  except Exception as e:
   err.append(str(e))
   if f.exists():f.unlink()
 if key not in sources:
  if key in ("forest","birds","score1","score2"):
   raise RuntimeError(f"Mandatory real audio missing: {key} {err}")
  print("OPTIONAL NATURE SOUND UNAVAILABLE",key,flush=True)
# Real-world forest and bird audio mandatory: NO generated fake animal noises.
assert len(meta)>=4 and all(k in meta for k in ("forest","birds","score1","score2"))

# Cinema title: animated source V3 footage remains beneath title. Blur, darken
# and mask prior typographic overlay, then reveal restrained new typography.
# The source MOVES the entire time. Not a still frame, not a new video or replay.
T0=title_start+0.10;T1=title_end-0.13
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def alpha(a,b,fadein=.70,fadeout=.57):
 return (f"if(lt(t,{a:.3f}),0,if(lt(t,{a+fadein:.3f}),"
         f"(t-{a:.3f})/{fadein:.3f},"
         f"if(lt(t,{b-fadeout:.3f}),1,if(lt(t,{b:.3f}),"
         f"({b:.3f}-t)/{fadeout:.3f},0))))")
base=(f"fade=t=in:st=0:d=0.24,"
      f"gblur=sigma=15:steps=2:enable='between(t,{T0:.3f},{T1:.3f})',"
      f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.47:t=fill:enable='between(t,{T0:.3f},{T1:.3f})'")
def dt(text,size,y,a,b,color="0xFFFFFF",border=0):
 global base
 base+=(f",drawtext=fontfile={FONT}:text='{text}':fontsize={size}:fontcolor={color}:"
        f"alpha='{alpha(a,b)}':borderw={border}:"
        f"x=(w-text_w)/2:y={y}:enable='between(t,{a:.3f},{b:.3f})'")
dt("A STRANGE, BUT VERIFIED DOCUMENTARY",23,"h*0.35",T0+.25,T1-.12,color="0xD0CCC3")
dt("THE FUNGUS",83,"h*0.425",T0+.55,T1-.10)
dt("THAT CONTROLS ANTS",57,"h*0.535",T0+.85,T1-.07)
# Refined thin ochre cinematic accent, after major text.
base+=(f",drawbox=x=(w-260)/2:y=h*0.68:w=260:h=3:"
       f"color=0xD8BD7B@0.95:t=fill:enable='between(t,{T0+1.3:.3f},{T1-.45:.3f})'")
# Music: score 1 -> score 2, dramatic transition around midpoint.
music_1=min(124.5, duration*.55)
music_2=duration-music_1+4.5
assert music_2<125 and music_1<125
# Input map: 0 existing cinematic video; 1 ORIGINAL voice with genuine gaps;
# 2 score1; 3 score2; 4 real woodland ambience; 5 birds; 6 crickets (optional); 7 wind (optional).
inputs=["-i",str(ORIGINAL),"-i",str(voice),
        "-i",str(sources["score1"]),"-i",str(sources["score2"]),
        "-stream_loop","-1","-i",str(sources["forest"]),
        "-stream_loop","-1","-i",str(sources["birds"])]
audio_filters=[]
audio_filters.append(
 f"[2:a]aresample=48000,aformat=channel_layouts=stereo,"
 f"atrim=0:{music_1:.3f},asetpts=PTS-STARTPTS,volume=0.60[s1]")
audio_filters.append(
 f"[3:a]aresample=48000,aformat=channel_layouts=stereo,"
 f"atrim=0:{music_2:.3f},asetpts=PTS-STARTPTS,volume=0.60[s2]")
audio_filters.append(f"[s1][s2]acrossfade=d=4.5:c1=tri:c2=tri,afade=t=out:st={duration-6:.3f}:d=6[score]")
audio_filters.append("[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[vmain][vside]")
audio_filters.append("[score][vside]sidechaincompress=threshold=0.028:ratio=5.5:attack=60:release=450[duckscore]")
audio_filters.append(f"[4:a]aresample=48000,aformat=channel_layouts=stereo,"
                     f"atrim=duration={duration:.3f},volume=0.16,highpass=f=120,"
                     f"afade=t=in:st=0:d=1.8,afade=t=out:st={duration-5:.3f}:d=5[forest]")
audio_filters.append(f"[5:a]aresample=48000,aformat=channel_layouts=stereo,"
                     f"atrim=duration={duration:.3f},volume=0.125,highpass=f=380,"
                     f"afade=t=in:st=0:d=2.2,afade=t=out:st={duration-5:.3f}:d=5[birds]")
mix_inputs="[vmain][duckscore][forest][birds]"
mix_count=4
for key,vol,hp in (("crickets",0.05,500),("wind",0.065,140)):
 if key in sources:
  idx=len(inputs)//1
  # input number determined by ordered -i records, not list slots
  next_index=6 if key=="crickets" and "crickets" in sources else (7 if "crickets" in sources else 6)
  inputs+=["-stream_loop","-1","-i",str(sources[key])]
  audio_filters.append(f"[{next_index}:a]aresample=48000,"
           f"aformat=channel_layouts=stereo,atrim=duration={duration:.3f},"
           f"volume={vol},highpass=f={hp},afade=t=in:st=3:d=7,"
           f"afade=t=out:st={duration-6:.3f}:d=6[{key}]")
  mix_inputs+=f"[{key}]";mix_count+=1
audio_filters.append(f"{mix_inputs}amix=inputs={mix_count}:duration=first:normalize=0,"
                     f"alimiter=limit=0.94,loudnorm=I=-15:TP=-1.5:LRA=10[aout]")
filter_complex=";".join(audio_filters)
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",*inputs,
     "-filter_complex",filter_complex,"-map","0:v:0","-map","[aout]",
     "-vf",base,"-c:v","libx264","-preset","veryfast","-crf","20",
     "-r","30","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",
     "-ar","48000","-movflags","+faststart","-t",f"{duration:.3f}",str(MASTER)]
print("RENDERING V4 FROM 20-SHOT VERIFIED MASTER",len(cmd),"arguments",flush=True)
run(cmd)
# Machine level QA
run(["ffmpeg","-v","error","-xerror","-i",str(MASTER),"-f","null","-"],True)
dv,dout=probe(MASTER)
assert abs(dout-duration)<0.3
v=next(z for z in dv["streams"] if z["codec_type"]=="video")
a=next(z for z in dv["streams"] if z["codec_type"]=="audio")
assert (v["width"],v["height"])==(1920,1080)
assert a["codec_name"]=="aac"
assert MASTER.stat().st_size>30_000_000
# Silence is actually inserted in unmodified narrator track in the cinematic title gap
with wave.open(str(voice),"rb") as inp:
 offset=round((title_start+0.3)*sr);inp.setpos(offset)
 frames=inp.readframes(round(1.7*sr))
 assert not any(frames),"The planned documentary title contains voice speech!"
# The completed mix must contain audible music and ambience in title.
pcm=DIR/"title_audio.pcm"
run(["ffmpeg","-v","error","-y","-ss",f"{title_start+.5:.3f}","-i",str(MASTER),
     "-t","1.9","-vn","-ac","1","-ar","16000","-f","s16le",str(pcm)],True)
sample=array.array("h");sample.frombytes(pcm.read_bytes())
rms=math.sqrt(sum(float(x)**2 for x in sample)/len(sample))/32768
db=20*math.log10(max(1.e-12,rms))
assert db>-39, f"Title music muted: {db:.1f}dBFS"
# Frames inside title must actually MOVЕ (no freeze / static photo)
md5=run(["ffmpeg","-hide_banner","-v","error","-ss",f"{title_start+.7:.3f}",
  "-i",str(MASTER),"-t","1.0","-vf","fps=10,scale=320:180",
  "-f","framemd5","-"],True)
checks=set(line.split(",")[-1].strip() for line in md5.splitlines() if line and not line.startswith("#"))
assert len(checks)>=5, f"Title isn't moving! only {len(checks)} unique frame digests"
qa={"status":"PASS","file":MASTER.name,"duration_seconds":round(dout,2),
"file_bytes":MASTER.stat().st_size,"resolution":"1920x1080","fps":30,
"video_sources":20,"reused_video_sources":0,"still_images":0,
"source":"original QA-passed video V3; no scene reordered, repeated or extended",
"cinematic_intro":{"title_start":title_start,"title_end":title_end,"animated_real_footage":True,
                     "title_motion_unique_frame_hashes":len(checks),"music_rms_dbfs":round(db,2)},
"sound_design":{"real_recorded_nature_sounds":[k for k in sources if k in ("forest","birds","crickets","wind")],
                "music":[k for k in ("score1","score2")],
                "synthetic_nature_imitation":False,
                "music_sidechain_ducking":True,
                "nature_stereo_mix":True},
"voice":"original Kokoro-82M v1.0 af_heart WAV unchanged with verified chapter pauses",
"decoder_test":"PASS","subtitles":"original V3 SRT remains valid because video timeline has not been shifted"}
(OUT/"QA_V4.json").write_text(json.dumps(qa,indent=2))
(OUT/"AUDIO_LICENSES.json").write_text(json.dumps(meta,indent=2))
shutil.copy2(P/"v3_source"/"SUBTITLES_EN.srt",OUT/"SUBTITLES_EN.srt")
shutil.copy2(OLD_EDL,OUT/"NO_REPEAT_EDL.json")
shutil.copy2(OLD_TIMINGS,OUT/"VERIFIED_CHAPTER_AUDIO_TIMINGS.json")
print("FINAL V4 PASS",json.dumps(qa,indent=2),flush=True)
