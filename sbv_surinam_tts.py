#!/usr/bin/env python3
from pathlib import Path
import json,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
D=Path('surinam_tts');D.mkdir(exist_ok=True)
model=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
lines=[
"Those are baby toads crawling OUT of their mother's BACK.",
"This is the Surinam toad. She carries fertilized eggs in tiny pockets in her skin.",
"Months later, fully formed babies push their way out, and swim away.",
"No, this isn't a horror movie. It's real."
]
total=[];segments=[];t=0
for i,line in enumerate(lines):
 samples,sr=model.create(line,voice='af_heart',speed=.88,lang='en-us',trim=True,continuous=True)
 assert sr==24000
 wave=np.asarray(samples,dtype=np.float32).reshape(-1)
 assert len(wave)>5000
 d=len(wave)/sr
 gap=.11
 segments.append(dict(text=line,index=i,start=t,vo_end=t+d,end=t+d+gap))
 total.extend([wave,np.zeros(int(gap*sr),dtype=np.float32)])
 t+=d+gap
 print("VOICE_SEGMENT",i,round(d,3),line,flush=True)
voice=np.concatenate(total)
sf.write(D/'surinam_af_heart.wav',voice,24000,subtype='PCM_24')
(D/'voice_timestamps.json').write_text(json.dumps(dict(duration=t,voice='af_heart',speed=.88,segments=segments),indent=2))
print("TOTAL",t,flush=True)
