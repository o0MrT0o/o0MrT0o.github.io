#!/usr/bin/env python3
"""Strange But Verified — V7 balanced nature/music re-mix.
Reconstructs the original Kokoro voice from unmodified 7 chapter WAVs with
original 6 chapter pauses. Carefully allocates the soundstage:
Voice foreground, CC0 film score behind voice via sidechain ducking,
authentic forest bed under score, occasional bird / wind / crickets accents.
V6's video bitstream is COPIED exactly. No video edit or repetition added.
"""
import array, hashlib, json, math, os, re, shutil, subprocess, time, urllib.request, wave
from pathlib import Path
ROOT=Path.cwd();IN=ROOT/"v7_input";WORK=ROOT/"v7_work";OUT=ROOT/"v7_output"
for d in (IN,WORK,OUT):d.mkdir(exist_ok=True)
FILM=IN/"SBV_ZOMBIE_ANT_V6_EXTRA_REAL_STAGGERING_FOOTAGE.mp4"
MASTER=OUT/"SBV_ZOMBIE_ANT_V7_BALANCED_NATURE_SOUND.mp4"
CHAPTERS=["00_COLD_OPEN","01_THE_INFECTION","02_THE_CLIMB","03_THE_DEATH_GRIP",
          "04_THE_IMPOSSIBLE_DISCOVERY","05_AFTER_DEATH","06_FINAL_TWIST"]
GAPS=[0.0,4.4,2.8,2.8,4.9,4.9,2.8]
LICENSES={
 "score1":("https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/UDu2MITfQLDYrPAQl83OVpBn4ahW10HvNtHRn3kl.mp3",
 "John Bartmann, dark-highway-master, CC0, via Free Music Archive"),
 "score2":("https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/veCj5PdYajKUZxwu9Juf5HL19kRsXBDmuN28gJWS.mp3",
 "John Bartmann, dark-dyne-master, CC0, via Free Music Archive"),
 "forest":("https://bigsoundbank.com/UPLOAD/mp3/0100.mp3",
 "Joseph Sardin, Forest, authentic recorded woodland ambience, CC0, bigsoundbank.com/forest-s0100.html"),
 "birds":("https://opengameart.org/sites/default/files/birds-isaiah658_0.ogg",
 "isaiah658, Ambient Bird Sounds, CC0, opengameart.org/content/ambient-bird-sounds"),
 "wind":("https://opengameart.org/sites/default/files/Birds%20and%20Wind%20-%20Ambient_1.ogg",
 "Spring Spring, Birds and Wind Ambient, CC0, opengameart.org/content/birds-and-wind-ambient-birds-wind-and-synth"),
 "crickets":("https://opengameart.org/sites/default/files/crickets_1.mp3",
 "Wolfgang_, Crickets Ambient Noise Loopable, CC0, opengameart.org/content/crickets-ambient-noise-loopable")
}
def execute(args,quiet=True):
 p=subprocess.run([str(i) for i in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:
  print("FFMPEG ERROR:\n"+p.stderr[-4500:],flush=True)
  raise RuntimeError("Command failed: "+str(args[:9]))
 if not quiet:print("OK",args[:8],flush=True)
 return p.stdout,p.stderr
def duration(path):
 _,err=execute(["ffmpeg","-hide_banner","-i",path],True) if False else ("",subprocess.run(["ffmpeg","-hide_banner","-i",str(path)],text=True,capture_output=True).stderr)
 m=re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",err)
 if not m:raise RuntimeError("Unknown duration: "+str(path)+" "+err[-200:])
 return int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))
def hashstream(path,spec):
 stdout,_=execute(["ffmpeg","-v","error","-i",path,"-map",f"0:{spec}:0",
     "-c","copy","-f","hash","-hash","SHA256","-"])
 return stdout.strip()
def download(url,path):
 error=""
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0","Accept":"*/*"})
   with urllib.request.urlopen(req,timeout=70) as response,open(path,"wb") as file:
    shutil.copyfileobj(response,file,1024*1024)
   if path.stat().st_size<10_000:raise RuntimeError("Downloaded audio is too small")
   return
  except Exception as exc:
   error=str(exc)
   if path.exists():path.unlink()
   print("AUDIO RETRY",path.name,attempt,error[:110],flush=True)
   time.sleep(2)
 raise RuntimeError(f"Original CC0 sound unavailable: {url}: {error}")
assert FILM.is_file() and FILM.stat().st_size>50_000_000
film_time=duration(FILM)
assert 240<film_time<249,film_time
sha_video_v6=hashstream(FILM,"v")
print("V6 video unchanged source confirmed",round(film_time,3),"s",sha_video_v6,flush=True)
narration=WORK/"KOKORO_AF_HEART_EXACT_CHAPTERS_AND_SILENCES.wav"
timings=[];sr=24000;cursor=0
with wave.open(str(narration),"wb") as wout:
 wout.setnchannels(1);wout.setsampwidth(3);wout.setframerate(sr)
 for i,(chapter,gap) in enumerate(zip(CHAPTERS,GAPS)):
  pad=round(gap*sr)
  if pad:wout.writeframesraw(bytes(3*pad));cursor+=pad
  start=cursor/sr
  src=IN/(chapter+".wav")
  if not src.is_file():raise RuntimeError("Original approved Kokoro chapter missing: "+str(src))
  with wave.open(str(src),"rb") as wav:
   assert wav.getframerate()==sr and wav.getnchannels()==1 and wav.getsampwidth()==3
   n=wav.getnframes()
   assert n>3*sr
   wout.writeframesraw(wav.readframes(n));cursor+=n
  end=cursor/sr
  timings.append({"chapter":chapter,"voice_start":round(start,4),"voice_end":round(end,4),"gap_sec":gap})
voice_time=cursor/sr
assert abs(voice_time-film_time)<0.17,("Narration time and movie duration shifted",voice_time,film_time)
# Verify long wordless title gap contains absolutely NO narrator signal
with wave.open(str(narration),"rb") as wav:
 gap_start=timings[1]["voice_start"]-GAPS[1]
 wav.setpos(round((gap_start+0.4)*sr))
 no_voice=wav.readframes(round(2.2*sr))
 assert no_voice and not any(no_voice),"Voice enters cinematic title prematurely"
print("ORIGINAL KOKORO PRESERVED",round(voice_time,2),"s, verified 4.4-sec silent title gap",flush=True)
paths={};info={}
for k,(url,rights) in LICENSES.items():
 path=WORK/(k+".source")
 download(url,path)
 d=duration(path)
 if (k.startswith("score") and d<126) or (k=="forest" and d<20) or (k=="birds" and d<5) or (k=="crickets" and d<4) or (k=="wind" and d<6):
  raise RuntimeError("Unexpectedly short/invalid recording: "+k+" "+str(d))
 paths[k]=path
 info[k]={"url":url,"license":rights,"length_s":d,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
 print("AUTHENTIC AUDIO VERIFIED",k,round(d,2),"s",flush=True)

# Sound-stage design. This is NOT 6 tracks competing at the same volume.
# Music -25 LUFS, continuous recorded forest -32.5 LUFS, short animal cues
# about -37 to -40 LUFS, and narrator -17 LUFS (the listener's focus).
# Sidechain automatically ducks music 5-9dB under speech, forest more mildly.
# Subtle one-off accents introduce the local ecosystem; unlike V4, four
# nature recordings never run at high volume simultaneously.
filters=[
 "[1:a]aresample=48000,aformat=channel_layouts=stereo,"
 "highpass=f=70,lowpass=f=10000,loudnorm=I=-17:TP=-2.7:LRA=8,"
 "asplit=3[voice][voice_key_score][voice_key_forest]",
 "[2:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:124.5,asetpts=PTS-STARTPTS[s1]",
 "[3:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:125.0,asetpts=PTS-STARTPTS[s2]",
 f"[s1][s2]acrossfade=d=4.5:c1=tri:c2=tri,"
 f"highpass=f=75,lowpass=f=7500,loudnorm=I=-25:TP=-5:LRA=10,"
 f"afade=t=in:st=0:d=2.3,afade=t=out:st={film_time-4.2:.3f}:d=4.2[score]",
 "[score][voice_key_score]sidechaincompress=threshold=0.024:ratio=6:attack=75:release=700[score_below_voice]",
 f"[4:a]aresample=48000,aformat=channel_layouts=stereo,"
 f"atrim=0:{film_time:.3f},highpass=f=105,lowpass=f=4800,"
 f"loudnorm=I=-32.5:TP=-7:LRA=8,"
 f"afade=t=in:st=0:d=3,afade=t=out:st={film_time-6:.3f}:d=6[forest_raw]",
 "[forest_raw][voice_key_forest]sidechaincompress=threshold=0.026:ratio=2.7:attack=110:release=880[forest_below_voice]",
 # Short real bird phrase at ~48 s, not incessant repetitive birds through whole film.
 "[5:a]aresample=48000,aformat=channel_layouts=stereo,"
 "atrim=0:5.8,asetpts=PTS-STARTPTS,highpass=f=620,lowpass=f=6000,"
 "loudnorm=I=-37.5:TP=-12:LRA=7,afade=t=in:st=0:d=1,"
 "afade=t=out:st=4.8:d=1,adelay=48000|48000[birds_accent]",
 # Soft wind mid-film during explanation, used once.
 "[6:a]aresample=48000,aformat=channel_layouts=stereo,"
 "atrim=0:8.5,asetpts=PTS-STARTPTS,highpass=f=140,lowpass=f=4600,"
 "loudnorm=I=-37:TP=-11:LRA=7,afade=t=in:st=0:d=1.7,"
 "afade=t=out:st=6.5:d=2,adelay=135000|135000[wind_accent]",
 # One soft 5 s cricket accent much later, never permanent chirping.
 "[7:a]aresample=48000,aformat=channel_layouts=stereo,"
 "atrim=0:5,asetpts=PTS-STARTPTS,highpass=f=450,lowpass=f=7100,"
 "loudnorm=I=-40:TP=-13:LRA=7,afade=t=in:st=0:d=1.1,"
 "afade=t=out:st=3.9:d=1.1,adelay=205000|205000[crickets_accent]",
 "[voice][score_below_voice][forest_below_voice][birds_accent][wind_accent][crickets_accent]"
 "amix=inputs=6:duration=first:dropout_transition=0:normalize=0,"
 "alimiter=limit=0.93,loudnorm=I=-16:TP=-1.6:LRA=10[aout]"
]
# Intro and pauses get un-ducked music naturally: narrator's input is silence.
# Copy exact source H.264 packet stream: all 20 real-video files, timestamps,
# cinematic title, chapter transitions and 0 repeats remain unchanged.
ff=[
 "ffmpeg","-hide_banner","-loglevel","error","-y",
 "-i",str(FILM),"-i",str(narration),
 "-i",str(paths["score1"]),"-i",str(paths["score2"]),
 "-stream_loop","-1","-i",str(paths["forest"]),
 "-i",str(paths["birds"]),"-i",str(paths["wind"]),"-i",str(paths["crickets"]),
 "-filter_complex",";".join(filters),"-map","0:v:0","-map","[aout]",
 "-c:v","copy","-c:a","aac","-b:a","256k","-ar","48000",
 "-movflags","+faststart","-t",f"{film_time:.3f}",str(MASTER)
]
print("BALANCED V7 AUDIO RENDER - visual bitstream copy, 6 soundtrack components",flush=True)
execute(ff)
if not MASTER.is_file() or MASTER.stat().st_size<50_000_000:raise RuntimeError("Master MP4 missing")
out_time=duration(MASTER)
if abs(out_time-film_time)>.17:raise RuntimeError("Film length shifted")
hash_v7=hashstream(MASTER,"v")
if hash_v7!=sha_video_v6:raise RuntimeError("Video bitstream changed - forbiddensh: "+sha_video_v6+" vs "+hash_v7)
execute(["ffmpeg","-hide_banner","-v","error","-xerror","-i",str(MASTER),"-f","null","-"])
print("FILM FULL-DECODE PASS; 20-source visual bitstream identical to V6",flush=True)

def rms_for_segment(start, seconds, outfile):
 execute(["ffmpeg","-v","error","-y","-ss",f"{start:.3f}","-i",str(MASTER),
          "-t",str(seconds),"-vn","-ac","1","-ar","16000","-f","s16le",str(outfile)])
 pcm=array.array("h")
 pcm.frombytes(outfile.read_bytes())
 return round(20*math.log10(max(1e-11,(sum(float(x)**2 for x in pcm)/len(pcm))**.5/32768)),2)
preview_moments={
 "opening_voice":(3.0,7.5),
 "title_music_no_voice":(timings[1]["voice_start"]-2.5,1.9),
 "chapter_2_narration":(timings[2]["voice_start"]+2,8.0),
 "later_forest_background":(timings[4]["voice_start"]+2,8.0)
}
measurements={}
for key,(at,amount) in preview_moments.items():
 measurements[key]=rms_for_segment(at,amount,WORK/(key+".pcm"))
 print("BALANCE CHECK",key,measurements[key],"dBFS RMS",flush=True)
if measurements["title_music_no_voice"]<-37.0:
 raise RuntimeError("Title score quieter than intended: "+str(measurements))
# Save 12-second voice+music QA excerpts only: no image stills, no additional
# repeated source material inserted in final master.
for key,at in [("A_OPENING_12_SECONDS",0.0),("B_CHAPTER_BREAK_12_SECONDS",timings[1]["voice_start"]-2.5),
               ("C_DEATH_GRIP_12_SECONDS",timings[3]["voice_start"]+1.5)]:
 execute(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",f"{at:.3f}",
          "-i",str(MASTER),"-t","12","-vn","-ac","2","-c:a","aac","-b:a","192k",
          str(OUT/(key+".m4a"))])
qa={
 "status":"PASS","file":MASTER.name,"size_bytes":MASTER.stat().st_size,
 "duration_seconds":round(out_time,3),"format":"MP4 H264(copy)+AAC 256k 48k stereo",
 "video_stream_sha256_v6":sha_video_v6,"video_stream_sha256_v7":hash_v7,
 "video_bitrate_unchanged":True,"visuals_exactly_as_v6":True,
 "source_videos":20,"source_video_repeat_count":0,"static_images":0,
 "kokoro":"original af_heart 7 chapter WAVs unmodified, silent chapter pauses rebuilt",
 "audio_mix":{"narrator_target_lufs":-17,"score_target_lufs":-25,
              "forest_target_lufs":-32.5,
              "nature_accents_lufs":[-37.5,-37,-40],
              "ducking":"sidechain compressor driven by narration: music strong, forest gentle",
              "field_sounds":"real CC0 forest continuously; 1x birds; 1x wind; 1x crickets",
              "music":"two original CC0 documentary tracks joined with crossfade",
              "looped_birds_and_other_prominent_effects":False},
 "title_voice_silence_verified":True,
 "music_audible_title_rms_dbfs":measurements["title_music_no_voice"],
 "audio_segment_rms_dbfs":measurements,
 "full_ffmpeg_decode":"PASS"
}
(OUT/"V7_AUDIO_BALANCE_QA.json").write_text(json.dumps(qa,indent=2))
(OUT/"V7_AUDIO_SOURCE_LICENSES.json").write_text(json.dumps(info,indent=2))
(OUT/"ORIGINAL_CHAPTER_TIMINGS.json").write_text(json.dumps(timings,indent=2))
for source,dest in [
 (IN/"SUBTITLES_EN.srt","SUBTITLES_EN.srt"),
 (IN/"NO_REPEAT_EDL_V6.json","NO_REPEAT_EDL_V6.json"),
 (IN/"QA_V6_REAL_OPHIOCORDYCEPS.json","QA_V6_REAL_OPHIOCORDYCEPS.json"),
 (IN/"CREDITS_SCIENTIFIC_SOURCES_V6.txt","CREDITS_SCIENTIFIC_SOURCES_V6.txt")]:
 if source.is_file():shutil.copy2(source,OUT/dest)
print("FINAL V7 BALANCED MIX SUCCESS",json.dumps(qa,indent=2),flush=True)
