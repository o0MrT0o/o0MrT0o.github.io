from pathlib import Path
import requests,hashlib,json,os
from kokoro_onnx import Kokoro
import soundfile as sf
os.environ['ORT_DISABLE_TELEMETRY']='1'
base=Path('voice');base.mkdir(exist_ok=True)
base_url='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
sha={'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for name,expected in sha.items():
 p=base/name
 if not p.exists():
  with requests.get(base_url+name,stream=True,timeout=160) as r:
   print('DOWNLOAD',name,r.status_code,r.headers.get('Content-Length'),flush=True)
   r.raise_for_status()
   with p.open('wb') as f:
    for chunk in r.iter_content(1<<20): f.write(chunk)
 actual=hashlib.sha256(p.read_bytes()).hexdigest()
 print('SHA',name,actual,flush=True)
 assert actual==expected, 'Refusing unapproved model'
script="This spider is dead. But it is lifting another spider. Rice University researchers turned it into a gripper. Normally, fluid pressure opens a spider's legs. The team used air instead. Pressure on: the legs open. Pressure off: they close. It even lifted a spider heavier than itself. Not alive. Still working. Strange, but verified."
print('SCRIPT',script,flush=True)
k=Kokoro(str(base/'kokoro-v1.0.onnx'),str(base/'voices-v1.0.bin'))
samples,rate=k.create(script,voice='af_heart',speed=0.88,lang='en-us',continuous=True,trim=False)
path=base/'SBV_NECROBOTICS_af_heart_088.wav'
sf.write(str(path),samples,rate,subtype='PCM_24')
meta={'script':script,'rate':rate,'duration':len(samples)/rate,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'model':sha,'voice':'af_heart','speed':0.88,'continuous':True,'trim':False}
(base/'narration_qa.json').write_text(json.dumps(meta,indent=2))
print('OUTPUT',meta,flush=True)
