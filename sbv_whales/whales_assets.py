from pathlib import Path
import os,requests,hashlib,json,subprocess,re
from kokoro_onnx import Kokoro
import soundfile as sf
os.environ['ORT_DISABLE_TELEMETRY']='1'
out=Path('whale_recovered');out.mkdir(exist_ok=True)
log=[]
def say(*a):
 s=' '.join(str(x) for x in a);log.append(s);print(s,flush=True)
script="These whales build fishing nets out of air. They swim in circles, blowing rings of bubbles that herd krill together. Then they surge upward, mouths wide open. Researchers estimate these nets can concentrate prey about sevenfold. No rope. No hooks. Just a fishing net that vanishes after dinner."
voice=out/'voice';voice.mkdir(exist_ok=True)
base_url='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
checksums={'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for name,expected in checksums.items():
 dest=voice/name
 if not dest.exists():
  with requests.get(base_url+name,timeout=120,stream=True) as r:
   say('MODEL',name,r.status_code,r.headers.get('Content-Length'));r.raise_for_status()
   with dest.open('wb') as f:
    for b in r.iter_content(1<<20): f.write(b)
 actual=hashlib.sha256(dest.read_bytes()).hexdigest()
 say('SHA',name,actual);assert actual==expected
k=Kokoro(str(voice/'kokoro-v1.0.onnx'),str(voice/'voices-v1.0.bin'))
samples,rate=k.create(script,voice='af_heart',speed=0.88,lang='en-us',continuous=True,trim=False)
sf.write(str(out/'SBV_WHALES_af_heart_088.wav'),samples,rate,subtype='PCM_24')
say('VOICE_DURATION',len(samples)/rate)
(out/'voice_meta.json').write_text(json.dumps({'script':script,'duration':len(samples)/rate,'sample_rate':rate,'voice':'af_heart','speed':0.88,'sha256':hashlib.sha256((out/'SBV_WHALES_af_heart_088.wav').read_bytes()).hexdigest()},indent=2))
# Follow original 2019 University of Hawaii press video link
try:
 r=requests.get('https://bit.ly/337g8oa',timeout=18,allow_redirects=True,stream=True)
 say('2019_ORIGINAL_LINK',r.status_code,r.url,r.headers.get('Content-Type'),r.headers.get('Content-Length'))
 (out/'2019_source_url.txt').write_text(r.url)
except Exception as e:say('2019_LINK_ERROR',repr(e))
try:
 cmd=['yt-dlp','--no-playlist','-f','best[height<=1080]/best','-o',str(out/'UH2019_%(id)s.%(ext)s'),'https://www.youtube.com/watch?v=JNhldKgPRg0']
 p=subprocess.run(cmd,timeout=110,capture_output=True,text=True)
 say('YT_DLP',p.returncode,p.stdout[-800:],p.stderr[-1300:])
except Exception as e:say('YOUTUBE_ERROR',repr(e))
for f in out.iterdir():
 if f.suffix.lower() in ['.mp4','.mov','.webm']:
  p=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height,codec_name:format=duration','-of','json',str(f)],capture_output=True,text=True)
  say('FOOTAGE',f.name,f.stat().st_size,p.stdout[:700])
(out/'diagnostics.txt').write_text('\n'.join(log))
