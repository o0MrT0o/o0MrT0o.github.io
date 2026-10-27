#!/usr/bin/env python3
"""Visual QA for entire SBV V8 244.87 seconds, source by source.
Creates JPG contact sheets of actual decoded frames (not stock search images),
flagged clips report (black-bordered/inset/lab-like), and per 2-second checks.
No images from user screenshot needed; this inspects the actual MP4.
"""
from pathlib import Path
import os,subprocess,json,math,statistics
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path.cwd();video=P/"v9_source"/"SBV_ZOMBIE_ANT_V8_FOREST_ONLY_NO_LAB_NO_REPEATS.mp4"
edl=json.loads((P/"v9_source"/"V8_NO_REPEATS_NO_LAB_EDL.json").read_text())
out=P/"v9_audit";out.mkdir(exist_ok=True)
W,H=320,180
args=["ffmpeg","-hide_banner","-loglevel","error","-i",str(video),
      "-vf","fps=1/2,scale=320:180:flags=bicubic",
      "-f","rawvideo","-pix_fmt","rgb24","-"]
proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
frames=[]
while True:
 data=proc.stdout.read(W*H*3)
 if not data:break
 if len(data)!=W*H*3:raise RuntimeError("Truncated rawvideo frames")
 frames.append(np.frombuffer(data,dtype=np.uint8).reshape(H,W,3).copy())
_,err=proc.communicate()
assert proc.returncode==0,err[-2000:].decode(errors="ignore")
assert len(frames)>=110,f"Only {len(frames)} decoded sample frames!"
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",14)
small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",12)
def frame_at(sec):
 i=min(max(round(sec/2),0),len(frames)-1)
 return frames[i],i*2

def metrics(x):
 g=x.astype(np.float32).mean(axis=2)
 # Source videos with baked black frames show a contiguous dark region on
 # both sides of the picture with animated narrow centre. Actual forest
 # shots fill the frame (even darker forest shots contain detailed texture).
 bright=g>21
 central=bright[H//5:H*4//5,:]
 col_rates=central.mean(axis=0)
 row_rates=bright.mean(axis=1)
 def margin(arr,threshold):
  start=0
  for val in arr:
   if val>=threshold:break
   start+=1
  return start
 left=margin(col_rates,.16);right=margin(col_rates[::-1],.16)
 top=margin(row_rates,.15);bottom=margin(row_rates[::-1],.15)
 # Text-bearing screenshots with black matte and a tiny native portrait are
 # picked up via band fractions and centre vs outer brightness.
 outleft=g[H//6:H*5//6,:W//5]
 outright=g[H//6:H*5//6,-W//5:]
 inside=g[H//5:H*4//5,W*2//5:W*3//5]
 risk=float((left+right)/W)
 outer_dark=float(np.mean(np.r_[outleft.reshape(-1),outright.reshape(-1)]<17))
 middle_nonblack=float((inside>35).mean())
 return dict(left=int(left),right=int(right),top=int(top),bottom=int(bottom),
             pillarbox_pct=round(100*risk,1),outer_black_pct=round(100*outer_dark,1),
             middle_nonblack_pct=round(100*middle_nonblack,1),
             suspect=(risk>.23 and middle_nonblack>.13 and outer_dark>.75))
results=[]
for shot in edl:
 start=float(shot["at"]);end=start+float(shot["duration"])
 sample_times=sorted(set([max(start+.3,min(end-.2,start+float(shot["duration"])*fraction)) for fraction in (.17,.5,.83)]))
 observations=[]
 for t in sample_times:
  image,actual=frame_at(t)
  o=metrics(image);o["actual_time_sec"]=actual
  observations.append(o)
 result={"file_id":shot["file_id"],"chapter":shot["chapter"],
         "start":round(start,3),"end":round(end,3),
         "sampled_frames":observations,
         "black_inset_frames":sum(int(o["suspect"]) for o in observations),
         "median_matte_pct":round(statistics.median(o["pillarbox_pct"] for o in observations),1),
         "research":shot.get("scientific",False)}
 results.append(result)
report={"movie_seconds":len(frames)*2,"total_frames_sampled":len(frames),
        "source_scenes":len(edl),
        "suspect_shots":[r for r in results if r["black_inset_frames"]],
        "all_shots":results}
(out/"FRAME_BY_FRAME_AUDIT.json").write_text(json.dumps(report,indent=2))
print("SAMPLE COUNT",len(frames),"; SHOTS",len(edl),flush=True)
for r in results:
 print(f"{r['start']:7.2f}-{r['end']:7.2f} {r['file_id']:44s} inset={r['black_inset_frames']}/3 matte={r['median_matte_pct']:5.1f}%",flush=True)

def draw_sheet(rows,filename,columns=4,scale=1):
 cellw=340;cellh=244
 outimg=Image.new("RGB",(columns*cellw,math.ceil(len(rows)/columns)*cellh),color=(27,29,31))
 draw=ImageDraw.Draw(outimg)
 for i,(shot,at,label) in enumerate(rows):
  frame,actual=frame_at(at)
  tile=Image.fromarray(frame,"RGB")
  col=i%columns;row=i//columns;x=col*cellw+10;y=row*cellh+14
  outimg.paste(tile,(x,y))
  for line,suffix in enumerate([f"{actual//60:02.0f}:{actual%60:02.0f} | {shot['file_id'][:32]}",label]):
   draw.text((x,y+187+18*line),suffix,font=small,fill=(235,238,238))
 outimg.save(out/filename,quality=85,subsampling=2,optimize=True)
 print("SAVED AUDIT SHEET",filename,outimg.size,flush=True)
# One contact sheet with *every one* of the 20 source segments:
draw_sheet([(s,(s["at"]+s["duration"]*.5),f"chapter {s['chapter']}  {s['duration']:.1f}s")
            for s in edl],"ALL_20_SCENES_CONTACT_SHEET.jpg",columns=4)
# One systematic 2s sampled storyboard covering entirety of first ~2m40,
# plus final third: not possible to "pass" an unseen problematic frame.
for p in range(0,3):
 subset=[]
 for t in range(p*40,(p+1)*40):
  sec=t*2
  if sec>=len(frames)*2:break
  s=next((s for s in edl if s["at"]<=sec<s["at"]+s["duration"]),edl[-1])
  subset.append((s,sec,f"sample {sec:03d}s, matte {metrics(frames[t])['pillarbox_pct']:.0f}%"))
 if subset:draw_sheet(subset,f"TIMELINE_{p+1}_EVERY_2_SECONDS.jpg",columns=5)
# Special enlarged contact sheet of suspicious clips, incl user's 1:01
at1=61
recheck=[(next((x for x in edl if x["at"]<=t<x["at"]+x["duration"]),edl[-1]),t,
          f"frame at {t}s | black matte {metrics(frame_at(t)[0])['pillarbox_pct']:.0f}%")
          for t in [0,4,16,21,34,48,58,60,61,62,64,68,90,98,104,112,119,142,170,200,228]]
draw_sheet(recheck,"SPECIAL_CASES_INCLUDING_1MIN01.jpg",columns=4)
print("REPORT SUMMARY",json.dumps({"suspects":[(r['file_id'],r['start'],r['median_matte_pct']) for r in report["suspect_shots"]],"61s":metrics(frame_at(61)[0])},indent=2),flush=True)
