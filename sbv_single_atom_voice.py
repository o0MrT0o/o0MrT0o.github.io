#!/usr/bin/env python3
from pathlib import Path
import json,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
D=Path("atom_voice");D.mkdir(exist_ok=True)
model=Kokoro("models/kokoro-v1.0.onnx","models/voices-v1.0.bin")
lines=[
"That tiny violet dot is light from ONE atom.",
"In 2017, an Oxford physicist trapped a strontium ion between two metal needle tips.",
"A blue violet laser made it glow, while electric fields held it almost still.",
"An ordinary camera caught the light during a thirty second exposure.",
"So you're not seeing the atom's shape. You're seeing the light it emitted."
]
waves=[];metadata=[];t=0.
for i,line in enumerate(lines):
 a,sr=model.create(line,voice="af_heart",speed=.98,lang="en-us",trim=True,continuous=True)
 assert sr==24000
 a=np.asarray(a,dtype=np.float32).reshape(-1)
 duration=len(a)/sr
 gap=.11 if i<len(lines)-1 else .28
 metadata.append(dict(index=i,text=line,start=t,voice_end=t+duration,end=t+duration+gap))
 waves.extend([a,np.zeros(round(sr*gap),dtype=np.float32)])
 t+=duration+gap
 print("SEGMENT",i,"duration",round(duration,3),line,flush=True)
sf.write(D/"Single_Atom_Kokoro_af_heart.wav",np.concatenate(waves),24000,subtype="PCM_24")
(D/"TIMECODES.json").write_text(json.dumps({"total_seconds":t,"segments":metadata},indent=2))
print("TOTAL",t,flush=True)
