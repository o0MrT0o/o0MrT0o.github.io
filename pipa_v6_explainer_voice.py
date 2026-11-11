#!/usr/bin/env python3
from pathlib import Path
import json,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
D=Path('pipa_v6_explainer_audio'); D.mkdir(exist_ok=True)
model=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
lines=[
"That is a BABY TOAD coming out of its mother's back.",
"Here is the mother. You're looking at her back.",
"She carries fertilized eggs here, inside her skin.",
"Each egg develops inside its own tiny pocket.",
"Three to four months later, tiny toads push out, fully formed.",
"And swim away."
]
parts=[];times=[];t=0.0
for i,line in enumerate(lines):
 samples,sr=model.create(line,voice='af_heart',speed=.92,lang='en-us',trim=True,continuous=True)
 assert sr==24000
 wav=np.asarray(samples,dtype='float32').reshape(-1)
 gap=.105
 d=len(wav)/sr
 times.append({"index":i,"text":line,"start":t,"vo_end":t+d,"end":t+d+gap,"duration":d})
 parts.extend([wav,np.zeros(round(gap*sr),dtype=np.float32)])
 t+=d+gap
 print("VOICE",i,round(d,3),line,flush=True)
sf.write(D/'PIPA_V6_Kokoro_af_heart.wav',np.concatenate(parts),24000,subtype='PCM_24')
(D/'TIMECODES.json').write_text(json.dumps({"duration":t,"lines":times,"voice":"af_heart","speed":.92},indent=2))
print("FINAL_VOICE_DURATION",t,flush=True)
