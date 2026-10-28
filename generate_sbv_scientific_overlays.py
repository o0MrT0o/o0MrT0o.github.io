from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
import urllib.request, shutil, json, zipfile, math, os
P=Path.cwd();O=P/"scientific_overlay_pack";O.mkdir(exist_ok=True)
SRC=O/"original_sources";SRC.mkdir(exist_ok=True)
FB="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def ft(z,b=False):return ImageFont.truetype(FB if b else FR,z)
def get(tag,url,optional=False):
 p=SRC/(tag+".png")
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
  with urllib.request.urlopen(req,timeout=75) as response,open(p,"wb") as f:shutil.copyfileobj(response,f)
  with Image.open(p) as im:im.verify()
  if p.stat().st_size<10000:raise RuntimeError("Suspiciously small source image")
  print("SOURCE",tag,p.stat().st_size,flush=True)
  return p
 except Exception as e:
  if optional:
   print("Optional photo unavailable, fallback to 2011 Figure 1:",repr(e),flush=True)
   return None
  raise
BASE="https://media.springernature.com/full/springer-static/image/art%3A10.1186%2F1472-6785-11-13/MediaObjects/"
fig={
  "field":get("BMC_2011_Fig1",BASE+"12898_2011_173_Fig1_HTML.jpg"),
  "head":get("BMC_2011_Fig3",BASE+"12898_2011_173_Fig3_HTML.jpg"),
  "muscle":get("BMC_2011_Fig4",BASE+"12898_2011_173_Fig4_HTML.jpg"),
  "bite":get("BMC_2011_Fig5",BASE+"12898_2011_173_Fig5_HTML.jpg"),
}
real=get("Wikimedia_original_infected_ant",
 "https://commons.wikimedia.org/wiki/Special:FilePath/Ant_infected_by_Ophiocordyceps_unilateralis.png",True)
if real:fig["infected"]=real
else:fig["infected"]=fig["field"]
photo_license="Hughes and Pontoppidan (2009), PLOS ONE, CC BY 2.5" if real else "Hughes et al. (2011), BMC Ecology, CC BY 2.0"
def base(title,subtitle,source_tag):
 img=Image.new("RGBA",(740,476),(0,0,0,0));d=ImageDraw.Draw(img)
 d.rounded_rectangle((4,4,735,470),radius=23,fill=(14,23,20,224),outline=(172,159,106,235),width=3)
 d.rounded_rectangle((28,23,205,57),radius=6,fill=(43,55,39,242))
 d.text((39,31),source_tag.upper(),font=ft(14,True),fill=(226,186,107))
 d.text((28,67),title,font=ft(30,True),fill=(250,249,240))
 d.text((28,108),subtitle,font=ft(18),fill=(199,208,201))
 return img
def photo(number,name,title,subtitle,src,credit):
 c=base(title,subtitle,"REAL RESEARCH FIGURE")
 p=Image.open(src).convert("RGB")
 p=ImageOps.contain(p,(646,268),Image.Resampling.LANCZOS)
 x=(740-p.width)//2;y=154+(268-p.height)//2
 d=ImageDraw.Draw(c);d.rounded_rectangle((32,146,706,425),radius=8,fill=(32,36,32,255))
 c.paste(p,(x,y))
 d=ImageDraw.Draw(c)
 d.text((27,445),"SOURCE: "+credit[:94],font=ft(12),fill=(206,209,196))
 path=O/(f"{number:02d}_{name}.png");c.save(path);return path.name
files=[]
files.append(photo(1,"REAL_INFECTED_ANT","A REAL ZOMBIE ANT","Ophiocordyceps-infected host",fig["infected"],photo_license))
files.append(photo(2,"BITE_MARKS","THE DEATH GRIP","Actual marks left in leaf tissue",fig["bite"],"Hughes et al. 2011, Fig 5, CC BY 2.0"))
files.append(photo(3,"MUSCLE_MICROSCOPY","MANDIBLE MUSCLES","Microscopy: infected and healthy tissue",fig["muscle"],"Hughes et al. 2011, Fig 4, CC BY 2.0"))
files.append(photo(4,"ANT_HEAD_MICROSCOPY","INSIDE THE HEAD","Fungal cells in real ant tissue sections",fig["head"],"Hughes et al. 2011, Fig 3, CC BY 2.0"))
gold=(226,187,100);cream=(246,239,215)
c=base("THE BRAIN IS NOT INVADED","No fungal cells detected INSIDE the brain","SCHEMATIC")
d=ImageDraw.Draw(c)
d.ellipse((212,164,495,406),fill=(91,130,117),outline=(182,209,190),width=7)
for x,y in [(260,202),(330,217),(395,236),(254,299),(315,338),(407,331)]:
 d.arc((x,y,x+75,y+64),35,300,fill=(175,210,189),width=5)
for x,y in [(193,202),(518,204),(197,350),(510,355),(360,154),(363,423)]:
 d.ellipse((x-10,y-10,x+10,y+10),fill=gold)
d.line((510,207,606,179),fill=gold,width=3)
d.text((537,144),"FUNGAL",font=ft(18,True),fill=cream)
d.text((537,164),"CELLS",font=ft(18,True),fill=cream)
d.text((27,446),"SCHEMATIC • FREDERICKSEN ET AL. 2017, PNAS",font=ft(12),fill=cream)
c.save(O/"05_BRAIN_SCHEMATIC.png");files.append("05_BRAIN_SCHEMATIC.png")
c=base("AFTER DEATH","Fungal stalk forms and releases spores","SCHEMATIC")
d=ImageDraw.Draw(c)
d.ellipse((152,336,476,395),fill=(72,54,39),outline=(165,131,91),width=5)
d.ellipse((284,286,400,359),fill=(114,77,52),outline=(177,142,95),width=5)
d.line([(359,288),(365,233),(396,196),(393,167)],fill=(210,174,105),width=13,joint="curve")
d.ellipse((365,143,425,195),fill=(194,155,82),outline=(228,192,107),width=5)
for x,y in [(458,160),(486,185),(524,200),(485,244),(552,238),(593,164),(564,133),(608,213)]:
 d.ellipse((x-4,y-4,x+4,y+4),fill=gold)
d.text((510,121),"SPORES",font=ft(18,True),fill=cream)
d.text((27,446),"SCHEMATIC • HUGHES ET AL. 2011, BMC ECOLOGY",font=ft(12),fill=cream)
c.save(O/"06_SPORE_SCHEMATIC.png");files.append("06_SPORE_SCHEMATIC.png")
# Precise spoken-word alignment should be reviewed. Suggested positions:
timing=[
 ("00:32",6,"right","infected host photo",files[0]),
 ("01:42",6,"left","evidence of death grip",files[1]),
 ("02:04",7,"right","mandible pathology",files[2]),
 ("02:27",6,"left","original microscopy in head",files[3]),
 ("02:47",7,"right","2017 brain observation schematic",files[4]),
 ("03:29",7,"left","spores after ant death schematic",files[5])
]
(O/"SUGGESTED_V9_OVERLAY_CUES.json").write_text(json.dumps([
 {"start":t,"duration_seconds":dur,"side":side,"concept":concept,"file":file,"illustrative_not_original":(n>=4)}
 for n,(t,dur,side,concept,file) in enumerate(timing)],indent=2))
(O/"SOURCES_AND_CREDITS.txt").write_text(
 "STRANGE, BUT VERIFIED — SIX SCIENCE PICTURE-IN-PICTURE CARDS, 740x476 transparent PNGs. "
 "Use at most ~40 percent of 1920x1080 frame and fade in/out 0.5 sec.\n"
 "01: Hughes and Pontoppidan 2009, PLOS ONE CC BY 2.5, Wikimedia Commons, or 2011 Figure 1 CC BY 2.0 fallback. "
 "02/03/04: Hughes et al. 2011, Behavioral mechanisms and morphological symptoms of zombie ants dying from fungal infection, BMC Ecology 11:13, "
 "doi.org/10.1186/1472-6785-11-13, original Figures 5,4,3, CC BY 2.0. The figure images were reformatted into labeled overlays.\n"
 "05: ORIGINAL SCHEMATIC based on Fredericksen et al. 2017 PNAS doi.org/10.1073/pnas.1711673114. NOT a photograph or real micrograph. "
 "06: ORIGINAL SCHEMATIC based on Hughes et al. 2011, CC BY 2.0. NOT an observed specimen photograph.\n"
 "IMPORTANT: Overlay times are suggestions, align precisely to narrator when completing V9. "
 "The 1920x1080 documentary video remains moving in the background.\n")
# Create ffmpeg overlay renderer ready to apply to the user's own V9 file.
# Single command; never remove source audio, overlay images appear only as brief side cards.
inputs=[];parts=[]
for i,(at,duration,side,concept,f) in enumerate(timing,1):
 inputs+=["-loop","1","-framerate","30","-i",f]
 st=int(at.split(":")[0])*60+int(at.split(":")[1])
 x="W-w-60" if side=="right" else "60"
 parts.append(f"[{i}:v]format=rgba,trim=duration={duration},fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st={duration-0.5}:d=0.5:alpha=1,setpts=PTS-STARTPTS+{st}/TB[ov{i}]")
 pre=f"[v{i-1}]" if i>1 else "[0:v]"
 parts.append(f"{pre}[ov{i}]overlay=x={x}:y=110:repeatlast=0:eof_action=pass[v{i}]")
render=["ffmpeg","-hide_banner","-y","-i","SBV_ZOMBIE_ANT_V9_YOUTUBE_READY_MASTER.mp4"]+inputs+[
 "-filter_complex",";".join(parts),"-map","[v6]","-map","0:a:0",
 "-c:v","libx264","-preset","medium","-crf","18","-r","30",
 "-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",
 "OUTPUT_V9_WITH_SCIENCE_CARDS.mp4"]
(O/"FFMPEG_COMMAND.json").write_text(json.dumps(render,indent=2))
import shlex
(O/"apply_overlays_when_V9_is_available.sh").write_text("#!/bin/sh\nset -eu\n"+" ".join(shlex.quote(x) for x in render)+"\n")
zippath=P/"SBV_V9_SCIENCE_OVERLAY_ASSET_PACK.zip"
with zipfile.ZipFile(zippath,"w",zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for file in O.iterdir():
  if file.is_file():z.write(file,file.name)
print("DONE",json.dumps({"cards":files,"zip_size":zippath.stat().st_size,"cues":timing},indent=2),flush=True)
