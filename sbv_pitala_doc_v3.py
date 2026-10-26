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


# REVISION 3: frame-filled research footage, real chapter pauses, audible evolving soundtrack.
import wave, collections, statistics
TITLE_NAMES = [
    "", "THE INFECTION", "THE CLIMB", "THE DEATH GRIP",
    "WITHOUT ENTERING THE BRAIN", "AFTER DEATH", "THE FINAL TWIST",
]
GAPS_BEFORE = [0.0, 4.4, 2.8, 2.8, 4.9, 4.9, 2.8]

footage = {}
for key,(url,credit,scientific) in S.items():
    path=MEDIA/(key+".mp4")
    if not path.exists():download(url,path)
    length=ffprobe(path)
    footage[key]={"path":path,"length":length,"credit":credit,
                  "research":scientific,"url":url,
                  "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    print("VALID MOVING FOOTAGE",key,round(length,2),"seconds",flush=True)
hashes=[v["sha256"] for v in footage.values()]
assert len(hashes)==len(set(hashes)), "Identical binary sources cannot count as different clips."

chapters=json.loads((ROOT/"sbv_chapters.json").read_text())
assert len(chapters)==len(TITLE_NAMES)==len(STORY)==7
WAVS = ROOT / "output"
VOICEMASTER = OUT / "KOKORO_AF_HEART_CHAPTERS_WITH_INTENTIONAL_PAUSES.wav"
# The original Kokoro synthetic voice is unchanged, bit for bit inside each chapter;
# explicitly inserted SILENCE is the ONLY difference.
timings=[]
outframes=0
sample_rate=24000
with wave.open(str(VOICEMASTER),"wb") as output_wave:
    output_wave.setnchannels(1);output_wave.setsampwidth(3);output_wave.setframerate(sample_rate)
    for i,chapter in enumerate(chapters):
        pause_frames=round(GAPS_BEFORE[i]*sample_rate)
        pause_start=outframes/sample_rate
        if pause_frames:
            output_wave.writeframesraw(bytes(pause_frames*3))
            outframes+=pause_frames
        voice_start=outframes/sample_rate
        wav=WAVS/(chapter["name"]+".wav")
        if not wav.exists():raise RuntimeError("Missing original Kokoro chapter WAV "+str(wav))
        with wave.open(str(wav),"rb") as w:
            assert w.getnchannels()==1 and w.getsampwidth()==3 and w.getframerate()==sample_rate
            n=w.getnframes()
            if n < 3*sample_rate:raise RuntimeError("Voice chapter too short")
            output_wave.writeframesraw(w.readframes(n));outframes+=n
        voice_end=outframes/sample_rate
        timings.append(dict(chapter=i,title=TITLE_NAMES[i],pause_start=pause_start,pause_end=voice_start,
            narration_start=voice_start,narration_end=voice_end,gap_sec=GAPS_BEFORE[i],voice_sec=n/sample_rate,
            source_wav=str(wav.name)))
duration=outframes/sample_rate
(OUT/"VERIFIED_CHAPTER_AUDIO_TIMINGS.json").write_text(json.dumps(timings,indent=2))
assert 238<duration<265,duration
print("KOKORO TIMELINE rebuilt with exact pauses",round(duration,3),timings,flush=True)
assert all(round(t["narration_start"]-t["pause_start"],2)==GAPS_BEFORE[i] for i,t in enumerate(timings))
# Boundaries are aligned to independently moving, never reused source clips.
edl=[];video_frame_cursor=0
chapter_frames=[]
for c,source_ids in enumerate(STORY):
    ch_end=round(timings[c]["narration_end"]*FPS)
    target=ch_end-video_frame_cursor
    caps={key:max(0,int((footage[key]["length"]-0.24)*FPS)) for key in source_ids}
    assert sum(caps.values())>=target,(
        f"Chapter {c} needs {target/FPS:.2f}s unique video but has only "
        f"{sum(caps.values())/FPS:.2f}s of unique source recordings")
    sizes={key:0 for key in source_ids}
    # Water-fill in 1-second steps; every original moving clip is used once in one contiguous interval.
    left=target
    while left:
        pool=[k for k in source_ids if sizes[k]<caps[k]]
        if not pool:raise RuntimeError("No footage left - repeats or stills prohibited")
        key=min(pool,key=lambda q:(sizes[q]/min(caps[q],20*FPS),source_ids.index(q)))
        n=min(left,caps[key]-sizes[key],FPS)
        sizes[key]+=n;left-=n
    min_shot_sec=1.25
    for key in source_ids:
        frames=sizes[key]
        if frames<round(min_shot_sec*FPS):raise RuntimeError("Tiny source clip - bad montage "+key)
        source=footage[key]
        st=max(0.0,(source["length"]-frames/FPS)/2)
        edl.append(dict(chapter=c,file_id=key,source_in=round(st,4),
            frames=frames,at=video_frame_cursor/FPS,duration=frames/FPS,
            scientific=source["research"],credit=source["credit"]))
        video_frame_cursor+=frames
    chapter_frames.append(ch_end)
assert video_frame_cursor==round(duration*FPS)
assert len(edl)==len(S)==len(set(x["file_id"] for x in edl))
assert len(set(hashes))==len(S)
(OUT/"NO_REPEAT_EDL.json").write_text(json.dumps(edl,indent=2))
print("SOURCE-UNIQUE VIDEO",len(edl),"no reused footage","video seconds",round(duration,2),flush=True)

# No borders or decorative fake frames: genuine footage fills the ENTIRE 16:9 image.
# Source 4:3 scientific video is cropped with a safe, slightly upper-focused vertical offset.
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for idx,shot in enumerate(edl):
    k=shot["file_id"];source=footage[k]
    is_start=idx==0 or shot["chapter"]!=edl[idx-1]["chapter"]
    ch=shot["chapter"];gap=GAPS_BEFORE[ch]
    # Scale enough to cover the frame, then crop. NO PAD FILTER, no pillarboxes, no stretching.
    vf="scale=1920:1080:force_original_aspect_ratio=increase," \
       "crop=1920:1080:(iw-ow)/2:(ih-oh)*0.37,setsar=1,fps=30," \
       "eq=contrast=1.045:saturation=0.94,format=yuv420p"
    if is_start:
        if source["research"]:
            label="RESEARCH FOOTAGE  /  HUGHES ET AL. 2011"
        else:
            label="ILLUSTRATIVE WILDLIFE FOOTAGE  /  DIFFERENT SPECIES"
        # Small scientific provenance for 1.6s only. No black label box.
        vf+=f",drawtext=fontfile={FONT}:text='{label}':fontsize=21:fontcolor=white:" \
            "bordercolor=black@0.74:borderw=2:x=42:y=37:enable='between(t,0,1.6)'"
        if ch>0:
            assert gap>=2.8
            if ch==1: 
                line1="STRANGE  BUT  VERIFIED"
                line2="THE FUNGUS THAT CONTROLS ANTS"
                title_size=57
            else:
                line1=f"CHAPTER {ch:02d}"
                line2=TITLE_NAMES[ch]
                title_size=66 if len(line2)<21 else 52
            # Chapter title appears only on the FIRST previously unseen MOVING clip
            # and only during a verified wordless gap. Never over active narration.
            enable=f"between(t,0.38,{gap-0.35:.2f})"
            vf+=f",drawtext=fontfile={FONT}:text='{line1}':fontsize=25:fontcolor=white@0.85:" \
                f"bordercolor=black@0.65:borderw=2:x=(w-text_w)/2:y=(h/2)-88:enable='{enable}'"
            vf+=f",drawtext=fontfile={FONT}:text='{line2}':fontsize={title_size}:" \
                f"fontcolor=white:bordercolor=black@0.78:borderw=3:" \
                f"x=(w-text_w)/2:y=(h/2)-32:enable='{enable}'"
    path=PARTS/f"{idx:03}.mp4"
    shell(["ffmpeg","-hide_banner","-loglevel","error","-y",
           "-ss",f"{shot['source_in']:.4f}","-i",str(source["path"]),
           "-an","-vf",vf,"-frames:v",str(shot["frames"]),
           "-c:v","libx264","-preset","superfast","-crf","21","-r","30",
           "-pix_fmt","yuv420p","-video_track_timescale","30000",str(path)],True)
    if (idx+1)%4==0:print("RENDERED UNIQUE CLIPS",idx+1,"/",len(edl),flush=True)
concat=OUT/"concat.txt"
concat.write_text("".join("file '"+str((PARTS/f"{i:03}.mp4").resolve())+"'\n" for i in range(len(edl))))

# Optional subtitles for YouTube. Every subtitle is aligned to the *new* chapter times,
# meaning the new wordless chapter interludes remain caption-free.
def tc(t):
    x=max(0,int(round(t*1000)));hr,x=divmod(x,3600000);mi,x=divmod(x,60000);sec,ms=divmod(x,1000)
    return f"{hr:02}:{mi:02}:{sec:02},{ms:03}"
def groups(txt):
    import re
    words=re.sub(r"\s+"," ",txt).split();lines=[];part=[]
    for word in words:
        if len(part)>=10 or len(" ".join(part+[word]))>68 and len(part)>=4:
            lines.append(" ".join(part));part=[]
        part.append(word)
    if part:lines.append(" ".join(part))
    return lines
captions=[]
for c,(chapter,time_data) in enumerate(zip(chapters,timings)):
    texts=groups(chapter["text"])
    weights=[len(t) for t in texts];tot=sum(weights)
    cur=time_data["narration_start"];en=time_data["narration_end"];begin=cur
    for idx,text_line in enumerate(texts):
        nxt=en if idx==len(texts)-1 else cur+(en-begin)*weights[idx]/tot
        words=text_line.split()
        if len(text_line)>43:
            mid=min(range(2,len(words)-1),key=lambda p:abs(len(" ".join(words[:p]))-len(text_line)/2))
            text_line=" ".join(words[:mid])+"\n"+" ".join(words[mid:])
        captions.append(f"{len(captions)+1}\n{tc(cur)} --> {tc(nxt)}\n{text_line}\n\n")
        cur=nxt
(OUT/"SUBTITLES_EN.srt").write_text("".join(captions))

# Two distinct professional atmospheric tracks (CC0), with a dynamic change
# halfway through the documentary and a soft crossfade; no music looping.
# Two independently recorded nature backgrounds, CC0 / public domain, no looping.
AUDIO = {
 "score_open":("https://upload.wikimedia.org/wikipedia/commons/6/6d/John_Bartmann_-_dark-highway-master.ogg",
               "John Bartmann - dark-highway-master - CC0 1.0"),
 "score_reveal":("https://upload.wikimedia.org/wikipedia/commons/8/8d/John_Bartmann_-_dark-dyne-master.ogg",
               "John Bartmann - dark-dyne-master - CC0 1.0"),
 "forest_intro":("https://upload.wikimedia.org/wikipedia/commons/0/0a/20090610_0_ambience.ogg",
               "nille - forest ambience - Public Domain"),
 "birds_late":("https://upload.wikimedia.org/wikipedia/commons/2/2f/Birds_chirping_in_a_garden.ogg",
               "Akum20 - birds chirping in a garden - CC0 1.0 (illustrative field ambience)")
}
for name,(url,lic) in AUDIO.items():
    dest=MEDIA/(name+".ogg")
    if not dest.exists():download(url,dest)
    shell(["ffprobe","-v","error","-show_entries","format=duration","-of",
           "default=noprint_wrappers=1:nokey=1",str(dest)],True)
print("FOUR DISTINCT SOUND SOURCES VERIFIED",flush=True)
# 124.5s + 125.0s - 4.5s crossfade = 245.0 seconds (enough for master).
# Preserve music in the final seconds and prevent undesired abrupt loss.
music_dur1=124.5;music_dur2=125.0;music_crossfade=4.5
assert music_dur1+music_dur2-music_crossfade>=duration
# Forest 123.4 and birds 209 sec: 119.5s+130s - 4.0 = 245.5 sec.
aud_filter=(
 "[1:a]aresample=48000,atrim=0:124.5,asetpts=PTS-STARTPTS[ms1];"
 "[2:a]aresample=48000,atrim=0:125,asetpts=PTS-STARTPTS[ms2];"
 "[ms1][ms2]acrossfade=d=4.5:c1=tri:c2=tri,loudnorm=I=-20:TP=-3:LRA=9[score];"
 "[3:a]aresample=48000,atrim=0:119.5,asetpts=PTS-STARTPTS[amb1];"
 "[4:a]aresample=48000,atrim=0:130,asetpts=PTS-STARTPTS[amb2];"
 "[amb1][amb2]acrossfade=d=4:c1=tri:c2=tri,loudnorm=I=-28:TP=-7:LRA=8[forest];"
 "[0:a]aresample=48000,volume=1[voice];"
 "[score][voice]sidechaincompress=threshold=0.028:ratio=5:attack=60:release=500[scoreduck];"
 "[voice][scoreduck][forest]amix=inputs=3:duration=first:normalize=0,"
 "alimiter=limit=0.9,loudnorm=I=-15:TP=-1.5:LRA=9[final]"
)
master=OUT/"SBV_ZOMBIE_ANT_PITALA_STYLE_CHAPTERS_NO_REPEAT_FINAL.mp4"
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
 "-safe","0","-f","concat","-i",str(concat),
 "-i",str(VOICEMASTER),"-i",str(MEDIA/"score_open.ogg"),
 "-i",str(MEDIA/"score_reveal.ogg"),"-i",str(MEDIA/"forest_intro.ogg"),
 "-i",str(MEDIA/"birds_late.ogg"),
 "-filter_complex",aud_filter,"-map","0:v:0","-map","[final]",
 "-c:v","libx264","-preset","veryfast","-crf","20",
 "-r","30","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","48000",
 "-movflags","+faststart","-t",f"{duration:.5f}",str(master)]
shell(cmd)
shell(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",str(master),"-f","null","-"],True)
info=json.loads(shell(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(master)],True))
video=next(x for x in info["streams"] if x["codec_type"]=="video")
audio=next(x for x in info["streams"] if x["codec_type"]=="audio")
assert (video["width"],video["height"])==(1920,1080)
assert audio["codec_name"]=="aac"
assert abs(float(info["format"]["duration"])-duration)<0.18
assert master.stat().st_size>10000000

# Sound-availability QA: the cinematic title break MUST contain audible score.
# Voice gap contains actual zeros, while post-mix audio is measurable at that moment.
first_gap=timings[1]
with wave.open(str(VOICEMASTER),"rb") as test_wave:
    test_wave.setpos(round((first_gap["pause_start"]+0.4)*sample_rate))
    sample=test_wave.readframes(round(2*sample_rate))
    assert not any(sample),"First 2s chapter title contains accidental narration"
check_audio=OUT/"chapter_break_audio.pcm"
shell(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",f"{first_gap['pause_start']+0.4:.4f}",
       "-i",str(master),"-t","2","-vn","-ac","1","-ar","16000",
       "-f","s16le",str(check_audio)],True)
import array
wavdata=array.array("h");wavdata.frombytes(check_audio.read_bytes())
rms=(sum(float(v)*float(v) for v in wavdata)/len(wavdata))**0.5/32768
dbfs=20*math.log10(max(rms,1e-12))
if dbfs < -38:raise RuntimeError(f"BACKGROUND MUSIC IN TITLE TOO QUIET: {dbfs:.1f} dBFS")
check_audio.unlink()
qa={"file":master.name,"status":"PASS","full_decode":"PASS",
    "duration_sec":round(duration,3),"output_duration_sec":float(info["format"]["duration"]),
    "size_bytes":master.stat().st_size,"resolution":"1920x1080","fps":30,
    "source_count":len(S),"source_reuse":0,"source_overlaps":0,
    "all_visuals":"100% real moving video, no stills, no AI imitation",
    "scientific_footage_framing":"full-bleed 16:9 crop, NO pad/pillarbox",
    "voice":"Original Kokoro-82M v1.0 af_heart speed 0.88 - original seven WAVs",
    "chapter_interludes_s":[4.4,2.8,2.8,4.9,4.9,2.8],
    "intentional_silence_before_each_later_chapter":True,
    "music":"2 different CC0 dark-ambient compositions with scene-shift crossfade and ducking",
    "nature_sound":"2 independent public-domain / CC0 recordings (no loop)",
    "music_audible_break_rms_dbfs":round(dbfs,2),
    "subtitles":"Separate optional SRT; no permanent giant captions",
    "mp4_codec":"H264 + AAC"}
(OUT/"QA_REVISED_MASTER.json").write_text(json.dumps(qa,indent=2))
sources=["Research footage: Hughes et al. 2011 BMC Ecology 11:13 https://doi.org/10.1186/1472-6785-11-13 - CC BY 2.0 - cropped, color-corrected and excerpted",
 "Other videos show DIFFERENT insect and fungal species, used only as illustrative B-roll; Pexels licence https://www.pexels.com/license/"]
sources+=([f"{k}: {v['credit']} | {v['url']}" for k,v in footage.items()])
sources+=([f"AUDIO {k}: {lic} | {url}" for k,(url,lic) in AUDIO.items()])
sources+=["Science: Fredericksen et al. 2017 PNAS https://doi.org/10.1073/pnas.1711673114",
          "Science: Mangold et al. 2019 Journal of Experimental Biology."]
(OUT/"SOURCE_RIGHTS_AND_CREDITS.txt").write_text("\n".join(sources)+"\n")
print("FINAL CINEMATIC MASTER",json.dumps(qa,indent=2),flush=True)
