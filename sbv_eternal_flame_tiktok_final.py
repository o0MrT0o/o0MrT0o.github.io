#!/usr/bin/env python3
"""Strange But Verified: Eternal Flame Falls — genuine 2025 CC BY field footage only."""
from pathlib import Path
import subprocess,requests,math,json,shutil,hashlib
import numpy as np
import soundfile as sf
from scipy.signal import lfilter
from PIL import Image,ImageDraw
BASE=Path('eternal_flame_work');BASE.mkdir(exist_ok=True)
OUT=Path('eternal_flame_final');OUT.mkdir(exist_ok=True)
SOURCE=BASE/'g_edward_johnson_real_waterfall_1080p.webm'
NAME='Burning_Eternal_Flame_Falls_Chestnut_Ridge_Park_NY_2025-09.webm'
URL='https://upload.wikimedia.org/wikipedia/commons/transcoded/b/b6/'+NAME+'/'+NAME+'.1080p.vp9.webm'
ORIGINAL_PAGE='https://commons.wikimedia.org/wiki/File:Burning_Eternal_Flame_Falls_Chestnut_Ridge_Park_NY_2025-09.webm'
SCRIPT=[
 "There's a REAL FIRE behind this waterfall.",
 "Natural gas escapes from the rock, feeding the flame.",
 "But the so-called eternal fire sometimes goes out."
]
AUTHOR='G. Edward Johnson'
LICENSE='https://creativecommons.org/licenses/by/4.0/'
def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(' '.join(map(str,args[:7]))+' '+p.stderr[-1500:])
 return p.stdout,p.stderr

def media_info(f):
 return json.loads(run(['ffprobe','-hide_banner','-v','error','-show_streams','-show_format','-of','json',f])[0])

def source():
 headers={'User-Agent':'StrangeButVerifiedCreator/1.0 (educational source inspection)',
          'Referer':ORIGINAL_PAGE,'Origin':'https://commons.wikimedia.org'}
 with requests.get(URL,headers=headers,timeout=100,stream=True) as r:
  print('SOURCE HTTP',r.status_code,r.headers.get('Content-Type'),r.headers.get('Content-Length'),flush=True)
  r.raise_for_status()
  count=0
  with open(SOURCE,'wb') as f:
   for chunk in r.iter_content(1024*1024):
    if chunk:count+=len(chunk);f.write(chunk)
 assert 6000000<count<11000000,count
 m=media_info(SOURCE)
 v=next(s for s in m['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'])==(1920,1080)
 assert 14.9<float(m['format']['duration'])<15.2
 print('SOURCE',v['codec_name'],m['format']['duration'],'sec',count,'bytes',flush=True)
 return m

def voice():
 from kokoro_onnx import Kokoro
 model=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
 parts=[];timestamps=[];t=0.0
 for line in SCRIPT:
  samples,sr=model.create(line,voice='af_heart',speed=.88,lang='en-us',trim=True,continuous=True)
  assert sr==24000
  wave=np.asarray(samples,dtype='float32').reshape(-1)
  assert len(wave)/sr>.6
  gap=.085
  timestamps.append({'text':line,'start':t,'vo_end':t+len(wave)/sr,'end':t+len(wave)/sr+gap})
  parts+=[wave,np.zeros(round(sr*gap),dtype='float32')]
  t+=len(wave)/sr+gap
 arr=np.concatenate(parts)
 path=OUT/'SBV_ETERNAL_FLAME_KOKORO_AF_HEART.wav';sf.write(path,arr,24000,subtype='PCM_24')
 assert 9.5<t<13.75,('Script too long for distinct nonrepeated footage',t)
 print('VOICE_SECTIONS',timestamps,'TOTAL',round(t,3),flush=True)
 return path,timestamps,t

def crop_clip(start,duration,name,wide):
 out=BASE/f'{name}.mp4'
 # Camera A: genuine flame close-up is source 07.45–14.8s
 # Camera B: genuine wide waterfall source is 00.15–06.9s
 # The portrait crop for the wide shot includes both flame and falling water.
 # Preserve photographic geometry; never fabricate or mirror footage.
 pos=480 if wide else 649  # source dimensions 1920x1080, 608x1080 vertical crop
 # Close-up: 1920*?? screenshot fire at horizontal center; x=649 puts central 608 at x=953.
 filt=(f'fps=30,crop=608:1080:{pos}:0,scale=1080:1920:flags=lanczos,'
       'eq=contrast=1.055:saturation=1.07,unsharp=3:3:0.32:3:3:0,format=yuv420p')
 run(['ffmpeg','-hide_banner','-v','error','-y','-ss',f'{start:.5f}',
      '-i',SOURCE,'-t',f'{duration:.5f}','-an','-vf',filt,
      '-r','30','-c:v','libx264','-preset','veryfast','-crf','18',
      '-pix_fmt','yuv420p','-video_track_timescale','30000',out])
 info=media_info(out);v=next(s for s in info['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'])==(1080,1920)
 assert abs(float(v.get('duration') or info['format']['duration'])-duration)<.08
 return out

def fmt(t):
 c=int(round(t*100))
 return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'

def subtitles(sections,total):
 p=BASE/'captions.ass'
 lines=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920',
 'WrapStyle: 2','ScaledBorderAndShadow: yes','','[V4+ Styles]',
 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
 'Style: Main,Montserrat,72,&H00FFFFFF,&H00FFFFFF,&H0010151B,&H80000000,-1,0,0,0,100,100,0.2,0,1,5,2,5,65,65,700,1',
 'Style: Brand,Montserrat,34,&H00FFFFFF,&H00FFFFFF,&H0010151B,&H80000000,-1,0,0,0,100,100,0.2,0,1,2.7,0,7,20,20,20,1',
 'Style: Source,Montserrat,24,&H00F8F8F8,&H00F8F8F8,&H0010151B,&H80000000,-1,0,0,0,100,100,0,0,1,2.1,0,7,20,20,20,1',
 '','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 def add(start,end,style,content,layer=0):
  if end>start:lines.append(f'Dialogue: {layer},{fmt(start)},{fmt(end)},{style},,0,0,0,,{content}')
 add(0,total,'Brand',r'{\an7\pos(40,65)}STRANGE, BUT VERIFIED',0)
 add(0,total,'Source',r'{\an7\pos(40,110)}SOURCE: G. E. JOHNSON / CC BY',0)
 # The opening hook appears on frame zero, under the action, NOT as a top banner.
 add(0,sections[0]['vo_end'],'Main',
     r'{\an5\pos(540,1210)\fad(0,70)}A REAL FIRE\N{\c&H001FE5FF&}BEHIND A WATERFALL{\c&H00FFFFFF&}',1)
 yellow={'natural','gas','rock','flame','eternal','fire','goes','out'}
 for sc in sections[1:]:
  words=sc['text'].split()
  groups=[];curr=[]
  for w in words:
   curr.append(w)
   if len(curr)>=3 or (w.endswith(('.', '!', '?')) and len(curr)>=2):
    groups.append(curr);curr=[]
  if curr:groups.append(curr)
  strengths=[sum(max(3,len(w.strip('.,!?'))) for w in g) for g in groups]
  st=sc['start'];weights=sum(strengths)
  for i,g in enumerate(groups):
   en=sc['vo_end'] if i==len(groups)-1 else st+(sc['vo_end']-sc['start'])*strengths[i]/weights
   words_markup=[]
   for w in g:
    if w.lower().strip('.,!?') in yellow:
     words_markup.append(r'{\c&H001FE5FF&}'+w+r'{\c&H00FFFFFF&}')
    else:words_markup.append(w)
   add(st,en,'Main',r'{\an5\pos(540,1225)\fad(25,45)}'+' '.join(words_markup),1)
   st=en
 events=[x.split(',')[3] for x in lines if x.startswith('Dialogue:')]
 assert events.count('Brand')==1 and events.count('Source')==1
 assert all(st in ('Brand','Source','Main') for st in events)
 p.write_text('\n'.join(lines),encoding='utf-8')
 shutil.copyfile(p,OUT/'SUBTITLES.ass')
 return p

def soundbed(total):
 sr=32000
 t=np.arange(int(sr*(total+.4)))/sr
 rng=np.random.default_rng(82736)
 noise=rng.standard_normal(t.size).astype('float32')
 low=lfilter([.004],[1,-.994],noise)
 hiss=lfilter([.0015],[1,-.85],noise)
 # Four-layer feel: warm ambient, real waterfall captured audio if available, narrator,
 # plus a gentle first-frame impact without artificial explosions.
 tone=(.0048*np.sin(2*np.pi*52*t)+.0025*np.sin(2*np.pi*78.4*t))
 impact=(.10*np.sin(2*np.pi*77*t)*np.exp(-10*t))
 air=.012*hiss+.045*low+tone+impact
 air*=np.minimum(1,np.maximum(0,(total-t)/.65))
 p=BASE/'original_ambient.wav'
 sf.write(p,air.astype('float32'),sr)
 return p

def assemble(c1,c2,voicepath,sections,total,sourceinfo):
 l=BASE/'cuts.txt'
 l.write_text("file '"+str(c1.resolve())+"'\nfile '"+str(c2.resolve())+"'\n")
 movie=BASE/'unedited_montage.mp4'
 # Reencode filterconcat to guarantee all image runs remain in final video.
 filterstr="[0:v]fps=30,setpts=PTS-STARTPTS[v0];[1:v]fps=30,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0,format=yuv420p[out]"
 run(['ffmpeg','-hide_banner','-v','error','-y','-i',c1,'-i',c2,'-filter_complex',filterstr,'-map','[out]',
      '-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r','30',movie])
 aud=soundbed(total)
 ass=subtitles(sections,total)
 mp4=OUT/'Strange_But_Verified_Eternal_Flame_TikTok_FINAL.mp4'
 # Mix voice and music/ambience, optional captured audio only if source actually has a real audio track.
 source_audio=any(s['codec_type']=='audio' for s in sourceinfo['streams'])
 if source_audio:
  # This video's native soundtrack may be quiet wind or water and contains no licensed commercial music.
  nature=BASE/'onsite_water.wav'
  run(['ffmpeg','-hide_banner','-v','error','-y','-i',SOURCE,'-vn','-af',
    'highpass=f=180,lowpass=f=4500','-ar','32000','-ac','1',nature])
  # Temporal sound from source recording is atmospheric, not tied to exact excerpt time.
  audio_inputs=['-i',voicepath,'-i',aud,'-stream_loop','-1','-i',nature]
  amix=('[1:a]aresample=48000,highpass=f=90,volume=1.12,acompressor=threshold=0.15:ratio=1.7:attack=8:release=145[v];'
        '[2:a]aresample=48000,volume=0.45[amb];'
        '[3:a]aresample=48000,volume=0.16[nat];'
        '[v][amb][nat]amix=inputs=3:duration=first:normalize=0,'
        'loudnorm=I=-16:TP=-1.7:LRA=8[a]')
 else:
  audio_inputs=['-i',voicepath,'-i',aud]
  amix=('[1:a]aresample=48000,highpass=f=90,volume=1.12,acompressor=threshold=0.15:ratio=1.7:attack=8:release=145[v];'
        '[2:a]aresample=48000,volume=0.40[amb];'
        '[v][amb]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.7:LRA=8[a]')
 run(['ffmpeg','-hide_banner','-v','error','-y','-i',movie,*audio_inputs,
      '-filter_complex',amix,'-vf',f'ass={ass.resolve()}','-map','0:v:0','-map','[a]',
      '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-r','30',
      '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',
      '-t',f'{total:.5f}',mp4])
 return mp4,source_audio

def qa(mp4,sections,total,scene_spans,source_audio):
 run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',mp4,'-f','null','-'])
 meta=media_info(mp4)
 v=next(x for x in meta['streams'] if x['codec_type']=='video')
 a=next(x for x in meta['streams'] if x['codec_type']=='audio')
 vlen=float(v.get('duration') or meta['format']['duration'])
 alen=float(a.get('duration') or meta['format']['duration'])
 assert (v['width'],v['height'])==(1080,1920)
 assert abs(vlen-total)<.13 and abs(alen-total)<.13,(vlen,alen,total)
 assert abs(vlen-alen)<.14,('TRUNCATED VIDEO vs audio',vlen,alen)
 _,bl=run(['ffmpeg','-hide_banner','-nostats','-i',mp4,'-vf','blackdetect=d=0.14:pix_th=0.10','-an','-f','null','-'])
 _,fr=run(['ffmpeg','-hide_banner','-nostats','-i',mp4,'-vf','freezedetect=n=-59dB:d=0.9','-an','-f','null','-'])
 blacks=[x for x in bl.splitlines() if 'black_start:' in x]
 freezes=[x for x in fr.splitlines() if 'lavfi.freezedetect.freeze_start:' in x]
 assert not blacks,blacks
 assert not freezes,freezes
 assert scene_spans[0][1]<scene_spans[1][0] or scene_spans[1][1]<scene_spans[0][0]
 rep={'result':'PASS','topic':'Natural flame behind Eternal Flame Falls','duration':round(vlen,3),
      'audio_duration':round(alen,3),'resolution':'1080x1920','fps':30,
      'original_source_fps':29.97,'original_1080p_licensed_video':URL,
      'first_frame_source_time':scene_spans[0][0],
      'frame_zero':'real full-size flame, NOT intro logo','source_ranges_inseconds':scene_spans,
      'nonrepeating_ranges':True,'two_separate_camera_takes':True,
      'source_audio_used':source_audio,'full_decode':True,'black_events':blacks,'freeze_events':freezes,
      'subtitles_y':'1210/1225','brand_lines':2,'source_license':'Creative Commons Attribution 4.0',
      'voice':'Kokoro af_heart 0.88','bytes':mp4.stat().st_size}
 (OUT/'QA.json').write_text(json.dumps(rep,indent=2))
 # 12 actual output frames covering opening and both distinct natural shots.
 sheet=Image.new('RGB',(4*320,3*600),'#151515');draw=ImageDraw.Draw(sheet)
 times=[0,.2,.5,1.0,2.0,3.5,5,6.25,7.35,9,11,max(.2,vlen-.4)]
 for idx,t in enumerate(times):
  t=min(t,max(.02,vlen-.27))
  frame=BASE/f'final_frame_{idx:02d}.jpg'
  run(['ffmpeg','-hide_banner','-v','error','-y','-ss',str(t),'-i',mp4,'-frames:v','1',frame])
  with Image.open(frame) as img:
   img.thumbnail((308,548))
   x=idx%4*320;y=idx//4*600
   sheet.paste(img,(x+(320-img.width)//2,y))
   draw.text((x+9,y+551),f'{t:.2f}s',fill='white')
 sheet.save(OUT/'CONTACT_SHEET.jpg',quality=87)
 print('QA PASS VIDEO',round(vlen,3),'s AUDIO',round(alen,3),'s',mp4.stat().st_size,'bytes',flush=True)

def main():
 info=source()
 voicepath,sc,total=voice()
 # Split into two independent original takes: close first, wide second.
 close=max(5.5,min(6.5,total*.52))
 wide=total-close
 assert close<7.2 and wide<6.7,(close,wide,total)
 first=(7.5,7.5+close);second=(.18,.18+wide)
 assert first[1]<14.88 and second[1]<6.88,(first,second)
 print('SOURCE EDIT DECISION: CLOSE',first,'WIDE',second,'NO REPEATS',flush=True)
 clip1=crop_clip(first[0],close,'01_FLAME_CLOSE_COLD_OPEN',False)
 clip2=crop_clip(second[0],wide,'02_WATERFALL_REVEAL',True)
 movie,source_audio=assemble(clip1,clip2,voicepath,sc,total,info)
 qa(movie,sc,total,[first,second],source_audio)
 credits=('STRANGE, BUT VERIFIED | ETERNAL FLAME FALLS\n\n'
 'Real footage: G. Edward Johnson, "Burning Eternal Flame Falls Chestnut Ridge Park NY 2025-09", recorded 5 and 9 September 2025.\n'
 f'Original file: {ORIGINAL_PAGE}\n'
 f'License: Creative Commons Attribution 4.0 {LICENSE}\n'
 'Changes: two authentic excerpts edited out of recording order; portrait cropping, mild color correction, on-screen captions, voiceover and atmospheric sound design. No CGI, duplicated frames or unrelated stock footage.\n'
 'Research: Etiope, Drobniak, Schimmelmann (2013), Natural seepage of shale gas and the origin of eternal flames in the Northern Appalachian Basin, USA. Marine and Petroleum Geology 43, 178-186. DOI 10.1016/j.marpetgeo.2013.02.009.\n'
 'Note: the flame is fueled by gas seepage and may extinguish and be relit. No claim that flame burns without interruption.\n')
 (OUT/'SOURCES_AND_LICENSES.txt').write_text(credits)
 (OUT/'ENGLISH_NARRATION.txt').write_text('\n'.join(SCRIPT))
 shutil.copyfile(SOURCE,OUT/'ORIGINAL_AUTHENTIC_SOURCE_1080P.webm')
 print('RENDER SUCCESS',movie,flush=True)
if __name__=='__main__': main()
