#!/usr/bin/env python3
"""Clean original English voice for Pipa pipa V9 -- NO on-screen captions."""
import numpy as np, soundfile as sf, json
from pathlib import Path
from kokoro_onnx import Kokoro
D=Path('pipa_v9_voice');D.mkdir(exist_ok=True)
m=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
script=[
 "This baby toad is crawling out of its mother's BACK.",
 "Those tiny holes are in her actual skin.",
 "After mating, fertilized eggs are placed on her back.",
 "Her skin grows over them, forming protective pockets.",
 "Months later, fully formed babies emerge and swim away."
]
waves=[];times=[];t=0.
for i,s in enumerate(script):
 sample,sr=m.create(s,voice='af_heart',speed=.94,lang='en-us',trim=True,continuous=True)
 if sr!=24000:raise ValueError(sr)
 a=np.asarray(sample,dtype=np.float32).reshape(-1)
 pause=.12 if i<len(script)-1 else .25
 dur=len(a)/sr
 times.append({'index':i,'text':s,'start':round(t,3),'vo_end':round(t+dur,3),'end':round(t+dur+pause,3),'duration':round(dur,3)})
 waves.extend([a,np.zeros(round(sr*pause),dtype=np.float32)])
 t+=dur+pause
 print('VOICE',i,round(dur,2),s,flush=True)
sf.write(D/'PIPA_V9_Kokoro_af_heart.wav',np.concatenate(waves),24000,subtype='PCM_24')
(D/'TIMECODES.json').write_text(json.dumps({'duration':round(t,3),'segments':times,'voice':'Kokoro af_heart','speed':.94},indent=2))
print('TOTAL',round(t,3),flush=True)
