"""Inline renderers + orbit metadata into site/index.html and copy media."""
import json, os, shutil, glob, sys
here = os.path.dirname(os.path.abspath(__file__))
site = os.path.join(here, 'site')
src = open(os.path.join(here, 'src.html')).read()
meta = json.load(open(os.path.join(here, 'render/orbit/orbit.json')))
for fr in meta['polys']:
    for t in fr.values():
        for k, poly in t.items():
            t[k] = [[round(a, 3), round(b, 3)] for a, b in poly]
fly = sorted(glob.glob(os.path.join(here, 'render/fly/fly_*.jpg')))
panos = [os.path.basename(p)[5:-4] for p in sorted(glob.glob(os.path.join(here, 'render/pano/pano_*.jpg')))]
order = [p for p in ['window', 'living', 'kitchen', 'primary', 'bedroom', 'bath', 'balcony'] if p in panos]
html = (src.replace('/*ASCII*/', open(os.path.join(here, 'fx_ascii.js')).read())
           .replace('/*GEO*/', open(os.path.join(here, 'fx_geo.js')).read())
           .replace('/*LG*/', open(os.path.join(here, 'render.js')).read())
           .replace('/*ORBIT_JSON*/', json.dumps(meta, separators=(',', ':')))
           .replace('/*FLY_N*/', str(int(sys.argv[1]) if len(sys.argv) > 1 else len(fly)))
           .replace('/*PANOS*/', json.dumps(order)))
os.makedirs(site, exist_ok=True)
open(os.path.join(site, 'index.html'), 'w').write(html)
for sub, pat in (('orbit', 'render/orbit/orbit_*.jpg'), ('pano', 'render/pano/pano_*.jpg')):
    d = os.path.join(site, 'media', sub); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(here, pat)):
        dst = os.path.join(d, os.path.basename(f))
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(f):
            shutil.copy2(f, dst)
print('built', len(html) // 1024, 'KB html;', len(fly), 'fly frames;', order)
