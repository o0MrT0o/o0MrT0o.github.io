#!/usr/bin/env python3
from pathlib import Path
import subprocess,json, numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path.cwd()
v7=P/"v7_reference"/"SBV_ZOMBIE_ANT_V7_BALANCED_NATURE_SOUND.mp4"
v8=P/"v8_reference"/"SBV_ZOMBIE_ANT_V8_FOREST_ONLY_NO_LAB_NO_REPEATS.mp4"
out=P/"v9_audit";out.mkdir(exist_ok=True)
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",15)
def sample(src,t):
 args=["ffmpeg","-hide_banner","-loglevel","error","-ss",str(t),"-i",str(src),
 "-frames:v","1","-vf","scale=512:288","-pix_fmt","rgb24","-f","rawvideo","-"]
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode or len(p.stdout)!=512*288*3:raise RuntimeError(p.stderr[-600:].decode())
 a=np.frombuffer(p.stdout,dtype="uint8").reshape(288,512,3)
 g=a.mean(axis=2)
 rows=g[60:228]
 low_left=np.mean(rows[:,:150]<22)
 low_right=np.mean(rows[:,-150:]<22)
 center=np.mean(rows[:,196:316]>34)
 return Image.fromarray(a),{"outer_dark_left":round(float(low_left),3),"outer_dark_right":round(float(low_right),3),"center_visible":round(float(center),3)}
times=[3,21,30,47,58,59,60,61,62,63,64,90,99,110,120,205,241]
pairs=[]
results=[]
for t in times:
 old,metric7=sample(v7,t)
 new,metric8=sample(v8,t)
 results.append({"sec":t,"v7":metric7,"v8":metric8})
 pairs.append((t,old,new,metric7,metric8))
sheet=Image.new("RGB",(2*540,len(pairs)*338),(18,21,23))
p=ImageDraw.Draw(sheet)
for i,(t,a,b,o,n) in enumerate(pairs):
 y=i*338+28
 sheet.paste(a,(12,y));sheet.paste(b,(552,y))
 p.text((12,y-23),f"V7 older | {t:03}s | blacks L={o['outer_dark_left']:.2f} R={o['outer_dark_right']:.2f}",font=font,fill="white")
 p.text((552,y-23),f"V8 current | {t:03}s | blacks L={n['outer_dark_left']:.2f} R={n['outer_dark_right']:.2f}",font=font,fill="white")
sheet.save(out/"V7_VS_V8_ACTUAL_FRAMES_COMPARISON.jpg",quality=86,optimize=True)
(out/"V7_VS_V8_1MIN01_COMPARE.json").write_text(json.dumps(results,indent=2))
print("1:01 sample comparison:",json.dumps(next(x for x in results if x["sec"]==61),indent=2),flush=True)
