#!/usr/bin/env python3
"""Strange But Verified / The Exploding Cucumber: authentic 2024 research footage, Kokoro, FFmpeg."""
from pathlib import Path
import json,re,subprocess,shutil,math
import numpy as np, soundfile as sf
from PIL import Image,ImageDraw
from scipy.signal import lfilter,butter,sosfilt
# Download licensed supplementary movies from PNAS/PMC via Europe PMC; fail closed if absent.
import sbv_ecballium_probe_20261107 as research
D=Path('ecballium_media')
WK=Path('ecballium_work');WK.mkdir(exist_ok=True)
OUT=Path('ecballium_output');OUT.mkdir(exist_ok=True)
W,H,FPS=1080,1920,30
S1=D/'pnas.2410420121.sm01.mov' # medical CT visualization; 1280x720 68s
S2=D/'pnas.2410420121.sm02.mov' # actual timelapse 1072x712 6.67s
S3=D/'pnas.2410420121.sm03.avi' # original 8600-fps research, vertical 480x768 17.8s
for p in (S1,S2,S3):
 assert p.exists() and p.stat().st_size>1500000,'MISSING VERIFIED AUTHENTIC VIDEO '+str(p)
PHRASES=[
 "That looks like an explosion. But it's a plant.",
 "Meet the squirting cucumber.",
 "Inside the fruit, pressure builds as it ripens.",
 "Then it detaches, shooting seeds at forty-five miles per hour.",
 "The whole launch takes just thirty milliseconds.",
 "Some seeds travel as far as ten metres.",
 "Researchers needed ultra-fast cameras to see how it works.",
 "Nature built a seed cannon."
]
VISUALS=[
 (S3,0.25,.50,'THE EXPLOSION'),       # actual fruit is visibly ejecting from the first frame
 (S2,.15,.19,'THE PLANT'),            # real green plant filmed over days
 (S1,15.2,.50,'INSIDE THE FRUIT'),   # CT seeds become visible
 (S3,7.05,.51,'THE SEEDS'),          # continuing original jet, no overlap with opener
 (S3,-1.00,.51,'30 MILLISECONDS'),   # time assigned dynamically after phrase 3
 (S2,3.05,.74,'10 METRES'),          # green mature fruit
 (S1,26.4,.50,'SCIENCE'),            # CT at different timeline portion
 (S3,-2.00,.51,'THE SEED CANNON')    # unique S3 interval after opening, not repeated
]
def run(args,check=True):
 p=subprocess.run([str(x) for x in args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if check and p.returncode:raise RuntimeError('FFmpeg failed: '+str(args[:8])+'\n'+p.stderr[-2000:])
 return p.stdout,p.stderr
def media_info(p):
 o,_=run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',p])
 return json.loads(o)
def voice():
 from kokoro_onnx import Kokoro
 tts=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
 t=0.0;parts=[];sections=[];sr=24000
 for phrase in PHRASES:
  wave,n=tts.create(phrase,voice='af_heart',speed=.88,lang='en-us',trim=True,continuous=True)
  assert n==sr,(phrase,n)
  a=np.asarray(wave,dtype=np.float32).reshape(-1)
  assert len(a)>sr*.5
  gap=.09
  parts.append(a);parts.append(np.zeros(round(sr*gap),dtype=np.float32))
  sections.append({'text':phrase,'start':t,'vo_end':t+len(a)/sr,'end':t+len(a)/sr+gap})
  t+=len(a)/sr+gap
 wave=np.concatenate(parts)
 path=OUT/'SBV_ECBALLIUM_KOKORO_AF_HEART.wav'
 sf.write(path,wave,sr,subtype='PCM_24')
 return path,sections,len(wave)/sr
def fmt(s):
 cs=max(0,int(round(float(s)*100)))
 return f'{cs//360000}:{(cs//6000)%60:02}:{(cs//100)%60:02}.{cs%100:02}'
def captions(sections,total):
 p=WK/'subtitles.ass'
 lines=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920',
 'WrapStyle: 2','ScaledBorderAndShadow: yes','','[V4+ Styles]',
 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
 'Style: Caps,Montserrat,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0.2,0,1,5,2,5,65,65,700,1',
 'Style: Hook,Montserrat,78,&H0017D5FF,&H0017D5FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,2,5,65,65,1250,1',
 'Style: Brand,Montserrat,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,7,20,20,20,1',
 'Style: Stat,Montserrat,71,&H0000D8FF,&H0000D8FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,5,70,70,1330,1',
 '','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 def add(start,end,style,text,layer=0):
  if end>start:lines.append(f'Dialogue: {layer},{fmt(start)},{fmt(end)},{style},,0,0,0,,{text}')
 add(0,total,'Brand',r'{\an7\pos(36,87)}STRANGE, BUT VERIFIED  /  PNAS 2024')
 add(0,min(2.6,total),'Hook',r'{\an5\pos(540,440)\fad(50,110)}IT\'S A PLANT.',layer=0)
 yellow={'explosion','plant','cucumber','pressure','detaches','seeds','forty-five','miles','hour','thirty','milliseconds','ten','metres','cameras','cannon'}
 for sec in sections:
  words=sec['text'].split();groups=[];part=[]
  for w in words:
   part.append(w)
   if len(part)>=4 or (w.endswith(('.', '!', '?')) and len(part)>=2):
    groups.append(part);part=[]
  if part:groups.append(part)
  wt=[sum(max(3,len(w.strip('.,!?'))) for w in g) for g in groups]
  cursor=sec['start'];s=sum(wt)
  for i,g in enumerate(groups):
   nxt=sec['vo_end'] if i==len(groups)-1 else cursor+(sec['vo_end']-sec['start'])*wt[i]/s
   colored=[]
   for w in g:
    if w.lower().strip('.,!?:') in yellow:colored.append(r'{\c&H0000D8FF&}'+w+r'{\c&H00FFFFFF&}')
    else:colored.append(w)
   txt=r'{\an5\pos(540,1210)\fad(35,60)}'+' '.join(colored)
   add(max(0,cursor-.025),min(total,nxt+.08),'Caps',txt,1)
   cursor=nxt
 stats=[(3,'45 MPH / 20 M/S'),(4,'0.030 SECONDS'),(5,'UP TO 10 METRES')]
 for idx,label in stats:
  st=sections[idx]['start']+.2
  en=min(sections[idx]['end']-.12,st+1.75)
  add(st,en,'Stat',r'{\an5\pos(540,440)\fad(90,180)}'+label,2)
 p.write_text('\n'.join(lines),encoding='utf-8')
 return p
def bed(sections,total):
 """Original, deliberately restrained ambient + nature-like rustling + short pressure releases.
 No external copyrighted audio."""
 sr=32000;n=int((total+.4)*sr);t=np.arange(n)/sr
 rng=np.random.default_rng(11072026)
 white=rng.standard_normal(n).astype(np.float32)
 wind=lfilter([.0015],[1,-.9985],white)
 wind=np.clip(wind,-.6,.6)
 low=sosfilt(butter(2,[70,950],btype='bandpass',fs=sr,output='sos'),white)
 breeze=.033*wind+.005*low*(.75+.25*np.sin(2*np.pi*.13*t))
 tones=.010*np.sin(2*np.pi*55*t)+.006*np.sin(2*np.pi*82.407*t)
 # Speech is always foreground; single restrained impact from the opening explosion.
 fx=np.zeros_like(t)
 for at,amp in [(0.06,.13),(sections[3]['start']+.1,.075),(sections[7]['start']+.1,.065)]:
  start=int(sr*at);length=min(n-start,int(sr*.42))
  if length<=0:continue
  k=np.arange(length)/sr
  fx[start:start+length]+=(amp*np.exp(-13*k)*np.sin(2*np.pi*(65-14*k)*k)).astype('float32')
 mix=(breeze+tones+fx).astype('float32')
 fade=np.minimum(1,np.maximum(0,(total-t)/.65))
 mix*=fade
 p=WK/'original_ambient_sound.wav'
 sf.write(p,mix,sr)
 return p
def clip(src,start,duration,i,focus,label):
 p=WK/f'{i:02d}.mp4'
 # Zoom and crop while retaining real footage, no generated filler.
 # Source S3 is already vertical; S1/S2 subject tracking is centered on crop focus.
 filt=(f'fps=30,scale=-2:1920:flags=lanczos,'
       f'crop=1080:1920:(iw-1080)*{focus:.4f}:0,'
       f'eq=contrast=1.055:saturation=1.05,format=yuv420p')
 run(['ffmpeg','-hide_banner','-v','error','-y','-ss',f'{start:.4f}',
      '-i',src,'-t',f'{duration:.4f}','-an','-vf',filt,'-r',FPS,
      '-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',
      '-video_track_timescale','30000',p])
 o=media_info(p);v=next(x for x in o['streams'] if x['codec_type']=='video')
 assert v['width']==W and v['height']==H and float(o['format']['duration'])>duration-.10
 print('EDIT',i,label,'at',start,'for',duration,flush=True)
 return p
def main():
 voicepath,secs,total=voice()
 print('VOICE',total,'seconds',flush=True)
 assert 17<total<34,total
 # Ensure all original source intervals are unique and valid; no reuse of exact frames.
 v=VISUALS.copy()
 v[4]=(S3,7.05+(secs[3]['end']-secs[3]['start'])+.16,.51,'30 MILLISECONDS')
 v[7]=(S3,.25+(secs[0]['end']-secs[0]['start'])+.18,.51,'THE SEED CANNON')
 ppath=[];edl=[];ranges={}
 for i,(source,st,focus,label) in enumerate(v):
  sec=secs[i];duration=round(sec['end']-sec['start'],5)
  sourceinfo=media_info(source)
  maxd=float(sourceinfo['format']['duration'])
  assert st>0 and st+duration<maxd-.04,(source,st,duration,maxd)
  prior=ranges.setdefault(source.name,[])
  for a,b in prior:assert st>=b+.01 or st+duration<=a-.01,(source.name,st,duration,prior)
  prior.append((st,st+duration))
  ppath.append(clip(source,st,duration,i,focus,label))
  edl.append({'beat':i,'screen':'real source movie','source':source.name,'source_in':st,'duration':duration,
              'timeline_start':sec['start'],'description':label})
 concat=WK/'concat.txt';concat.write_text(''.join("file '"+str(p.resolve())+"'\n" for p in ppath))
 join=WK/'picture.mp4'
 run(['ffmpeg','-hide_banner','-v','error','-y','-safe','0','-f','concat','-i',concat,'-c','copy',join])
 ass=captions(secs,total);amb=bed(secs,total)
 mp4=OUT/'SBV_EXPLODING_CUCUMBER_KOKORO_FINAL.mp4'
 fa=("[1:a]aresample=48000,highpass=f=85,volume=1.18,acompressor=threshold=0.14:ratio=1.8:attack=10:release=130[v];"
     "[2:a]aresample=48000,volume=0.20[a];[v][a]amix=inputs=2:duration=first:normalize=0,"
     "loudnorm=I=-16:TP=-1.7:LRA=8[master]")
 run(['ffmpeg','-hide_banner','-v','error','-y','-i',join,'-i',voicepath,'-i',amb,
      '-filter_complex',fa,'-vf',f'ass={ass.resolve()}',
      '-map','0:v:0','-map','[master]',
      '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r','30',
      '-c:a','aac','-b:a','192k','-ar','48000',
      '-movflags','+faststart','-t',f'{total:.3f}',mp4])
 run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',mp4,'-f','null','-'])
 data=media_info(mp4)
 va=next(s for s in data['streams'] if s['codec_type']=='video')
 au=next(s for s in data['streams'] if s['codec_type']=='audio')
 dur=float(data['format']['duration'])
 assert (va['width'],va['height'])==(W,H)
 assert au['codec_name']=='aac'
 assert abs(dur-total)<.55,(dur,total)
 assert mp4.stat().st_size>3000000
 _,audioqa=run(['ffmpeg','-hide_banner','-nostats','-i',mp4,
   '-af','ebur128=peak=true','-vn','-f','null','-'])
 _,blackqa=run(['ffmpeg','-hide_banner','-nostats','-i',mp4,
   '-vf','blackdetect=d=0.14:pix_th=0.08','-an','-f','null','-'])
 black=[line.strip() for line in blackqa.splitlines() if 'black_start:' in line]
 qa={'status':'PASS','file':mp4.name,'duration_sec':dur,'width':W,'height':H,'fps':FPS,
     'size_bytes':mp4.stat().st_size,
     'voice':'Kokoro-82M v1.0 af_heart, en-US speed 0.88','voice_sec':total,
     'video_codec':va['codec_name'],'audio_codec':au['codec_name'],
     'source':'Box, Moulton, Vella et al (2024) PNAS e2410420121; Movie S1 S2 S3; CC BY 4.0',
     'all_video_authentic':True,'scene_repetitions':0,'source_frame_overlap_count':0,
     'full_decode':'PASS','black_events':black,
     'audio_loudness_summary':audioqa[-2100:],
     'edl':edl}
 (OUT/'QA.json').write_text(json.dumps(qa,indent=2))
 (OUT/'SOURCES_AND_LICENSES.txt').write_text(
  'Footage: Box F, Moulton DE, Vella D, Bhagotra Y, Lowe T, Goriely A, Thorogood CJ (2024). '
  'Uncovering the mechanical secrets of the squirting cucumber. Proceedings of the National Academy of Sciences 121(50), e2410420121. '
  'DOI: https://doi.org/10.1073/pnas.2410420121\n'
  'Research supplementary Movie S1 (CT scan), Movie S2 (timelapse), Movie S3 (slow-motion seed ejection), '
  'downloaded from https://pmc.ncbi.nlm.nih.gov/articles/PMC11648854/\n'
  'Article and supplementary research materials are distributed under Creative Commons Attribution 4.0: '
  'https://creativecommons.org/licenses/by/4.0/\n'
  'Changes made: cropped to vertical, scene excerpts selected/reordered, subtitles, original synthesized sound bed, generated Kokoro narration and color adjustment. '
  'The original 8600fps Movie S3 is monochrome 480x768: output upscale is not genuine 4K.\n'
  'No Oxford/Manchester press-only footage or stock footage is used.\n')
 (OUT/'NARRATION.txt').write_text(' '.join(PHRASES))
 shutil.copyfile(ass,OUT/'CAPTIONS.ass')
 sheet=Image.new('RGB',(4*270,3*500),'#101820')
 draw=ImageDraw.Draw(sheet)
 ts=[0,.55,1.4,2.6,4.3,6.2,8.6,11.4,14.1,17.2,20.3,max(.1,dur-.3)]
 for idx,t in enumerate(ts):
  t=min(t,max(.1,dur-.1))
  frame=WK/f'qa_{idx:02d}.jpg'
  run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',mp4,'-frames:v','1',frame])
  with Image.open(frame) as im:
   im.thumbnail((270,475));x=(idx%4)*270;y=(idx//4)*500
   sheet.paste(im,(x+(270-im.width)//2,y))
   draw.text((x+8,y+478),f'{t:.1f}s',fill='white')
 sheet.save(OUT/'CONTACT_SHEET.jpg',quality=89)
 print('SUCCESS',mp4,'duration',dur,'bytes',mp4.stat().st_size,'BLACK_EVENTS',len(black),flush=True)
if __name__=='__main__':main()
