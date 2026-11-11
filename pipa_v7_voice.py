#!/usr/bin/env python3
"""Short, clear, accurate Surinam toad voice for mobile viewer comprehension."""
import json
from pathlib import Path
import numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
D=Path('pipa_v7_voice');D.mkdir(exist_ok=True)
k=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
script=[
"Wait. Those are baby toads coming out of their mother's BACK.",
"That's her actual skin. Not a nest.",
"Fertilized eggs sink into her back and her skin grows over them.",
"Each baby develops in its own pocket for months.",
"Then tiny, fully formed toads push out, ready to swim."
]
a=[];times=[];t=0.
for i,s in enumerate(script):
 x,sr=k.create(s,voice='af_heart',speed=.94,lang='en-us',trim=True,continuous=True)
 assert sr==24000
 x=np.asarray(x,dtype=np.float32).reshape(-1)
 d=len(x)/sr
 gap=.12 if i<len(script)-1 else .28
 times.append({'index':i,'text':s,'start':t,'vo_end':t+d,'end':t+d+gap,'duration':d})
 a.extend([x,np.zeros(round(gap*sr),dtype=np.float32)])
 t+=d+gap
 print('SEGMENT',i,round(d,3),s,flush=True)
sf.write(D/'PIPA_V7_af_heart.wav',np.concatenate(a),24000,subtype='PCM_24')
(D/'TIMECODES.json').write_text(json.dumps({'duration':t,'voice':'Kokoro af_heart','speed':.94,'segments':times},indent=2))
print('TOTAL',round(t,3),flush=True)
