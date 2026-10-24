from pathlib import Path
import requests,hashlib,json,os
from kokoro_onnx import Kokoro
import soundfile as sf
os.environ['ORT_DISABLE_TELEMETRY']='1'
folder=Path('voice_v2');folder.mkdir(exist_ok=True)
expected={'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
base='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
for name,sha in expected.items():
 target=folder/name
 with requests.get(base+name,timeout=150,stream=True) as r:
  print('GET',name,r.status_code,flush=True);r.raise_for_status()
  with target.open('wb') as f:
   for b in r.iter_content(1<<20):f.write(b)
 actual=hashlib.sha256(target.read_bytes()).hexdigest()
 print('SHA',name,actual,flush=True);assert actual==sha
script="These whales make fishing nets out of air. They blow circles of bubbles, trapping their prey. Then they lunge through the net to feed. Scientists estimate that, for solo humpbacks, the nets could mean seven times more prey per gulp. And they can adjust the size of each net. They build a hunting tool from breath — then let it disappear."
k=Kokoro(str(folder/'kokoro-v1.0.onnx'),str(folder/'voices-v1.0.bin'))
samples,rate=k.create(script,voice='af_heart',speed=0.88,lang='en-us',continuous=True,trim=False)
sf.write(str(folder/'SBV_WHALES_V2_KOKORO.wav'),samples,rate,subtype='PCM_24')
(folder/'narration.json').write_text(json.dumps({'script':script,'duration':len(samples)/rate,'sample_rate':rate,'voice':'af_heart','speed':0.88},indent=2))
print('DURATION',len(samples)/rate,flush=True)
