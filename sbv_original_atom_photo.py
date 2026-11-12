#!/usr/bin/env python3
"""Recover the photographer's own high-resolution unaltered source image for editorial review."""
from pathlib import Path
import requests,re,json,html
from bs4 import BeautifulSoup
D=Path("single_atom_original_image");D.mkdir(exist_ok=True)
u="https://klickverbot.at/blog/2018/02/photographing-a-single-atom/"
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; educational-media-research/1.0)"})
r=s.get(u,timeout=45);r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
imglist=[]
for tag in soup.select("img,a"):
 href=tag.get("src") if tag.name=="img" else tag.get("href")
 if href and any(x in href.lower() for x in ("jpg","jpeg","png","webp")):
  imglist.append(dict(kind=tag.name,href=href,alt=tag.get("alt",""),title=tag.get("title","")))
print("IMG LIST",json.dumps(imglist,ensure_ascii=False)[:12000],flush=True)
# Collect unique candidates; prefer anchor linking to full-quality version.
urls=[]
for d in imglist:
 href=d["href"]
 if href.startswith("/"):href="https://klickverbot.at"+href
 if href.startswith("http"):urls.append(href)
urls=list(dict.fromkeys(urls))
results=[]
for i,url in enumerate(urls[:25]):
 try:
  rr=s.get(url,timeout=50);rr.raise_for_status()
  if not rr.headers.get("Content-Type","").startswith("image/"):continue
  data=rr.content
  name=re.sub(r'[^a-zA-Z0-9._-]+','_',url.split("/")[-1])[:110]
  path=D/(f"{i:02d}_"+name)
  path.write_bytes(data)
  results.append(dict(path=str(path),bytes=len(data),url=url))
  print("SAVED",path,len(data),flush=True)
 except Exception as e:print("FAIL",url,str(e)[:150],flush=True)
(D/"CANDIDATES.json").write_text(json.dumps(results,indent=2))
