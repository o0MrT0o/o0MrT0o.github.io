#!/usr/bin/env python3
"""Strange But Verified - Zombie Snail short: Kokoro af_heart, 9:16, real CC BY-SA video."""
from pathlib import Path
import os, json, re, shutil, subprocess, urllib.request, time
import numpy as np
import soundfile as sf

R=Path.cwd()
AS=R/'snail_assets'; AS.mkdir(exist_ok=True)
WK=R/'snail_work'; WK.mkdir(exist_ok=True)
OUT=R/'snail_output'; OUT.mkdir(exist_ok=True)
W,H,FPS=1080,1920,30
VIDEOS={
 'a':['https://upload.wikimedia.org/wikipedia/commons/transcoded/e/e3/Ambrette_commune_001.ogv/Ambrette_commune_001.ogv.1080p.vp9.webm','https://upload.wikimedia.org/wikipedia/commons/e/e3/Ambrette_commune_001.ogv'],
 'b':['https://upload.wikimedia.org/wikipedia/commons/transcoded/7/74/Leucochloridium.ogv/Leucochloridium.ogv.720p.vp9.webm','https://upload.wikimedia.org/wikipedia/commons/7/74/Leucochloridium.ogv']
}
PHRASES=[
 "That pulsing thing?",
 "It's a parasite.",
 "Inside a living snail.",
 "Leucochloridium fills its eyestalks with striped sacs that move like caterpillars.",
 "Infected snails spend more time in brighter, exposed places, where birds can see them.",
 "A bird can swallow the parasite and complete its life cycle.",
 "And the snail?",
 "Still alive."
]
SHOTS=[
 ('b',69.0,'tight',3.0,.51),
 ('a',14.0,'tight',2.45,.49),
 ('b',5.0,'tight',2.4,.53),
 ('a',26.0,'wide',2.5,.50),
 ('b',18.0,'tight',2.55,.52),
 ('a',38.0,'tight',2.65,.55),
 ('b',34.0,'tight',2.7,.48),
 ('a',52.5,'tight',3.1,.54),
 ('b',49.0,'wide',2.7,.50),
 ('a',44.5,'tight',2.6,.52)
]
def run(args):
 p=subprocess.run([str(v) for v in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:raise RuntimeError('COMMAND FAILED '+' '.join(str(x) for x in args[:8])+'\n'+p.stderr[-3000:])
 return p.stdout
def probe(p):
 j=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',p]))
 return j,float(j['format']['duration'])
def download(k):
 for f in AS.glob(f'source_{k}.*'):
  try:
   _,d=probe(f)
   if d>45:return f
  except Exception:pass
 for url in VIDEOS[k]:
  p=AS/f'source_{k}{".webm" if url.endswith(".webm") else ".ogv"}'
  for attempt in range(3):
   try:
    print('Downloading true camera footage:',k,url,'attempt',attempt+1,flush=True)
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 StrangeButVerified/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r, open(p,'wb') as f:shutil.copyfileobj(r,f,1024*1024)
    _,dur=probe(p)
    assert dur>50 and p.stat().st_size>400000
    print('Source verified',k,p.stat().st_size,dur,flush=True)
    return p
   except Exception as e:
    print('Retrying after',repr(e),flush=True)
    p.unlink(missing_ok=True);time.sleep(5)
 raise RuntimeError('No original footage for '+k)
def voice():
 from kokoro_onnx import Kokoro
 tts=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
 sr=24000;sections=[];t=0;pieces=[]
 for phrase in PHRASES:
  a,n=tts.create(phrase,voice='af_heart',speed=0.88,lang='en-us',trim=True,continuous=True)
  assert n==sr,(phrase,n)
  a=np.asarray(a,dtype=np.float32).reshape(-1)
  assert len(a)>3000
  gap=.07
  pieces.extend([a,np.zeros(round(sr*gap),dtype=np.float32)])
  sections.append((phrase,t,t+len(a)/sr))
  t+=len(a)/sr+gap
 samples=np.concatenate(pieces)
 wav=OUT/'SBV_ZOMBIE_SNAIL_KOKORO_AF_HEART.wav'
 sf.write(wav,samples,sr,subtype='PCM_24')
 return wav,sections,len(samples)/sr
def clock(s):
 n=max(0,round(s*100))
 return f'{n//360000}:{n//6000%60:02d}:{n//100%60:02d}.{n%100:02d}'
def captions(section,total):
 p=WK/'captions.ass'
 rows=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','WrapStyle: 2','ScaledBorderAndShadow: yes','','[V4+ Styles]',
 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
 'Style: Caps,Montserrat,63,&H00FFFFFF,&H00FFFFFF,&H00000000,&HAA000000,-1,0,0,0,100,100,1,0,1,5,2,5,60,60,560,1',
 'Style: Hook,Montserrat,78,&H0000D8FF,&H0000D8FF,&H00000000,&HCC000000,-1,0,0,0,100,100,1,0,1,6,2,5,60,60,1150,1',
 'Style: Brand,Montserrat,21,&H00FFFFFF,&H00FFFFFF,&H00000000,&HCC000000,-1,0,0,0,100,100,0,0,1,2,0,7,30,30,30,1',
 '','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 def add(a,b,sty,tx):
  if b>a:rows.append(f'Dialogue: 0,{clock(a)},{clock(b)},{sty},,0,0,0,,{tx}')
 add(0,total,'Brand',r'{\an7\pos(44,64)}STRANGE, BUT VERIFIED  /  WIKIMEDIA')
 add(0,1.13,'Hook',r'{\an5\pos(540,445)\fad(60,90)}THAT THING IS PULSING')
 add(1.13,2.96,'Hook',r'{\an5\pos(540,445)\fad(60,90)}INSIDE A LIVING SNAIL')
 highlight={'parasite','snail','pulsing','eyestalks','caterpillars','birds','alive','living','brighter','striped'}
 for phrase,start,end in section:
  words=phrase.split();groups=[];cur=[]
  for w in words:
   cur.append(w)
   if len(cur)>=4 or (w.endswith(('.', '?','!')) and len(cur)>=2):
    groups.append(cur);cur=[]
  if cur:groups.append(cur)
  weight=[sum(max(2,len(w.strip(',.!?'))) for w in g) for g in groups]
  sumw=sum(weight);now=start
  for i,g in enumerate(groups):
   e=end if i==len(groups)-1 else now+(end-start)*weight[i]/sumw
   marked=[]
   for w in g:
    clean=w.lower().strip(',.?!:;')
    marked.append(r'{\c&H0000D8FF&}'+w+r'{\c&H00FFFFFF&}' if clean in highlight else w)
   add(max(0,now-.03),min(total,e+.05),'Caps',r'{\an5\pos(540,1320)\fad(45,70)}'+' '.join(marked))
   now=e
 p.write_text('\n'.join(rows))
 return p
def original_bed(total):
 from scipy.signal import lfilter
 sr=32000;t=np.arange(int(sr*total))/sr
 noise=np.random.default_rng(3607).standard_normal(t.size).astype('float32')
 wind=lfilter([.003],[1,-.997],noise).astype('float32')
 drone=.020*np.sin(2*np.pi*55*t)+.012*np.sin(2*np.pi*82.41*t)+.006*np.sin(2*np.pi*110*t)
 suspense=(.7+.3*np.sin(2*np.pi*.12*t))
 hit=.085*np.exp(-12*t)*np.sin(2*np.pi*67*t)
 bed=(drone*suspense+.020*wind+hit).astype('float32')
 bed*=np.minimum(1,np.maximum(0,(total-t)/.9))
 p=WK/'original_ambient.wav';sf.write(p,bed,sr)
 return p
def cut(source,i,start,sec,variant,focus):
 p=WK/f'clip_{i:02d}.mp4'
 h=H if variant=='wide' else int(H*1.04)//2*2
 vf=f'fps=30,scale=-2:{h}:flags=lanczos,crop=1080:1920:(iw-1080)*{focus:.4f}:(ih-1920)/2,eq=contrast=1.04:saturation=1.08,format=yuv420p'
 run(['ffmpeg','-v','error','-y','-ss',f'{start:.3f}','-i',source,'-t',f'{sec:.3f}','-an','-vf',vf,
      '-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-r','30',p])
 return p
def main():
 a,b=download('a'),download('b')
 wav,timings,voice_len=voice()
 total=voice_len+.20
 print('Kokoro voice duration',voice_len,'s, edited runtime',total,'s',flush=True)
 frames=round(total*FPS)
 w=np.array([x[3] for x in SHOTS]);w/=w.sum()
 quotas=np.floor(w*frames).astype(int)
 for i in range(frames-int(quotas.sum())):quotas[i%len(quotas)]+=1
 parts=[];edl=[];cursor=0
 for i,(k,start,variant,_,focus) in enumerate(SHOTS):
  d=int(quotas[i])/FPS
  assert d>1.6
  f=cut(a if k=='a' else b,i,start,d,variant,focus)
  parts.append(f);edl.append({'source':k,'source_start':start,'duration':d,'timeline_start':cursor})
  cursor+=d
 concat=WK/'clips.txt';concat.write_text(''.join("file '"+str(x.resolve())+"'\n" for x in parts))
 joined=WK/'joined.mp4'
 run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',joined])
 ass=captions(timings,total)
 ambience=original_bed(total+.3)
 master=OUT/'SBV_ZOMBIE_SNAIL_KOKORO_TIKTOK_FINAL.mp4'
 mix=("[1:a]aresample=48000,highpass=f=85,volume=1.25,acompressor=threshold=0.12:ratio=2:attack=12:release=130[v];"
      "[2:a]aresample=48000,volume=0.17[b];[v][b]amix=inputs=2:duration=first:normalize=0,"
      "loudnorm=I=-16:TP=-2:LRA=8[final]")
 run(['ffmpeg','-v','error','-y','-i',joined,'-i',wav,'-i',ambience,
      '-vf',f'ass={ass.resolve()}','-filter_complex',mix,'-map','0:v','-map','[final]',
      '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r','30',
      '-c:a','aac','-b:a','192k','-ar','48000','-t',f'{total:.3f}',master])
 run(['ffmpeg','-v','error','-xerror','-i',master,'-f','null','-'])
 info,d=probe(master)
 v=next(x for x in info['streams'] if x['codec_type']=='video')
 au=next(x for x in info['streams'] if x['codec_type']=='audio')
 assert (v['width'],v['height'])==(W,H)
 assert au['codec_name']=='aac' and abs(d-total)<.7
 assert master.stat().st_size>1000000
 qa={'status':'PASS','duration_sec':d,'fps':FPS,'resolution':'1080x1920',
 'voice':'Kokoro-82M af_heart speed=0.88 en-us','voice_seconds':voice_len,
 'unique_source_sections':edl,'no_generated_visuals':True,'full_decode':'PASS',
 'source_credits':'Entomolo CC BY-SA 4.0; Gilles San Martin CC BY-SA 3.0',
 'adaptation_license':'CC BY-SA 4.0','render_bytes':master.stat().st_size}
 (OUT/'QA.json').write_text(json.dumps(qa,indent=2))
 (OUT/'NARRATION.txt').write_text(' '.join(PHRASES))
 (OUT/'SOURCES_AND_LICENSES.txt').write_text(
  'Entomolo, Ambrette commune 001.ogv, CC BY-SA 4.0, https://commons.wikimedia.org/wiki/File:Ambrette_commune_001.ogv\n'+
  'Gilles San Martin, Leucochloridium.ogv, CC BY-SA 3.0, https://commons.wikimedia.org/wiki/File:Leucochloridium.ogv\n'+
  'Adapted by editing, cropping, grading, narration, captions. Adaptation licensed CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/\n'+
  'Scientific source Wesołowska & Wesołowski 2014 Journal of Zoology https://doi.org/10.1111/jzo.12094\n')
 shutil.copy(ass,OUT/'CAPTIONS.ass')
 from PIL import Image,ImageDraw
 sheet=Image.new('RGB',(920,1320),'#101820')
 draw=ImageDraw.Draw(sheet)
 for i,t in enumerate([0,.4,1.3,2.3,4.6,6.9,9.2,12,15,18,21,d-.3]):
  pic=WK/f'frame_{i:02d}.jpg'
  run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',master,'-frames:v','1',pic])
  im=Image.open(pic);im.thumbnail((230,410))
  x=i%4*230;y=i//4*440;sheet.paste(im,(x,y));draw.text((x+5,y+412),f'{t:.1f}s',fill='white')
 sheet.save(OUT/'CONTACT_SHEET.jpg',quality=87)
 print('RENDER_SUCCESS',str(master),round(d,3),master.stat().st_size,flush=True)
if __name__=='__main__':main()
