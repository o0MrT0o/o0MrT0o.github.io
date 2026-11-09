#!/usr/bin/env python3
"""Locate three original nonfiction birth footage sources, download previews and audit visually.
Rights may require permission; this is PREVIEW research, not a license claim."""
from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw
D=Path("surinam_video_candidates");D.mkdir(exist_ok=True)
candidates=[
("01_french_science","https://www.dailymotion.com/video/x8q9cxt"),
("02_brut_nature","https://www.dailymotion.com/video/x82rxjz"),
("03_pbs_gross_science","https://www.pbs.org/video/gross-science-how-surinam-toads-give-birth/")
]
def sh(cmd,timeout=160):
 r=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout)
 print("CMD",cmd[:4],"RET",r.returncode,"ERROR",r.stderr[-400:],flush=True)
 return r
result=[]
for label,url in candidates:
 record={"name":label,"url":url}
 info=sh(["yt-dlp","--skip-download","--dump-single-json","--no-warnings","--no-playlist",url],timeout=70)
 if info.returncode:
  record["error"]=info.stderr[-500:];result.append(record);continue
 j=json.loads(info.stdout)
 for k in ('title','uploader','duration','license','height','width','description'): record[k]=j.get(k) if k!='description' else (j.get(k) or '')[:300]
 # Limit to 720p, audio not required; if multiple source matches, we need independent takes.
 dest=D/f'{label}.mp4'
 c=sh(["yt-dlp","--no-playlist","--no-warnings","--retries","1",
  "-f","bv*[height<=720]+ba/b[height<=720]/best","--merge-output-format","mp4",
  "--max-filesize","250M","-o",str(dest),url],timeout=140)
 if c.returncode or not dest.exists():
  record['download_error']=c.stderr[-500:];result.append(record);continue
 record['bytes']=dest.stat().st_size
 pb=sh(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_name,codec_type,width,height","-of","json",str(dest)])
 record['ffprobe']=json.loads(pb.stdout) if pb.returncode==0 else {}
 try:
  dr=float(record['ffprobe']['format']['duration'])
  sheet=Image.new('RGB',(5*310,3*230),'#121212');draw=ImageDraw.Draw(sheet)
  for i in range(15):
   t=round(dr*(i+.4)/15,2)
   jpg=D/f'{label}_sample_{i:02d}.jpg'
   ex=sh(["ffmpeg","-v","error","-y","-ss",str(t),"-i",str(dest),"-frames:v","1",str(jpg)])
   if ex.returncode or not jpg.exists():continue
   with Image.open(jpg) as img:
    img.thumbnail((302,199));x=i%5*310;y=i//5*230
    sheet.paste(img,(x+(310-img.width)//2,y));draw.text((x+8,y+204),f'{t:.1f}s',fill='white')
  sheet.save(D/f'{label}_CONTACT.jpg',quality=85)
 except Exception as e:record['thumb_error']=str(e)
 result.append(record);print('CANDIDATE',json.dumps(record,ensure_ascii=False)[:950],flush=True)
(D/'CANDIDATE_QA.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print('DONE',len(result),flush=True)
