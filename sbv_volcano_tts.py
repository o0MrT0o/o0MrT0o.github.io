#!/usr/bin/env python3
from pathlib import Path
import json,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
D=Path("sbv_volcano_voice");D.mkdir(exist_ok=True)
model=Kokoro("models/kokoro-v1.0.onnx","models/voices-v1.0.bin")
lines=[
"Watch glowing rocks get sucked into a spinning vortex.",
"This isn't a tornado. It's a volcanic whirlwind.",
"At Hawaii's Kilauea, hot lava sends air racing upward.",
"The rotating air can rip glowing chunks from the lava's surface...",
"and fling them into the sky."
]
parts=[];segments=[];t=0
for i,txt in enumerate(lines):
 a,sr=model.create(txt,voice="af_heart",speed=.97,lang="en-us",trim=True,continuous=True)
 assert sr==24000
 a=np.asarray(a,dtype="float32").reshape(-1)
 pause=.10 if i<len(lines)-1 else .5
 d=len(a)/sr
 segments.append({"text":txt,"start":round(t,3),"vo_end":round(t+d,3),"end":round(t+d+pause,3),"duration":round(d,3)})
 parts.extend([a,np.zeros(round(pause*sr),dtype=np.float32)])
 t+=d+pause
 print("VOICE",i,round(d,2),txt,flush=True)
sf.write(D/"Volcano_Vortex_Kokoro_af_heart.wav",np.concatenate(parts),24000,subtype="PCM_24")
(D/"voice_timing.json").write_text(json.dumps({"duration":t,"segments":segments},indent=2))
print("TOTAL_SECONDS",t)
