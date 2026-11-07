#!/usr/bin/env python3
"""Strange But Verified - Exploding Cucumber V5, no repeated recordings.
First 3.665 seconds preserve exact V4 source interval, hook text and same Kokoro voice.
Citations & permissions: Box et al 2024 PNAS CC BY 4; Gorges et al 2025 npj CC BY 4;
Robert Flogaus-Faust CC BY 4; Adrian198cm public domain.
"""
import hashlib,json,re,subprocess,shutil,requests,urllib.parse,time
from pathlib import Path
import numpy as np,soundfile as sf
from PIL import Image,ImageDraw
from scipy.signal import lfilter
import sbv_ecballium_probe_20261107 as research

D=Path('ecballium_media'); D.mkdir(exist_ok=True)
WK=Path('ecballium_v5_work');WK.mkdir(exist_ok=True)
OUT=Path('ecballium_v5_final');OUT.mkdir(exist_ok=True)
S1=D/'pnas.2410420121.sm01.mov'
S2=D/'pnas.2410420121.sm02.mov'
S3=D/'pnas.2410420121.sm03.avi'
GORGES=D/'gorges_2025_original.avi'
PHOTO1=D/'ecballium_RF_robert_flogaus.jpg'
PHOTO2=D/'ecballium_1_adrian.jpg'
for p in (S1,S2,S3):
 assert p.is_file() and p.stat().st_size>1500000,f'Missing PNAS research video {p}'
FPS=30;W=1080;H=1920
SPEECH=[
 "This thing fires seeds at forty-five miles per hour.",
 "It's a plant called the squirting cucumber.",
 "Pressure builds inside the fruit as it ripens.",
 "Then, in just thirty milliseconds, it launches the seeds.",
 "Some fly as far as ten metres.",
 "A seed cannon. Grown by nature."
]
SOURCES=[
 {'id':'pnas_launch','kind':'video','file':S3,'in':2.10,'focus':0.50,'name':'2024 REAL SEED EJECTION','license':'CC BY 4.0'},
 {'id':'pnas_growth','kind':'video','file':S2,'in':0.15,'focus':0.74,'name':'2024 GROWTH TIMELAPSE','license':'CC BY 4.0'},
 {'id':'pnas_ct','kind':'video','file':S1,'in':20.8,'focus':0.50,'name':'2024 INTERNAL CT SCAN','license':'CC BY 4.0'},
 {'id':'gorges_launch','kind':'video','file':GORGES,'in':12.65,'focus':0.00,'name':'INDEPENDENT 2025 HIGH SPEED EXPERIMENT','license':'CC BY 4.0'},
 {'id':'robert_fruit','kind':'photo','file':PHOTO1,'name':'2016 REAL PLANT CLOSEUP','license':'CC BY 4.0'},
 {'id':'adrian_fruit','kind':'photo','file':PHOTO2,'name':'2005 REAL EC BALLIUM PLANT','license':'public domain'}
]
assert len(set(x['id'] for x in SOURCES))==len(SOURCES)==len(SPEECH)
assert len(set(x['file'].name for x in SOURCES))==len(SOURCES),'Any source reuse is disallowed'

def run(args):
 p=subprocess.run([str(a) for a in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:raise RuntimeError(' '.join(map(str,args[:8]))+'\n'+p.stderr[-2000:])
 return p.stdout,p.stderr

def download(url,path,minsize=100000,maxsize=155000000):
 if path.exists() and path.stat().st_size>=minsize:return
 session=requests.Session()
 for i in range(4):
  try:
   r=session.get(url,timeout=130,stream=True,headers={'User-Agent':'Mozilla/5.0 (academic documentary)', 'Referer':'https://www.nature.com/'})
   print('GET',r.status_code,url[:170],r.headers.get('content-length'),flush=True)
   r.raise_for_status()
   if 'text/html' in r.headers.get('Content-Type','').lower():raise RuntimeError('HTML instead of media')
   count=0
   with open(path,'wb') as out:
    for chunk in r.iter_content(1024*1024):
     if chunk:
      count+=len(chunk)
      if count>maxsize:raise RuntimeError('Too large')
      out.write(chunk)
   if not minsize<=count<=maxsize:raise RuntimeError(f'Unexpected download length {count}')
   return
  except Exception as e:
   path.unlink(missing_ok=True)
   print('Download retry',i,repr(e),flush=True)
   time.sleep(3)
 raise RuntimeError('Cannot fetch licensed research asset '+url)

GORGES_URL='https://static-content.springer.com/esm/art%3A10.1038%2Fs44383-025-00003-7/MediaObjects/44383_2025_3_MOESM2_ESM.avi'
def wikimedia(name,path):
 filebase=name.replace(' ','_')
 h=hashlib.md5(filebase.encode('utf-8')).hexdigest()
 url=f'https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{urllib.parse.quote(filebase)}'
 download(url,path,minsize=160000,maxsize=10000000)
 return url

def prepare():
 download(GORGES_URL,GORGES,minsize=20000000,maxsize=140000000)
 photo_urls=[
 wikimedia('Ecballium elaterium RF.jpg',PHOTO1),
 wikimedia('Ecballium elaterium 1.jpg',PHOTO2)]
 for p in [GORGES]:
  pinfo=probe(p)
  assert float(pinfo['format']['duration'])>20
 for p in [PHOTO1,PHOTO2]:
  with Image.open(p) as im:
   assert im.width>=1800 and im.height>=1000,(p,im.size)
 return photo_urls

def probe(p):
 output,_=run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)])
 return json.loads(output)

def narrator():
 from kokoro_onnx import Kokoro
 kokoro=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
 sr=24000;arrs=[];sections=[];elapsed=0.0
 for sentence in SPEECH:
  a,n=kokoro.create(sentence,voice='af_heart',speed=0.88,lang='en-us',trim=True,continuous=True)
  assert n==sr
  a=np.asarray(a,dtype=np.float32).reshape(-1)
  assert len(a)>sr*.48
  gap=.09
  arrs.append(a);arrs.append(np.zeros(round(sr*gap),dtype=np.float32))
  sections.append({'phrase':sentence,'start':elapsed,'voice_end':elapsed+len(a)/sr,'end':elapsed+len(a)/sr+gap})
  elapsed+=len(a)/sr+gap
 wave=np.concatenate(arrs)
 path=OUT/'KOKORO_AF_HEART_NARRATION.wav'
 sf.write(path,wave,sr,subtype='PCM_24')
 assert 13<elapsed<21,elapsed
 return path,sections,elapsed

def qtime(sec):
 cs=max(0,int(round(sec*100)))
 return f'{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}'

def subtitle(sections,total):
 lines=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920',
 'WrapStyle: 2','ScaledBorderAndShadow: yes','','[V4+ Styles]',
 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
 'Style: Caps,Montserrat,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0.2,0,1,5,2,5,65,65,700,1',
 'Style: Brand,Montserrat,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H70000000,-1,0,0,0,100,100,0,0,1,2.8,0,7,20,20,20,1',
 'Style: Source,Montserrat,23,&H00EEEEEE,&H00EEEEEE,&H00000000,&H80000000,-1,0,0,0,100,100,0.5,0,1,2.2,0,7,20,20,20,1',
 '','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 def add(st,en,style,txt,layer=0):
  if en>st:lines.append(f'Dialogue: {layer},{qtime(st)},{qtime(en)},{style},,0,0,0,,{txt}')
 add(0,total,'Brand',r'{\an7\pos(40,66)}STRANGE, BUT VERIFIED')
 add(0,total,'Source',r'{\an7\pos(40,110)}SOURCE: PNAS  |  BOX ET AL. (2024)')
 # Preserve V4 hook exactly.
 add(0,sections[0]['voice_end'],'Caps',r'{\an5\pos(540,1220)\fad(0,75)}THIS THING FIRES SEEDS\N{\c&H0000D8FF&}AT 45 MPH{\c&H00FFFFFF&}',1)
 yellow={'plant','squirting','cucumber','pressure','fruit','thirty','milliseconds','seeds','metres','ten','cannon','nature'}
 for section in sections[1:]:
  words=section['phrase'].split()
  groups=[];current=[]
  for word in words:
   current.append(word)
   if len(current)>=4 or word.endswith('.') and len(current)>=2:
    groups.append(current);current=[]
  if current:groups.append(current)
  weights=[sum(max(3,len(w.strip('.,?!'))) for w in g) for g in groups]
  st=section['start'];weights_total=sum(weights)
  for i,g in enumerate(groups):
   en=section['voice_end'] if i==len(groups)-1 else st+(section['voice_end']-section['start'])*weights[i]/weights_total
   colored=[]
   for word in g:
    colored.append(r'{\c&H0000D8FF&}'+word+r'{\c&H00FFFFFF&}' if word.lower().strip('.,?!:') in yellow else word)
   add(st,en,'Caps',r'{\an5\pos(540,1210)\fad(30,50)}'+' '.join(colored),1)
   st=en
 # Exactly two static top-left rows, and narration captions below center. No other overlays.
 events=[l.split(',')[3] for l in lines if l.startswith('Dialogue:')]
 assert events.count('Brand')==events.count('Source')==1 and all(x in ('Brand','Source','Caps') for x in events)
 f=WK/'captions.ass';f.write_text('\n'.join(lines),encoding='utf-8')
 return f

def source_clip(source,st,length,index):
 p=WK/f'visual_{index:02d}.mp4'
 kind=source['kind']
 if kind=='video':
  meta=probe(source['file'])
  dur=float(meta['format']['duration'])
  assert st+length<dur-.03,(source['id'],st,length,dur)
  if source['id']=='gorges_launch':
   # Preserve *entire* independent square 2025 experimental recording, no 9:16 crop cutting off seeds.
   vf=("[0:v]fps=30,split=2[bg][fg];"
       "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
       "boxblur=20:2,eq=brightness=-0.09[back];"
       "[fg]scale=1080:1080,setsar=1[front];"
       "[back][front]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]")
   filterarg=['-filter_complex',vf,'-map','[out]']
  else:
   pan=(f'(iw-1080)*{source["focus"]:.4f}+16*sin(n/24)' if source['id']=='pnas_ct'
        else f'(iw-1080)*{source["focus"]:.4f}')
   vf=(f'fps=30,scale=-2:1920:flags=lanczos,crop=1080:1920:{pan}:0,'
       'eq=contrast=1.05:saturation=1.05,format=yuv420p')
   filterarg=['-vf',vf]
  cmd=['ffmpeg','-hide_banner','-v','error','-y','-ss',f'{st:.4f}','-i',source['file'],'-t',f'{length:.4f}',
       '-an',*filterarg,'-r','30','-c:v','libx264','-preset','veryfast',
       '-crf','21','-pix_fmt','yuv420p','-video_track_timescale','30000',p]
 else:
  # Archival photographs are marked as still photographs in QA. Subtle Ken Burns motion is not real filmed movement.
  frames=int(round(length*FPS))
  vf=('scale=1280:2276:force_original_aspect_ratio=increase,crop=1280:2276,'
      f"zoompan=z='min(1.06+0.0007*on,1.13)':"
      f"x='(iw-iw/zoom)*({0.18 if index%2 else 0.55} + {0.21 if index%2 else -0.22}*on/{frames})':"
      f"y='(ih-ih/zoom)*0.50':d=1:s=1080x1920:fps=30,"
      'eq=contrast=1.04:saturation=1.10,format=yuv420p')
  cmd=['ffmpeg','-hide_banner','-v','error','-y','-loop','1','-framerate','30',
       '-i',source['file'],'-frames:v',str(frames),'-an','-vf',vf,'-r','30',
       '-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',p]
 run(cmd)
 j=probe(p);v=next(x for x in j['streams'] if x['codec_type']=='video')
 assert (v['width'],v['height'])==(W,H),(source['id'],v['width'],v['height'])
 assert abs(float(j['format']['duration'])-length)<.09,(source['id'],j['format']['duration'],length)
 print('UNIQUE SOURCE SHOT',source['id'],round(length,3),source['kind'],flush=True)
 return p

def ambient(total):
 sr=32000
 t=np.arange(int((total+.2)*sr))/sr
 rng=np.random.default_rng(10425)
 white=rng.standard_normal(len(t)).astype('float32')
 breeze=lfilter([.0015],[1,-.9985],white)
 tones=.010*np.sin(2*np.pi*55*t)+.006*np.sin(2*np.pi*82.4*t)
 impact=.13*np.exp(-12*t)*np.sin(2*np.pi*65*t)
 a=(.033*breeze+tones+impact)*np.minimum(1,np.maximum(0,(total-t)/.65))
 p=WK/'original_ambience.wav';sf.write(p,a.astype('float32'),sr)
 return p

def main():
 photos=prepare()
 voice,sections,total=narrator()
 ass=subtitle(sections,total)
 duration_by_scene=[round(s['end']-s['start'],5) for s in sections]
 assert abs(duration_by_scene[0]-3.665)<.35,('Opening differs from approved V4',duration_by_scene[0])
 # Each clip uses a different camera recording or independently photographed image, exactly once.
 segments=[];timeline=[]
 for i,(src,sc) in enumerate(zip(SOURCES,sections)):
  length=duration_by_scene[i]
  out=source_clip(src,src.get('in',0),length,i)
  segments.append(out)
  timeline.append({'id':src['id'],'file':src['file'].name,'type':src['kind'],
    'in':src.get('in',0),'out':src.get('in',0)+length,'duration':length,
    'position':sc['start'],'voice':sc['phrase']})
 assert len(set(x['file'] for x in timeline))==len(timeline),'Repeated source video detected'
 concat=WK/'concat.txt';concat.write_text(''.join("file '"+str(x.resolve())+"'\n" for x in segments))
 movie=WK/'unique_visuals.mp4'
 run(['ffmpeg','-hide_banner','-v','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',movie])
 ambience=ambient(total)
 mp4=OUT/'SBV_EXPLODING_CUCUMBER_V5_NO_REPEATED_SHOTS.mp4'
 fa=("[1:a]aresample=48000,highpass=f=85,volume=1.18,acompressor=threshold=0.14:ratio=1.8:attack=10:release=130[v];"
      "[2:a]aresample=48000,volume=0.20[a];[v][a]amix=inputs=2:duration=first:normalize=0,"
      "loudnorm=I=-16:TP=-1.7:LRA=8[m]")
 run(['ffmpeg','-hide_banner','-v','error','-y','-i',movie,'-i',voice,'-i',ambience,
      '-filter_complex',fa,'-vf',f'ass={ass.resolve()}','-map','0:v:0','-map','[m]',
      '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r','30',
      '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',
      '-t',f'{total:.4f}',mp4])
 run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',mp4,'-f','null','-'])
 meta=probe(mp4);dur=float(meta['format']['duration'])
 v=next(x for x in meta['streams'] if x['codec_type']=='video')
 assert (v['width'],v['height'])==(1080,1920) and abs(dur-total)<.6 and mp4.stat().st_size>2500000
 _,freeze=run(['ffmpeg','-hide_banner','-nostats','-i',mp4,'-vf','freezedetect=n=-57dB:d=0.85',
               '-an','-f','null','-'])
 freezes=[x.strip() for x in freeze.splitlines() if 'lavfi.freezedetect.freeze_start:' in x]
 _,black=run(['ffmpeg','-hide_banner','-nostats','-i',mp4,'-vf','blackdetect=d=0.16:pix_th=0.08',
              '-an','-f','null','-'])
 blacks=[x.strip() for x in black.splitlines() if 'black_start:' in x]
 assert not blacks,blacks
 assert not freezes,freezes
 _,sound=run(['ffmpeg','-hide_banner','-nostats','-i',mp4,'-af','ebur128=peak=true','-vn','-f','null','-'])
 loud=sound[sound.rfind('Integrated loudness:'):]
 report={'status':'PASS','duration_sec':dur,'resolution':'1080x1920','fps':30,
  'no_visual_source_reused':True,'source_video_count':4,'unique_photo_count':2,'repeated_video_count':0,
  'video_pct':round(100*sum(x['duration'] for x in timeline if x['type']=='video')/total,2),
  'same_opening_v4':{'source':'pnas.2410420121.sm03.avi','source_offset':2.10,'text':SPEECH[0]},
  'audio':'Kokoro-82M af_heart speed 0.88, original ambient, AAC 192k',
  'two_row_top_left':True,'upper_central_extra_text':False,
  'visual_edl':timeline,'full_decode':'PASS','black_events':blacks,'freeze_events':freezes,
  'loudness':loud,'bytes':mp4.stat().st_size}
 (OUT/'QA_NO_REPEATS.json').write_text(json.dumps(report,indent=2))
 (OUT/'FULL_CREDITS_LICENSES.txt').write_text(
  '1) ORIGINAL RECORDING (2024): Finn Box et al. Uncovering the mechanical secrets of the squirting cucumber. '
  'PNAS, doi:10.1073/pnas.2410420121. Movie S3 original high-speed footage, Movie S2 fruit time-lapse, '
  'Movie S1 CT scan visualization. CC BY 4.0 https://creativecommons.org/licenses/by/4.0/; '
  'https://pmc.ncbi.nlm.nih.gov/articles/PMC11648854/\n'
  '2) INDEPENDENT RECORDING (2025): Helen Gorges, Mieke Brinkhaus, Pauline Sator et al. '
  'Structural and biomechanical adaptations of fruits and seeds in Ecballium elaterium. '
  'npj Science of Plants 1, article 4 (2025), doi:10.1038/s44383-025-00003-7, Supplementary Movie-1. '
  'CC BY 4.0 https://creativecommons.org/licenses/by/4.0/; '
  'https://www.nature.com/articles/s44383-025-00003-7\n'
  '3) PHOTO (2016): Robert Flogaus-Faust, Ecballium elaterium RF.jpg, Wikimedia Commons, CC BY 4.0, '
  'https://commons.wikimedia.org/wiki/File:Ecballium_elaterium_RF.jpg\n'
  '4) PHOTO (2005): Adrian198cm, Ecballium elaterium 1.jpg, Wikimedia Commons, public domain, '
  'https://commons.wikimedia.org/wiki/File:Ecballium_elaterium_1.jpg\n'
  'Photo credit URLs: '+str(photos)+'\n'
  'Edits: cropping, source excerpts, duration, subtle movement over still images, original background score, '
  'Kokoro narration, typography, audio leveling, 9:16 adaptation.\n'
  'No video recording, source segment or photo reused. Copyright owners retain their rights; '
  'CC BY 4.0 attribution is required in the description. Photos are still images, not purported footage.\n')
 (OUT/'NARRATION.txt').write_text(' '.join(SPEECH))
 shutil.copyfile(ass,OUT/'CAPTIONS.ass')
 # Produce visual contact sheet and 0-3.6s timing proof.
 contact=Image.new('RGB',(4*270,3*505),'#101820');d=ImageDraw.Draw(contact)
 times=[0,.35,1.25,2.6,3.7,5.1,6.9,8.2,9.7,11.3,13.2,max(0.2,dur-.25)]
 for i,t in enumerate(times):
  if t>dur-.08:t=dur-.09
  frame=WK/f'frame_{i}.jpg'
  run(['ffmpeg','-hide_banner','-v','error','-y','-ss',str(t),'-i',mp4,'-frames:v','1',frame])
  with Image.open(frame) as im:
   im.thumbnail((265,473));x=(i%4)*270;y=(i//4)*505;contact.paste(im,(x+(270-im.width)//2,y))
   d.text((x+6,y+476),f'{t:.2f}s',fill='#FFFFFF')
 contact.save(OUT/'CONTACT_SHEET.jpg',quality=88)
 print('V5 SUCCESS',report['duration_sec'],'s',report['video_pct'],'percent true moving video; 4 unique videos, 2 stills, no repeats',flush=True)

if __name__=='__main__':main()
