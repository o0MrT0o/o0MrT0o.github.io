#!/usr/bin/env python3
"""Acquire actual licensed Wikimedia Commons stills for the zombie ant documentary."""
import hashlib,urllib.parse,urllib.request,time,json,os
from pathlib import Path
from PIL import Image
P=Path("v10_stills");P.mkdir(exist_ok=True)
records=[
 ("01_hughes_ant_under_leaf","Ophiocordyceps unilateralis A.png","David P. Hughes; Maj-Britt Pontoppidan","CC BY 2.5","https://creativecommons.org/licenses/by/2.5/","https://commons.wikimedia.org/wiki/File:Ophiocordyceps_unilateralis_A.png","Infected Camponotus leonardi beneath rainforest leaf"),
 ("02_hughes_death_grip_closeup","Ophiocordyceps unilateralis B.png","David P. Hughes; Maj-Britt Pontoppidan","CC BY 2.5","https://creativecommons.org/licenses/by/2.5/","https://commons.wikimedia.org/wiki/File:Ophiocordyceps_unilateralis_B.png","Close-up death grip and emerging fungus, Thailand"),
 ("03_denis_zabin_wild","Ophiocordyceps unilateralis - Denis Zabin - 407452035.jpeg","Denis Zabin","CC BY 4.0","https://creativecommons.org/licenses/by/4.0/","https://commons.wikimedia.org/wiki/File:Ophiocordyceps_unilateralis_-_Denis_Zabin_-_407452035.jpeg","Real infected ant, field photograph Brazil"),
 ("04_chandu_bandi_ophio","Ophiocordyceps.jpg","ChanduBandi","CC BY 4.0","https://creativecommons.org/licenses/by/4.0/","https://commons.wikimedia.org/wiki/File:Ophiocordyceps.jpg","Ophiocordyceps fungus growing from Polyrhachis exercita ant"),
 ("05_aloony_loon_zombie_ant","Complex Ophiocordyceps unilateralis (Zombie Ant Fungus).jpg","Aloony loon","CC BY 4.0","https://creativecommons.org/licenses/by/4.0/","https://commons.wikimedia.org/wiki/File:Complex_Ophiocordyceps_unilateralis_(Zombie_Ant_Fungus).jpg","Genuine forest fungus and insect photograph"),
]
manifest=[]
for dest,name,author,license,license_url,source,description in records:
 escaped=urllib.parse.quote(name.replace(' ','_'),safe='()')
 md5=hashlib.md5(name.replace(' ','_').encode('utf-8')).hexdigest()
 url=f"https://upload.wikimedia.org/wikipedia/commons/{md5[0]}/{md5[:2]}/{escaped}"
 path=P/(dest+("." + name.rsplit(".",1)[1].lower()))
 err=None
 for attempt in range(4):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"SBV-Documentary-Credited-Images/1.0 (educational; github.com/o0MrT0o)"})
   with urllib.request.urlopen(req,timeout=45) as f,open(path,'wb') as o:
    import shutil;shutil.copyfileobj(f,o)
   if path.stat().st_size<25000:raise RuntimeError("Not an image")
   with Image.open(path) as im:
    im.verify()
   with Image.open(path) as im:
    w,h=im.size
   manifest.append({"key":dest,"filename":path.name,"author":author,"license":license,"license_url":license_url,"source_page":source,"description":description,"download_url":url,"width":w,"height":h,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"changes":"Crop and scale into a smaller on-video photographic panel; subtle fade overlay, no subject alterations."})
   print("LICENSED IMAGE VERIFIED",dest,name,w,h,path.stat().st_size,flush=True)
   break
  except Exception as e:
   err=str(e)
   if path.exists():path.unlink()
   print("RETRY",dest,str(e)[:250],flush=True)
   time.sleep(2)
 else: print("ERROR PHOTO",dest,err,flush=True)
if len(manifest)<4:raise RuntimeError("Fewer than 4 verified independent images; refusing to use unlicensed substitutes")
(P/"ORIGINAL_PHOTO_CREDITS.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with open(P/"CREDITS_TO_APPEND_TO_YOUTUBE_DESCRIPTION.txt","w") as out:
 out.write("Authentic Ophiocordyceps photo overlays (photos shown partially over moving field footage; each used once):\n")
 for x in manifest:
  out.write(f"{x['description']} — {x['author']}, {x['license']} ({x['license_url']}), {x['source_page']}. Adjusted: cropped, resized, faded as overlay.\n")
print("DONE",len(manifest),flush=True)
