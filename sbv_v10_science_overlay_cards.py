#!/usr/bin/env python3
"""SBV science/photo insert overlay cards.
Produce 6 nonobscuring 630x440 transparent overlays and one
fully rendered V8 demonstration; separate PNGs can be placed over V9.
No fake photos, no still footage replacing nature background; videos retain
original audio bit-identically. Original CC BY licensed research images.
"""
from pathlib import Path
import json, os, re, urllib.request, subprocess, shutil, hashlib, math
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter

ROOT=Path.cwd()
ASSETS=ROOT/"overlay_cards"
OUT=ROOT/"overlay_delivery"
ASSETS.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
FILM=ROOT/"baseline"/"SBV_ZOMBIE_ANT_V8_FOREST_ONLY_NO_LAB_NO_REPEATS.mp4"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
fb=ImageFont.truetype(BOLD,27)
fm=ImageFont.truetype(FONT,21)
fs=ImageFont.truetype(FONT,16)
tiny=ImageFont.truetype(FONT,14)
W,H=630,438
CC=(224,193,119,255)
white=(246,246,240,255)
aqua=(106,192,172,255)
photo_sources={
 "hughes_ant":("Ant_infected_by_Ophiocordyceps_unilateralis.png",
     "David P. Hughes, Maj-Britt Pontoppidan, PLOS ONE (2009), CC BY 2.5",
     "https://commons.wikimedia.org/wiki/File:Ant_infected_by_Ophiocordyceps_unilateralis.png"),
 "denis_ant":("Ophiocordyceps_unilateralis_-_Denis_Zabin_-_407452035.jpeg",
     "Denis Zabin (2024), CC BY 4.0, iNaturalist/Wikimedia Commons",
     "https://commons.wikimedia.org/wiki/File:Ophiocordyceps_unilateralis_-_Denis_Zabin_-_407452035.jpeg"),
 "aloony_ant":("Complex_Ophiocordyceps_unilateralis_(Zombie_Ant_Fungus).jpg",
     "Aloony loon (2025), CC BY 4.0, Wikimedia Commons",
     "https://commons.wikimedia.org/wiki/File:Complex_Ophiocordyceps_unilateralis_(Zombie_Ant_Fungus).jpg")
}
def fetch_wikimedia(filename,dest):
 url="https://commons.wikimedia.org/wiki/Special:FilePath/"+urllib.parse.quote(filename,safe="()")
 err=None
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"SBVDocumentaryResearch/1.0 (open-source scientific attribution)", "Accept":"image/*"})
   with urllib.request.urlopen(req,timeout=55) as resp,open(dest,"wb") as f:
    shutil.copyfileobj(resp,f)
   im=Image.open(dest);im.verify()
   if dest.stat().st_size<25_000:raise RuntimeError("not enough bytes")
   return
  except Exception as e:
   err=str(e)
   if dest.exists():dest.unlink()
 raise RuntimeError(f"Licensed image unavailable {filename}: {err}")
loaded={}
for key,(name,credit,page) in photo_sources.items():
 target=ASSETS/("SOURCE_"+key+Path(name).suffix)
 try:
  fetch_wikimedia(name,target)
  loaded[key]=Image.open(target).convert("RGB")
  print("VERIFIED REAL SCIENTIFIC PHOTO",key,loaded[key].size,target.stat().st_size,flush=True)
 except Exception as e:
  print("AUTHOR PHOTO UNAVAILABLE; switching to explicit scientific diagram:",key,str(e)[:100],flush=True)

def card_base():
 im=Image.new("RGBA",(W,H),(0,0,0,0));draw=ImageDraw.Draw(im)
 draw.rounded_rectangle((1,1,W-2,H-2),radius=25,fill=(13,20,21,216),outline=(110,136,119,220),width=2)
 draw.rounded_rectangle((20,17,W-20,68),radius=9,fill=(38,51,50,210))
 draw.rectangle((22,70,W-23,72),fill=CC)
 return im
def fit_photo(src,box):
 left,top,right,bottom=box
 pic=ImageOps.fit(src,(right-left,bottom-top),method=Image.Resampling.LANCZOS,centering=(.5,.5))
 return pic
def label(im,head,lines,credit):
 d=ImageDraw.Draw(im)
 d.text((29,26),head,font=fb,fill=white)
 for i,line in enumerate(lines): d.text((30,352+i*30),line,font=fm,fill=white)
 d.text((30,414),credit,font=tiny,fill=(203,209,207,230))
def photographic(name,source,header,lines,credit):
 img=card_base()
 # Show real photo when download is permitted, otherwise our own clearly
 # labelled original vector illustration — NEVER a generated fake photograph.
 if source in loaded:
  crop=fit_photo(loaded[source],(26,86,W-26,342))
  img.paste(crop,(26,86))
 else:
  d=ImageDraw.Draw(img)
  d.rounded_rectangle((26,88,604,342),radius=12,fill=(30,49,45,255),outline=(63,105,91,255),width=2)
  header="SCHEMATIC  •  "+("DEATH GRIP" if source=="denis_ant" else "FUNGAL CYCLE")
  credit="Original schematic · not a photograph"
  if source=="denis_ant":
   d.line((82,218,533,218),fill=(115,187,130,255),width=12)
   d.ellipse((256,162,367,239),fill=(153,109,64,255),outline=CC,width=5)
   d.ellipse((355,180,397,220),fill=(176,132,78,255))
   d.line((380,191,400,215),fill=CC,width=6)
   d.line((380,226,405,213),fill=CC,width=6)
   d.text((80,108),"MANDIBLES  →  LEAF VEIN",font=fm,fill=white)
  elif source=="aloony_ant":
   d.line((76,280,522,280),fill=(115,187,130,255),width=11)
   d.ellipse((265,231,370,277),fill=(145,100,64,255),outline=CC,width=4)
   d.line((320,229,335,123),fill=(202,179,128,255),width=9)
   d.ellipse((310,100,362,146),fill=(211,184,133,255))
   d.text((65,113),"FRUITING BODY",font=fm,fill=white)
  else:
   for cx,cy in [(112,226),(262,226),(412,226)]:
    d.ellipse((cx-37,cy-37,cx+37,cy+37),fill=(78,116,96,255),outline=aqua,width=4)
   d.line((152,225,220,225),fill=CC,width=5)
   d.line((302,225,370,225),fill=CC,width=5)
   d.text((50,111),"SPORES   →   INFECTION   →   GROWTH",font=fs,fill=white)
 label(img,header,lines,credit)
 img.save(ASSETS/(name+".png"))
 return ASSETS/(name+".png")

p1=photographic("01_real_zombie_ant","hughes_ant","REAL INFECTED ANT",
 ["Documented on forest vegetation"],"Hughes & Pontoppidan (2009) · CC BY 2.5")
p2=photographic("03_death_grip_photo","denis_ant","THE DEATH GRIP",
 ["Ant fixed to vegetation"],"Denis Zabin (2024) · CC BY 4.0")
p3=photographic("06_fungal_reproductive_stalk","aloony_ant","AFTER DEATH",
 ["Fungal structures develop"],"Aloony loon (2025) · CC BY 4.0")
def round_rect(d,box,fill=None,outline=None,r=16,width=2):
 d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
def diagram(name,title,lines,mode,credit):
 img=card_base();d=ImageDraw.Draw(img)
 d.text((30,27),title,font=fb,fill=white)
 if mode=="spores":
  # conceptual diagram, not a photographic claim.
  d.ellipse((70,152,230,281),fill=(49,72,64,255),outline=aqua,width=5)
  d.line((230,216,345,216),fill=CC,width=7)
  for x,y in [(351,174),(389,211),(417,264),(354,285),(471,199)]:
   d.ellipse((x-8,y-8,x+8,y+8),fill=CC)
  d.text((62,118),"SOURCE",font=fm,fill=aqua)
  d.text((338,123),"SPORES",font=fm,fill=CC)
 elif mode=="muscle":
  for xx in [82,154,226,298,370,442]:
   d.rounded_rectangle((xx,135,xx+36,287),radius=13,fill=(67,108,103,225),outline=aqua,width=3)
  for cx,cy in [(65,172),(135,254),(214,202),(344,165),(412,285),(500,230)]:
   d.ellipse((cx-15,cy-13,cx+15,cy+13),fill=(202,166,94,245),outline=CC,width=2)
  d.text((33,100),"MUSCLE FIBERS",font=fs,fill=aqua)
  d.text((347,100),"FUNGAL CELLS",font=fs,fill=CC)
 elif mode=="brain":
  d.ellipse((228,135,400,284),fill=(48,87,79,255),outline=aqua,width=5)
  d.text((262,195),"BRAIN",font=fm,fill=white)
  for cx,cy in [(164,145),(155,241),(468,156),(466,246),(198,294),(438,300)]:
   d.ellipse((cx-14,cy-14,cx+14,cy+14),fill=CC)
  d.text((37,107),"FUNGAL CELLS OUTSIDE",font=fs,fill=CC)
  # avoids saying fungus never affects the brain — only no cells detected within.
 elif mode=="habitat":
  d.line([(83,290),(203,160),(290,232),(402,102),(523,216)],fill=aqua,width=8,joint="curve")
  for x,y in [(84,290),(203,160),(290,232),(402,102),(523,216)]:
   d.ellipse((x-14,y-14,x+14,y+14),fill=CC)
  d.text((76,108),"HUMID FOREST UNDERSTORY",font=fm,fill=aqua)
 for i,line in enumerate(lines):
  d.text((29,351+i*29),line,font=fm,fill=white)
 d.text((30,414),credit,font=tiny,fill=(203,209,207,230))
 img.save(ASSETS/(name+".png"))
 return ASSETS/(name+".png")

p4=diagram("02_spore_path","INFECTION BEGINS",
           ["Spores reach the ant's cuticle"],"spores","Schematic · illustrative")
p5=diagram("04_muscles","FUNGUS AND MUSCLES",
           ["Fungal cells surround muscle fibers"],"muscle","Schematic · Mangold et al. (2019)")
p6=diagram("05_brain","BRAIN NOT INVADED",
           ["No fungal cells found inside","the brain in a 2017 study"],"brain","Schematic · Fredericksen et al. (2017)")

# Position on 1920x1080 film, x/y in pixels. At most 12.5% of frame area.
# These are starting points for user-owned V9, which may have a slightly
# different narration timing. Do not imply perfect word synchronization.
timeline=[
 {"file":p4.name,"start":39.3,"end":43.9,"x":1200,"y":100,"description":"spores / early infection"},
 {"file":p1.name,"start":48.5,"end":53.2,"x":1200,"y":100,"description":"scientifically documented infection photograph"},
 {"file":p2.name,"start":111.5,"end":116.5,"x":1200,"y":100,"description":"mandibles and death grip"},
 {"file":p5.name,"start":139.0,"end":143.8,"x":1200,"y":100,"description":"fungal cells and muscle fibers"},
 {"file":p6.name,"start":172.0,"end":177.2,"x":1200,"y":100,"description":"brain not colonized in 2017"},
 {"file":p3.name,"start":206.0,"end":211.2,"x":1200,"y":100,"description":"fruiting body emerging after death"},
]
# Every individual scientific PHOTO is used once. Some diagrams factual, labelled.
assert len(timeline)==len(set(t["file"] for t in timeline))
(OUT/"OVERLAY_TIMELINE.json").write_text(json.dumps(timeline,indent=2))
(OUT/"REAL_PHOTO_CREDITS.txt").write_text(
 "STRANGE, BUT VERIFIED — SCIENTIFIC PICTURE-IN-PICTURE PHOTO + SCHEMATIC OVERLAYS\n"
 "Research photograph source references (included only if downloaded successfully):\n"
 +"\n".join(f"{name}: {license} | {url}" for name,(filename,license,url) in photo_sources.items())
 +"\n\nThese images are real ant–fungus photographs, not generated. Displayed at "
 "small size over continuous forest footage and modified by crop/caption/card frame.\n"
 "Conceptual vector schematics drawn for this video, explicitly labelled 'Schematic'. "
 "The graphic 'No fungal cells detected inside brain in a 2017 study' does not claim the brain is unaffected.\n"
 "Important: Some field footage beneath cards shows ordinary uninfected ants; do not claim otherwise.\n"
 "Research: Fredericksen et al. (2017) DOI 10.1073/pnas.1711673114; "
 "Mangold et al. (2019) DOI 10.1242/jeb.200683; "
 "Hughes et al. (2011) DOI 10.1186/1472-6785-11-13.\n"
 "The photographic overlays are not separate moving footage and each photo is shown once.\n"
)
for card in ASSETS.glob("*.png"):
 shutil.copy2(card,OUT/card.name)
# Printable screenshot visual storyboard showing the overlays actual scale.
preview=Image.new("RGB",(1920,1080),(30,55,43));d=ImageDraw.Draw(preview)
d.rectangle((0,775,1920,1080),fill=(16,28,24))
d.text((80,820),"CONTINUOUS NATURE FOOTAGE — sample only",font=ImageFont.truetype(BOLD,48),fill=white)
preview.paste(Image.open(p2), (1200,100),Image.open(p2))
preview.save(OUT/"EXAMPLE_PICTURE_IN_PICTURE_FRAME.jpg",quality=91)
print("CARD PACK:",len(timeline),"PIP overlays; real photos embedded:",len(loaded),"; original schematics:",6-len(loaded),flush=True)
# Render baseline DEMONSTRATION to show correct 4K-like picture-in-picture
# composition. This is V8 footage, NOT user's locally authored V9 master.
if os.getenv("SBV_SKIP_DEMO")=="1":
 print("ALL PNG OVERLAY ASSETS COMPLETE; demonstration video skipped.",flush=True)
 exit()
if not FILM.exists():
 print("NO DEMO VIDEO AVAILABLE, OVERLAYS READY",flush=True)
 exit()
inputs=["-i",str(FILM)]
filter_parts=[]
prev="[0:v]"
for i,task in enumerate(timeline,start=1):
 inputs.extend(["-loop","1","-framerate","30","-i",str(ASSETS/task["file"])])
 label=f"[card{i}]"
 start=float(task["start"]);end=float(task["end"])
 filter_parts.append(
  f"[{i}:v]format=rgba,fade=t=in:st={start:.2f}:d=0.36:alpha=1,"
  f"fade=t=out:st={end-0.36:.2f}:d=0.36:alpha=1{label}"
 )
 vout=f"[v{i}]"
 filter_parts.append(
  f"{prev}{label}overlay=x={task['x']}:y={task['y']}:"
  f"enable='between(t,{start:.2f},{end:.2f})':"
  f"shortest=1{vout}"
 )
 prev=vout
demopath=OUT/"SBV_V8_PROOF_WITH_SCIENCE_OVERLAYS.mp4"
ff=["ffmpeg","-hide_banner","-loglevel","error","-y",*inputs,
 "-filter_complex",";".join(filter_parts),"-map",prev,"-map","0:a:0",
 "-c:v","libx264","-preset","veryfast","-crf","20",
 "-pix_fmt","yuv420p","-r","30","-c:a","copy",
 "-movflags","+faststart",str(demopath)]
print("RENDER COMPOSITED SCIENTIFIC CARDS OVER DEMO BASELINE",flush=True)
p=subprocess.run(ff,capture_output=True,text=True)
if p.returncode:raise RuntimeError(p.stderr[-4000:])
p=subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(demopath),"-f","null","-"],capture_output=True,text=True)
if p.returncode:raise RuntimeError("Full decode failed: "+p.stderr[-1500:])
print("VIDEO PROOF PASS",demopath.name,demopath.stat().st_size,flush=True)
