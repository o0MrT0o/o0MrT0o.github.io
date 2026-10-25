from pathlib import Path
import requests,hashlib,json,os
from kokoro_onnx import Kokoro
import soundfile as sf
import numpy as np
os.environ['ORT_DISABLE_TELEMETRY']='1'
base=Path('voice_output');base.mkdir(exist_ok=True)
model_dir=base/'models';model_dir.mkdir(exist_ok=True)
models={'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for name,sha in models.items():
 p=model_dir/name
 with requests.get('https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'+name,timeout=200,stream=True) as r:
  print('MODEL',name,r.status_code,flush=True);r.raise_for_status()
  with p.open('wb') as f:
   for ch in r.iter_content(1<<20):f.write(ch)
 print('HASH',name,hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
chapters=[
("THE IMPOSSIBLE SMOKE","This is not smoke. And it isn't a volcano erupting lava. It's water, shooting out of the ocean floor at temperatures that can exceed four hundred degrees Celsius. That should be enough to boil almost any pot of water on Earth. But down here, it doesn't boil. And the strangest part is what scientists found living around it. These are hydrothermal vents, filmed thousands of meters beneath the surface. Their dark plumes look like an underwater fire. But the black clouds are actually tiny particles of metal-rich minerals. To understand why they're here, we need to go beneath the seafloor."),
("THE CHIMNEYS","Far below the ocean, the Earth's crust is cracked open in places. Cold seawater seeps down through those fractures, moves near intensely hot rock, and begins to heat up. Along the way, the water reacts with rock and picks up dissolved metals and other chemicals. It becomes buoyant, rises through the cracks, and bursts back into the freezing deep ocean. The dissolved minerals suddenly cool and solidify. Grain by grain, they build towers: some as tall as buildings. These structures are called black smokers. They aren't made of soot. They're mineral chimneys, formed by the meeting of two very different kinds of water. And some vent fields look less like geological formations, and more like the skyline of another planet."),
("WATER THAT WON'T BOIL","Here's the part that sounds impossible. At the surface, water boils at about one hundred degrees Celsius, assuming ordinary atmospheric pressure. But the deeper you go, the greater the pressure of the water above you. At the depths of many hydrothermal vents, that pressure changes the conditions for boiling. So water can remain liquid at temperatures far above one hundred degrees. Some vents release fluids hotter than four hundred degrees Celsius. What you're seeing is not steam pouring into the sea. The black cloud forms as dissolved minerals react with cold seawater. And the hottest fluid is not where the animals live. Just centimeters away, mixing can drop the temperature dramatically, creating narrow, habitable zones around an extreme source of heat."),
("LIFE WITHOUT SUNLIGHT","Now look closely at the rocks. They move. That isn't the current. Those are animals. Shrimp crowd against the chimneys. Crabs creep between mineral ledges. In some vent systems, tubeworms and other strange organisms gather in dense colonies. Down here, there is no sunlight to grow plants. So what keeps a food web alive? Microbes. Certain bacteria and archaea harvest energy from chemicals released by the vents. A process called chemosynthesis allows them to make organic material without sunlight. Animals eat these microbes, graze on bacterial films, or live in partnership with microbes inside their bodies. The whole community is built around chemistry rising out of the Earth. When scientists discovered hydrothermal vents near the Galápagos in nineteen seventy-seven, they found a kind of ecosystem that forced us to rethink where life could flourish."),
("AN ENTIRE WORLD BELOW","But these ecosystems have a weakness. A chimney may stop flowing. The chemical energy can disappear. And then the animals that depended on it may lose their source of food. New vents can open elsewhere, with new communities growing in the darkness. Think about what that means. At the bottom of our own planet, we've found boiling-hot-looking water that doesn't boil, rocks that build themselves into towers, and life supported by chemical reactions instead of sunlight. No fictional alien planet required. The world we were looking for was here all along. Strange, but verified.")
]
k=Kokoro(str(model_dir/'kokoro-v1.0.onnx'),str(model_dir/'voices-v1.0.bin'))
timeline=[];t=0.
for i,(name,text) in enumerate(chapters):
 samples,rate=k.create(text,voice='af_heart',speed=0.88,lang='en-us',continuous=True,trim=False)
 out=base/f'chapter_{i+1:02d}.wav'
 sf.write(str(out),samples,rate,subtype='PCM_24')
 dur=len(samples)/rate;print('CHAPTER',name,round(dur,2),'words',len(text.split()),flush=True)
 timeline.append({'id':i+1,'name':name,'script':text,'start':round(t,3),'duration':round(dur,3),'file':out.name})
 t+=dur+0.62
(base/'voice_timeline.json').write_text(json.dumps({'chapters':timeline,'pause_between_chapters':0.62,'target_duration':t-0.62,'model_sha256':models,'voice':'af_heart','speed':0.88},indent=2))
print('VOICE_TOTAL_SECONDS',t-0.62,flush=True)
