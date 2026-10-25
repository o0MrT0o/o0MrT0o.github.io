from pathlib import Path
import os,subprocess,json,requests,io,math,textwrap
import numpy as np,soundfile as sf
from PIL import Image,ImageDraw,ImageFont
from kokoro import KPipeline
p=Path('snail_film');p.mkdir(exist_ok=True)
def run(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode: raise RuntimeError('COMMAND FAILED '+str(cmd)+'\n'+r.stderr[-3000:])
 return r.stdout
# Resolve Wikimedia originals through Commons API, including stable file titles.
for title,outname in [('File:Leucochloridium.ogv','commons_leuco.ogv'),('File:Ambrette commune 001.ogv','ambrette.ogv')]:
 dest=p/outname
 if dest.exists() and dest.stat().st_size>500000: continue
 api='https://commons.wikimedia.org/w/api.php'
 j=requests.get(api,params={'action':'query','titles':title,'prop':'imageinfo','iiprop':'url','format':'json'},headers={'User-Agent':'StrangeButVerifiedFilm/1.0'},timeout=45).json()
 pages=j.get('query',{}).get('pages',{})
 item=next(iter(pages.values()),{})
 url=item.get('imageinfo',[{}])[0].get('url')
 if not url: print('NO_COMMONS_URL',title,j,flush=True);continue
 with requests.get(url,stream=True,timeout=120,headers={'User-Agent':'StrangeButVerifiedFilm/1.0'}) as r:
  r.raise_for_status()
  with dest.open('wb') as f:
   for c in r.iter_content(1024*1024): f.write(c)
 print('COMMONS',title,dest.stat().st_size,url,flush=True)
# Probe available authentic videos.
videos=[]
for name in ['smithsonian.mp4','commons_leuco.ogv','ambrette.ogv']:
 f=p/name
 if f.exists() and f.stat().st_size>500000:
  q=json.loads(run(['ffprobe','-v','error','-show_entries','stream=width,height:format=duration','-of','json',str(f)]))
  videos.append((f,float(q['format']['duration']),q))
print('VIDEOS',[(str(x[0]),x[1],x[2]) for x in videos],flush=True)
if not videos: raise RuntimeError('No authentic video footage downloaded.')
# Narration split into paragraph beats. Kokoro uses the established af_heart voice.
script=Path('sbv_whales/snail_narration.txt').read_text().strip()
paras=[x.strip() for x in script.split('\n\n') if x.strip()]
pipeline=KPipeline(lang_code='a')
voice_parts=[];segments=[]
for i,para in enumerate(paras):
 arr=[]
 for _,_,audio in pipeline(para, voice='af_heart', speed=0.90, split_pattern=r'\n+'):
  arr.append(audio.numpy() if hasattr(audio,'numpy') else np.asarray(audio))
 if not arr: raise RuntimeError('Kokoro generated no audio for paragraph '+str(i))
 wav=np.concatenate(arr).astype(np.float32)
 voice_parts.append(wav)
 dur=len(wav)/24000
 segments.append({'text':para,'duration':dur,'index':i})
voice=np.concatenate(voice_parts)
sf.write(p/'narration.wav',voice,24000)
# SRT timing follows paragraph-aligned generated voice. Each beat has a corresponding real-footage shot.
def srt_time(t):
 ms=round(t*1000);h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000;s=ms//1000;ms%=1000
 return f'{h:02}:{m:02}:{s:02},{ms:03}'
srt=[];cursor=0
for i,seg in enumerate(segments,1):
 seg['start']=cursor;seg['end']=cursor+seg['duration']
 words=seg['text'].split()
 # Break paragraph into readable subtitle units, timing evenly across speech segment.
 chunks=[];current=[]
 for w in words:
  if len(' '.join(current+[w]))>43 and current: chunks.append(' '.join(current));current=[w]
  else: current.append(w)
 if current:chunks.append(' '.join(current))
 span=seg['duration']/len(chunks)
 for j,ch in enumerate(chunks):
  start=cursor+j*span;end=cursor+(j+1)*span
  srt.append(f'{len(srt)+1}\n{srt_time(start)} --> {srt_time(end)}\n{ch}\n')
 cursor+=seg['duration']
(p/'SBV_ZOMBIE_SNAIL_EN.srt').write_text('\n'.join(srt))
# Render one 1080p landscape scene per narration paragraph; authentic videos only, no generated fake footage.
scene_files=[]
for i,seg in enumerate(segments):
 target=p/f'scene_{i:02}.mp4'
 vf="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,eq=contrast=1.04:saturation=1.05"
 # Rotate through actual video sources and source times, using unique intervals where possible.
 src,duration,meta=videos[i%len(videos)]
 maxstart=max(0,duration-seg['duration']-0.15)
 start=(i*13.7)%(maxstart+0.01) if maxstart>0.1 else 0
 # Shorter source shots are looped only within a segment, never replaced with stills.
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-stream_loop','-1','-ss',str(start),'-i',str(src),'-t',str(seg['duration']),'-vf',vf,'-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(target)])
 seg['source']=src.name;seg['source_start']=start
 scene_files.append(target)
# Concat visual scenes.
lst=p/'scenes.txt'
lst.write_text(''.join("file '"+str(f.resolve())+"'\n" for f in scene_files))
visual=p/'visual.mp4'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy','-movflags','+faststart',str(visual)])
# Soft original synthesized ambient bed; voice remains clearly foregrounded.
dur=len(voice)/24000
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(visual),'-i',str(p/'narration.wav'),'-filter_complex',
     f"[1:a]loudnorm=I=-16:TP=-2:LRA=7,apad=pad_dur=1[vo];sine=frequency=110:sample_rate=48000,lowpass=f=260,volume=0.018,atrim=0:{dur:.3f},afade=t=in:st=0:d=2,afade=t=out:st={max(0,dur-3):.3f}:d=3[bed];[vo]aresample=48000[voice];[voice][bed]amix=inputs=2:duration=first:weights=1 0.12[a]",
     '-map','0:v','-map','[a]','-t',f'{dur:.3f}','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(p/'premaster.mp4')])
# Burn readable subtitles in the established white/black-outline style with sparse yellow emphasis omitted for reliability.
out=p/'SBV_ZOMBIE_SNAIL_PARASITE_LONG_FILM.mp4'
sub=str((p/'SBV_ZOMBIE_SNAIL_EN.srt').resolve()).replace('\\','/').replace(':','\\:')
vf=f"subtitles='{sub}':force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=54'"
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p/'premaster.mp4'),'-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(out)])
# Thumbnail from actual infected-snail footage, not a generated image.
thumb=p/'SBV_ZOMBIE_SNAIL_COVER.jpg'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','1.5','-i',str(videos[0][0]),'-frames:v','1','-vf','scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720',str(thumb)])
im=Image.open(thumb).convert('RGB');draw=ImageDraw.Draw(im)
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',58)
except: font=ImageFont.load_default()
draw.rounded_rectangle((35,500,1010,674),radius=16,fill=(0,0,0),outline=(255,255,255),width=2)
draw.text((62,515),'THE ZOMBIE SNAIL',font=font,fill=(255,235,65),stroke_width=2,stroke_fill=(0,0,0))
im.save(thumb,quality=93)
# Description + explicit attribution, no assumption of commercial reuse beyond cited file licences.
desc="""A snail’s pulsing, caterpillar-like eyestalks are not science fiction. They are brood sacs of the parasitic flatworm Leucochloridium. This film follows the parasite’s documented life cycle and separates confirmed biology from the exaggerated claim that it fully controls a snail’s mind.

SOURCES & FOOTAGE
• Smithsonian National Museum of Natural History / Smithsonian Insider, “Leucochloridium paradoxum 2,” video by Gilles San Martin via Wikimedia: https://insider.si.edu/2014/11/leucochloridium-paradoxum-2/
• Wikimedia Commons, “Leucochloridium.ogv”: https://commons.wikimedia.org/wiki/File:Leucochloridium.ogv
• Wikimedia Commons, “Ambrette commune 001.ogv”: https://commons.wikimedia.org/wiki/File:Ambrette_commune_001.ogv
• Animal Diversity Web, University of Michigan: https://animaldiversity.org/accounts/Leucochloridium_paradoxum/
• Ataev et al., 2024, “Development and reproduction of sporocysts of Leucochloridium paradoxum,” Invertebrate Biology, DOI: 10.1111/ivb.12443
• Wesołowski & Wesołowska, research summarized by Science in Poland: https://scienceinpoland.pl/en/news/news%2C399642%2Cparasite-exposes-snail-to-bird-attack.html

Footage is credited to its original source. Check each file’s current individual licence and attribution terms before commercial reuse; the Smithsonian-hosted video may have separate terms. Ambient bed is synthesized for this edit.
"""
(p/'SBV_ZOMBIE_SNAIL_DESCRIPTION.txt').write_text(desc)
# Contact sheet and QA.
frames=[]
for t in np.linspace(0,max(0,dur-0.1),20):
 raw=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',f'{t:.3f}','-i',str(out),'-frames:v','1','-vf','scale=320:180','-f','image2pipe','-vcodec','mjpeg','pipe:1'],capture_output=True).stdout
 if raw:
  from PIL import Image
  frames.append((t,Image.open(io.BytesIO(raw)).convert('RGB')))
sheet=Image.new('RGB',(320*4,210*math.ceil(len(frames)/4)),(18,18,18));d=ImageDraw.Draw(sheet)
for i,(t,im) in enumerate(frames):
 x=(i%4)*320;y=(i//4)*210;sheet.paste(im,(x,y));d.text((x+8,y+184),f'{t:.1f}s',fill='white')
sheet.save(p/'SBV_ZOMBIE_SNAIL_CONTACT.jpg',quality=88)
probe=json.loads(run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate:format=duration,size','-of','json',str(out)]))
run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'])
qa={'duration_s':dur,'narration_paragraphs':len(paras),'narration_words':len(script.split()),'segments':segments,'ffprobe':probe,'decode':'PASS','sources':[(str(f),d) for f,d,_ in videos]}
(p/'SBV_ZOMBIE_SNAIL_QA.md').write_text('# Production QA\n\n'+json.dumps(qa,indent=2))
print('FINAL',json.dumps(qa),flush=True)
