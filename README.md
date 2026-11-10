# Marlow Point — Pick a floor. Fly inside.

A leasing site for three invented residential towers, modelled on the "London Towers, Erbil" reel (alann.jaf): hover the towers to light up a floor, open its floor plate to see which homes are still available, pick a home, then fly from outside the building, over the balcony and through the open slider into the apartment, and look around it in 360°.

Everything you see is rendered in **Blender Cycles** (no photos, no stock): the towers, the city, the bay and the furnished apartment on Tower B, floor 24.

## Open it

The site loads its renders by relative path, so serve the folder rather than opening `index.html` directly:

```bash
cd site && python3 -m http.server 8000
# then open http://localhost:8000
```

## What's in here

| Path | What it is |
|---|---|
| `site/index.html` | The whole site in one file (ASCII loader, Liquid Glass UI, floor picker, flight player, 360 viewer) |
| `site/media/orbit/` | 36 frames around the towers; the site opens on a still shot and you drag to turn |
| `site/media/video/fly.mp4` | The fly-in, facade to living room (48 Cycles frames, motion-interpolated to 30 fps) |
| `site/media/pano/` | 360° equirectangular panoramas: window, living, kitchen, balcony |
| `scene.py` | The Blender scene: towers, city, sky, apartment, cameras and the render modes |
| `lib.py` | Material and mesh helpers (shared with the Calder Quay room renders) |
| `src.html` + `build.py` | Page source; `build.py` inlines the effects, the GPU renderer and the floor outlines into `site/index.html` |
| `render.js` | One WebGL pass that draws the renders, the 360 view and the Liquid Glass panels together |

## Re-render

Needs `pip install bpy` (Blender 5.x as a Python module).

```bash
python3 scene.py orbit render/orbit --res 1440 810 --samples 24 --frames 36   # also writes orbit.json (floor outlines per frame)
python3 scene.py fly   render/fly   --res 1280 720 --samples 24 --frames 48
python3 scene.py pano  render/pano  --res 2560 1280 --samples 32
python3 build.py
```

`scene.py test` and `scene.py interior` render single preview frames.

## How the floor picking works

For every orbit frame, `scene.py` projects each storey of each tower (slab edge to slab edge) into screen space and stores the outline in `orbit.json`. The page tests the mouse against those outlines, so the highlight lines up with the rendered floor exactly, from any angle.

Marlow Point, its homes and prices are fictional.
