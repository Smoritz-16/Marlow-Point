"""Marlow Point: three residential towers at dusk + one furnished apartment (Tower B, floor 24).

python3 scene.py MODE OUT [--res W H] [--samples S] [--frames N] [--only i,j]
MODE: test | orbit | fly | pano
"""
import bpy, bmesh, math, random, sys, os, json
from mathutils import Vector, Euler, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ARGS = sys.argv[1:]
MODE, OUT = (ARGS + ['test', 'out'])[:2]
def arg(name, n=1, default=None):
    if name in ARGS:
        i = ARGS.index(name); v = ARGS[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default
RES = [int(x) for x in arg('--res', 2, ['1280', '720'])]
SAMPLES = int(arg('--samples', default=48))
FRAMES = int(arg('--frames', default=36))
ONLY = [int(x) for x in arg('--only', default='').split(',') if x != '']
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
import lib
from lib import node_mat, setin, hexc, tex_coord, bump, ramp, wood, stone, emissive, box, cyl, sphere, soft, MATS
scene = bpy.context.scene
rnd = random.Random(11)

# ------------------------------------------------------------------ render settings
scene.render.engine = 'CYCLES'
cy = scene.cycles
cy.device = 'CPU'
cy.samples = SAMPLES
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.025
cy.use_denoising = True
try: cy.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
try: cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
except Exception: pass
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3
cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
cy.blur_glossy = 1.0; cy.sample_clamp_indirect = 8.0
try: cy.use_light_tree = True
except Exception: pass
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 90
scene.view_settings.view_transform = 'AgX'
try: scene.view_settings.look = 'AgX - High Contrast'
except Exception: pass
scene.render.film_transparent = False
scene.view_settings.exposure = -0.25

# ------------------------------------------------------------------ constants
FH = 3.2                 # floor-to-floor
PODIUM = 6.4             # floors 1-2 are a double-height lobby
W, D, R = 30.0, 20.0, 7.0  # tower glass footprint
BAL = 1.8                # balcony depth
TOWERS = {'A': dict(c=(-50.0, 16.0), floors=32), 'B': dict(c=(0.0, 0.0), floors=38), 'C': dict(c=(50.0, 10.0), floors=35)}
TARGET = ('B', 24)
def zbase(n):
    return PODIUM + (n - 3) * FH
ZT = zbase(TARGET[1])            # slab bottom of the target floor
ZF = ZT + 0.32                   # finished floor
EYE = ZF + 1.6

# ------------------------------------------------------------------ materials
def mixshader(nt, a, b, fac=None):
    m = nt.nodes.new('ShaderNodeMixShader')
    if fac is None: m.inputs[0].default_value = 0.5
    elif isinstance(fac, float): m.inputs[0].default_value = fac
    else: nt.links.new(fac, m.inputs[0])
    nt.links.new(a, m.inputs[1]); nt.links.new(b, m.inputs[2])
    return m

def math_node(nt, op, a, b=None, v2=None):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op
    if isinstance(a, (int, float)): n.inputs[0].default_value = a
    else: nt.links.new(a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): n.inputs[1].default_value = b
        else: nt.links.new(b, n.inputs[1])
    return n.outputs[0]

def haze(nt, shader_out, out_node, color='#9fb0c4', dist=900.0, strength=1.0):
    """Cheap aerial perspective: mix toward a haze emission by camera distance."""
    cam = nt.nodes.new('ShaderNodeCameraData')
    f = math_node(nt, 'DIVIDE', cam.outputs['View Distance'], dist)
    f = math_node(nt, 'MULTIPLY', f, -1.0)
    f = math_node(nt, 'EXPONENT', f)
    f = math_node(nt, 'SUBTRACT', 1.0, f)
    f = math_node(nt, 'MULTIPLY', f, 0.85)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = hexc(color); em.inputs['Strength'].default_value = strength
    m = mixshader(nt, shader_out, em.outputs[0], f)
    nt.links.new(m.outputs[0], out_node.inputs[0])

def plain(name, color, rough=0.5, metal=0.0, coat=0.0, sheen=0.0, nb=0.0, nbs=60.0, sss=0.0):
    m, nt, bsdf, _ = node_mat(name)
    setin(bsdf, 'Base Color', hexc(color)); setin(bsdf, 'Roughness', rough); setin(bsdf, 'Metallic', metal)
    if coat: setin(bsdf, 'Coat Weight', coat); setin(bsdf, 'Coat Roughness', 0.1)
    if sheen: setin(bsdf, 'Sheen Weight', sheen); setin(bsdf, 'Sheen Roughness', 0.5)
    if sss: setin(bsdf, 'Subsurface Weight', sss)
    if nb:
        n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = nbs; n.inputs['Detail'].default_value = 8
        nt.links.new(tex_coord(nt), n.inputs['Vector']); bump(nt, bsdf, n.outputs['Fac'], nb, 0.004)
    MATS[name] = m
    return m

def facade_glass(name='facade'):
    """Glazing of floors we never enter: real reflections over a faked room behind the glass."""
    m, nt, bsdf, out = node_mat(name); nt.nodes.remove(bsdf)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    snap = nt.nodes.new('ShaderNodeVectorMath'); snap.operation = 'SNAP'
    snap.inputs[1].default_value = (3.2, 3.2, FH)
    nt.links.new(geo.outputs['Position'], snap.inputs[0])
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '4D'
    nt.links.new(snap.outputs[0], wn.inputs['Vector']); nt.links.new(oi.outputs['Random'], wn.inputs['W'])
    lit = math_node(nt, 'GREATER_THAN', wn.outputs['Value'], 0.86)
    # height inside the floor (0 at slab, 1 at ceiling): rooms read brighter near the ceiling
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    zf = math_node(nt, 'DIVIDE', sep.outputs['Z'], FH); zf = math_node(nt, 'FRACT', zf)
    grad = math_node(nt, 'POWER', zf, 1.6); grad = math_node(nt, 'MULTIPLY_ADD', grad, 0.0) if False else grad
    g2 = math_node(nt, 'MULTIPLY', grad, 3.5); g2 = math_node(nt, 'ADD', g2, 0.6)
    warm = ramp(nt, wn.outputs['Color'], [(0.0, hexc('#ffb36b')), (0.6, hexc('#ffd29a')), (1.0, hexc('#fff0dc'))])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(warm.outputs['Color'], em.inputs['Color'])
    st = math_node(nt, 'MULTIPLY', g2, lit); st = math_node(nt, 'MULTIPLY', st, 0.55)
    nt.links.new(st, em.inputs['Strength'])
    dark = nt.nodes.new('ShaderNodeBsdfDiffuse')
    ceil = math_node(nt, 'GREATER_THAN', zf, 0.86)
    curt = math_node(nt, 'GREATER_THAN', math_node(nt, 'FRACT', math_node(nt, 'MULTIPLY', wn.outputs['Value'], 7.3)), 0.88)
    c1 = nt.nodes.new('ShaderNodeMix'); c1.data_type = 'RGBA'
    nt.links.new(curt, c1.inputs['Factor']); c1.inputs['A'].default_value = hexc('#161b21'); c1.inputs['B'].default_value = hexc('#6b655c')
    c2 = nt.nodes.new('ShaderNodeMix'); c2.data_type = 'RGBA'
    nt.links.new(ceil, c2.inputs['Factor']); nt.links.new(c1.outputs['Result'], c2.inputs['A']); c2.inputs['B'].default_value = hexc('#5a5650')
    nt.links.new(c2.outputs['Result'], dark.inputs['Color'])
    room = mixshader(nt, dark.outputs[0], em.outputs[0], 0.5)
    addsh = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(dark.outputs[0], addsh.inputs[0]); nt.links.new(em.outputs[0], addsh.inputs[1])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Color'].default_value = hexc('#a9c2d3'); gl.inputs['Roughness'].default_value = 0.01
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.42
    fac = math_node(nt, 'ADD', lw.outputs['Fresnel'], 0.12); fac = math_node(nt, 'MINIMUM', fac, 0.95)
    mx = mixshader(nt, addsh.outputs[0], gl.outputs[0], fac)
    nt.links.new(mx.outputs[0], out.inputs[0])
    MATS[name] = m

def rail_glass(name='railglass'):
    m, nt, bsdf, out = node_mat(name); nt.nodes.remove(bsdf)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = hexc('#d6e6e2')
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.02; gl.inputs['Color'].default_value = hexc('#cfe0dc')
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    f = math_node(nt, 'ADD', lw.outputs['Fresnel'], 0.06)
    mx = mixshader(nt, tr.outputs[0], gl.outputs[0], f); nt.links.new(mx.outputs[0], out.inputs[0])
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    MATS[name] = m

def clear_glass(name='glass'):
    """Real window glass for the apartment we fly into: see-through, fresnel reflections, casts light."""
    m, nt, bsdf, out = node_mat(name); nt.nodes.remove(bsdf)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (0.9, 0.94, 0.95, 1)
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.0; gl.inputs['Color'].default_value = (0.9, 0.95, 0.97, 1)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.22
    f = math_node(nt, 'ADD', lw.outputs['Fresnel'], 0.03)
    mx = mixshader(nt, tr.outputs[0], gl.outputs[0], f); nt.links.new(mx.outputs[0], out.inputs[0])
    MATS[name] = m

def city_mat(name='city'):
    m, nt, bsdf, out = node_mat(name)
    geo = nt.nodes.new('ShaderNodeNewGeometry'); oi = nt.nodes.new('ShaderNodeObjectInfo')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    # facade colour per building (vertex colour carries a per-building random)
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_name = 'bid'
    base = ramp(nt, attr.outputs['Fac'], [(0.0, hexc('#4a4845')), (0.25, hexc('#7d766c')), (0.5, hexc('#5c636b')), (0.75, hexc('#9b9284')), (1.0, hexc('#3a3e43'))])
    roofn = nt.nodes.new('ShaderNodeTexNoise'); roofn.inputs['Scale'].default_value = 0.6; nt.links.new(geo.outputs['Position'], roofn.inputs['Vector'])
    roofc = ramp(nt, roofn.outputs['Fac'], [(0.3, hexc('#3b3d3f')), (0.7, hexc('#6a6862'))])
    rmix = nt.nodes.new('ShaderNodeMix'); rmix.data_type = 'RGBA'
    nzs = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], nzs.inputs[0])
    nt.links.new(math_node(nt, 'GREATER_THAN', nzs.outputs['Z'], 0.5), rmix.inputs['Factor'])
    nt.links.new(base.outputs['Color'], rmix.inputs['A']); nt.links.new(roofc.outputs['Color'], rmix.inputs['B'])
    nt.links.new(rmix.outputs['Result'], bsdf.inputs['Base Color']); setin(bsdf, 'Roughness', 0.7)
    # window grid in world space: 3.4m bays, 3.3m floors
    snap = nt.nodes.new('ShaderNodeVectorMath'); snap.operation = 'SNAP'; snap.inputs[1].default_value = (3.4, 3.4, 3.3)
    nt.links.new(geo.outputs['Position'], snap.inputs[0])
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '4D'
    nt.links.new(snap.outputs[0], wn.inputs['Vector']); nt.links.new(attr.outputs['Fac'], wn.inputs['W'])
    def frac_mask(sock, period, lo, hi):
        f = math_node(nt, 'DIVIDE', sock, period); f = math_node(nt, 'FRACT', f)
        a = math_node(nt, 'GREATER_THAN', f, lo); b = math_node(nt, 'LESS_THAN', f, hi)
        return math_node(nt, 'MULTIPLY', a, b)
    wx = frac_mask(math_node(nt, 'ADD', sep.outputs['X'], sep.outputs['Y']), 3.4, 0.08, 0.92)
    wz = frac_mask(sep.outputs['Z'], 3.3, 0.18, 0.9)
    nz = math_node(nt, 'ABSOLUTE', geo.outputs['Normal']) if False else None
    nsep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], nsep.inputs[0])
    side = math_node(nt, 'LESS_THAN', math_node(nt, 'ABSOLUTE', nsep.outputs['Z']), 0.5)
    win = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', wx, wz), side)
    lit = math_node(nt, 'GREATER_THAN', wn.outputs['Value'], 0.8)
    warm = ramp(nt, wn.outputs['Color'], [(0.0, hexc('#ff9d4d')), (0.5, hexc('#ffcf8f')), (1.0, hexc('#dfe9ff'))])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(warm.outputs['Color'], em.inputs['Color'])
    nt.links.new(math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', win, lit), 0.9), em.inputs['Strength'])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.12; gl.inputs['Color'].default_value = hexc('#6d7884')
    winsh = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(gl.outputs[0], winsh.inputs[0]); nt.links.new(em.outputs[0], winsh.inputs[1])
    mx = mixshader(nt, bsdf.outputs[0], winsh.outputs[0], win)
    haze(nt, mx.outputs[0], out, '#b9c7d6', 520.0, 0.9)
    MATS[name] = m

def ground_mat(name='ground'):
    m, nt, bsdf, out = node_mat(name)
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    setin(bsdf, 'Base Color', hexc('#2b2d2f')); setin(bsdf, 'Roughness', 0.85)
    # street lights: warm lines on a 60m grid
    def line(sock):
        f = math_node(nt, 'DIVIDE', math_node(nt, 'ADD', sock, 30.0), 60.0); f = math_node(nt, 'FRACT', f)
        f = math_node(nt, 'SUBTRACT', f, 0.5); f = math_node(nt, 'ABSOLUTE', f)
        return math_node(nt, 'LESS_THAN', f, 0.025)
    ln = math_node(nt, 'MAXIMUM', line(sep.outputs['X']), line(sep.outputs['Y']))
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = hexc('#ffb064')
    nt.links.new(math_node(nt, 'MULTIPLY', ln, 0.5), em.inputs['Strength'])
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(bsdf.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
    haze(nt, ad.outputs[0], out, '#b9c7d6', 520.0, 0.9)
    MATS[name] = m

def water_mat(name='water'):
    m, nt, bsdf, out = node_mat(name)
    setin(bsdf, 'Base Color', hexc('#0b1820')); setin(bsdf, 'Roughness', 0.04); setin(bsdf, 'IOR', 1.33)
    n = nt.nodes.new('ShaderNodeTexWave'); n.inputs['Scale'].default_value = 0.08; n.inputs['Distortion'].default_value = 6; n.inputs['Detail'].default_value = 6
    nt.links.new(tex_coord(nt, (1, 3, 1)), n.inputs['Vector']); bump(nt, bsdf, n.outputs['Fac'], 0.25, 0.3)
    haze(nt, bsdf.outputs[0], out, '#b9c7d6', 2200.0, 0.9)
    MATS[name] = m

def leaf_mat(name, color):
    m, nt, bsdf, out = node_mat(name)
    setin(bsdf, 'Base Color', hexc(color)); setin(bsdf, 'Roughness', 0.45)
    setin(bsdf, 'Subsurface Weight', 0.25)
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); nt.links.new(geo.outputs['Position'], wn.inputs['Vector'])
    r = ramp(nt, wn.outputs['Value'], [(0.0, hexc('#2f4a22')), (0.5, hexc(color)), (1.0, hexc('#6f8a45'))])
    nt.links.new(r.outputs['Color'], bsdf.inputs['Base Color'])
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); tl.inputs['Color'].default_value = hexc('#7a9a3a')
    mx = mixshader(nt, bsdf.outputs[0], tl.outputs[0], 0.25); nt.links.new(mx.outputs[0], out.inputs[0])
    MATS[name] = m

def build_materials():
    plain('slab', '#e9e5dc', 0.45, nb=0.03, nbs=40)
    plain('alu', '#3a3d40', 0.32, metal=1.0)
    plain('alu_light', '#b8b9b6', 0.28, metal=1.0)
    plain('podium', '#d8d2c6', 0.55)
    facade_glass(); rail_glass(); clear_glass(); city_mat(); ground_mat(); water_mat()
    wood('oak_floor', '#c19a6b', '#8d6844', along='x', rough=0.38, planks=True)
    wood('oak', '#b98c5c', '#7d5634', along='z', rough=0.42)
    wood('oak_h', '#b98c5c', '#7d5634', along='x', rough=0.42)
    wood('walnut', '#6b4a32', '#3e2a1c', along='x', rough=0.4)
    stone('marble', '#efece6', '#8f8a84', scale=1.4, vein_width=0.03, rough=0.14)
    stone('travertine', '#d9cdb7', '#b7a487', travertine=True)
    plain('plaster', '#e8e2d8', 0.85, nb=0.02, nbs=90)
    plain('ceiling', '#f1ede6', 0.9)
    plain('boucle', '#e7e0d4', 0.95, sheen=0.6, nb=0.25, nbs=380)
    plain('linen', '#cfc5b5', 0.9, sheen=0.4, nb=0.12, nbs=250)
    plain('taupe', '#8d7d6c', 0.85, sheen=0.4, nb=0.12, nbs=250)
    plain('leather', '#6a4430', 0.45, coat=0.1, nb=0.05, nbs=120)
    plain('black', '#141414', 0.35)
    plain('black_matte', '#1b1b1b', 0.7)
    plain('brass', '#b08a52', 0.25, metal=1.0)
    plain('ceramic', '#e9e4dc', 0.25, coat=0.3)
    plain('stoneware', '#9a8f80', 0.7, nb=0.2, nbs=60)
    plain('rug', '#cbbfae', 1.0, sheen=0.5, nb=0.35, nbs=200)
    plain('soil', '#2b2219', 1.0)
    plain('bark', '#5a4634', 0.8, nb=0.4, nbs=30)
    plain('screen', '#060606', 0.08, coat=0.8)
    plain('book1', '#a7553a', 0.7); plain('book2', '#3b4a5c', 0.7); plain('book3', '#d8cfbf', 0.7)
    leaf_mat('leaf', '#46642c')
    m, nt, bsdf, out = node_mat('sheer'); nt.nodes.remove(bsdf)
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); tl.inputs['Color'].default_value = hexc('#fbf6ee')
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = hexc('#f0e9dd')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    a = mixshader(nt, df.outputs[0], tl.outputs[0], 0.6); b = mixshader(nt, a.outputs[0], tr.outputs[0], 0.3)
    nt.links.new(b.outputs[0], out.inputs[0]); MATS['sheer'] = m
    emissive('led', '#ffc98a', 9.0)
    emissive('led_soft', '#ffcf96', 4.0)
    emissive('bulb', '#ffcf9a', 25.0)
    emissive('corridor', '#ffd7a8', 1.2)
    m, nt, bsdf, out = node_mat('shade_glass')
    setin(bsdf, 'Base Color', hexc('#f2e2c6')); setin(bsdf, 'Transmission Weight', 1.0); setin(bsdf, 'Roughness', 0.35)
    MATS['shade_glass'] = m

# ------------------------------------------------------------------ geometry helpers
def rrect(w, d, r, seg=10):
    pts = []
    cs = [(w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)]
    for cx, cy, a0 in cs:
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def mesh_obj(name, bm, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for mt in mats: me.materials.append(MATS[mt])
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    return ob

def add_prism(bm, pts, z0, z1, mi=0, cap=True, side=True):
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    n = len(pts)
    if side:
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((bot[i], bot[j], top[j], top[i])); f.material_index = mi; f.smooth = True
    if cap:
        f = bm.faces.new(top); f.material_index = mi
        f = bm.faces.new(list(reversed(bot))); f.material_index = mi

def add_ribbon(bm, pts, z0, z1, mi, skip=None):
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        (x0, y0), (x1, y1) = pts[i], pts[j]
        if skip and skip((x0 + x1) / 2, (y0 + y1) / 2):
            continue
        vs = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1))]
        f = bm.faces.new(vs); f.material_index = mi; f.smooth = True

def add_box(bm, cx, cy, cz, sx, sy, sz, mi, rz=0.0):
    c, s = math.cos(rz), math.sin(rz)
    vs = []
    for dz in (-0.5, 0.5):
        for dx, dy in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
            x, y = dx * sx, dy * sy
            vs.append(bm.verts.new((cx + x * c - y * s, cy + x * s + y * c, cz + dz * sz)))
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        fc = bm.faces.new([vs[i] for i in f]); fc.material_index = mi

def resample(pts, step):
    """Points every `step` metres along a closed outline, with the outward normal angle."""
    segs = []
    n = len(pts)
    for i in range(n):
        a, b = Vector((*pts[i], 0)), Vector((*pts[(i + 1) % n], 0))
        segs.append((a, b, (b - a).length))
    total = sum(s[2] for s in segs)
    out, t, k, acc = [], 0.0, 0, 0.0
    cnt = int(total / step)
    for i in range(cnt):
        d = i * total / cnt
        while acc + segs[k][2] < d:
            acc += segs[k][2]; k += 1
        a, b, L = segs[k]
        p = a + (b - a) * ((d - acc) / L)
        tdir = (b - a).normalized()
        out.append((p.x, p.y, math.atan2(tdir.y, tdir.x)))
    return out

# ------------------------------------------------------------------ the tower floor module
GLASS = rrect(W, D, R)
SLAB = rrect(W + 2 * BAL, D + 2 * BAL, R + BAL)
RAIL = rrect(W + 2 * BAL - 0.12, D + 2 * BAL - 0.12, R + BAL - 0.06)

def floor_module(name, skip=None, crown=False):
    """One storey (local z 0..FH): slab with rounded balcony edge, glass wall, fins, glass rail."""
    bm = bmesh.new()
    add_prism(bm, SLAB, 0.0, 0.32, 0)                        # slab (white)
    add_ribbon(bm, GLASS, 0.32, FH, 1, skip)                  # facade glass
    for x, y, a in resample(GLASS, 1.6):                      # mullions
        if skip and skip(x, y):
            continue
        add_box(bm, x, y, 0.32 + (FH - 0.32) / 2, 0.06, 0.16, FH - 0.32, 2, a)
    add_ribbon(bm, RAIL, 0.32, 1.37, 3)                       # glass balustrade
    for x, y, a in resample(RAIL, 1.5):                       # rail posts
        add_box(bm, x, y, 0.32 + 0.53, 0.03, 0.03, 1.05, 2, a)
    rail_top = rrect(W + 2 * BAL - 0.1, D + 2 * BAL - 0.1, R + BAL - 0.05, 10)
    inner = rrect(W + 2 * BAL - 0.16, D + 2 * BAL - 0.16, R + BAL - 0.08, 10)
    add_ribbon(bm, rail_top, 1.36, 1.41, 2); add_ribbon(bm, inner, 1.36, 1.41, 2)
    ob = mesh_obj(name, bm, ['slab', 'facade', 'alu', 'railglass'])
    md = ob.modifiers.new('bev', 'BEVEL'); md.width = 0.06; md.segments = 3; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(40)
    return ob

def build_towers():
    mod = floor_module('floor_mod')
    mod.hide_render = True
    for key, t in TOWERS.items():
        cx, cy = t['c']; top = t['floors']
        # podium / lobby: double-height glass with a stone band
        bm = bmesh.new()
        add_prism(bm, rrect(W + 8, D + 8, R + 4), -0.5, 0.6, 0)
        add_ribbon(bm, rrect(W - 1, D - 1, R - 0.5), 0.6, PODIUM, 1)
        add_prism(bm, SLAB, PODIUM - 0.01, PODIUM, 0, side=False)
        lob = mesh_obj(f'podium_{key}', bm, ['podium', 'facade'])
        lob.location = (cx, cy, 0)
        for n in range(3, top + 1):
            if (key, n) == TARGET:
                continue
            ob = bpy.data.objects.new(f'{key}_{n:02d}', mod.data)
            for md in mod.modifiers:
                pass
            scene.collection.objects.link(ob)
            ob.location = (cx, cy, zbase(n))
            bev = ob.modifiers.new('bev', 'BEVEL'); bev.width = 0.06; bev.segments = 3; bev.limit_method = 'ANGLE'; bev.angle_limit = math.radians(40)
        # roof: slab, parapet and a set-back plant screen
        zr = zbase(top + 1)
        bm = bmesh.new()
        add_prism(bm, SLAB, 0.0, 0.45, 0)
        add_prism(bm, rrect(W - 6, D - 6, R - 3), 0.45, 4.2, 1)
        add_ribbon(bm, RAIL, 0.45, 1.5, 2)
        roof = mesh_obj(f'roof_{key}', bm, ['slab', 'alu_light', 'railglass'])
        roof.location = (cx, cy, zr)

def build_target_floor():
    """Tower B floor 24: same storey, but the south apartment is real - clear glass and an open slider."""
    cx, cy = TOWERS['B']['c']
    front = lambda x, y: (y < -D / 2 + 0.2 and abs(x) < 8.0)
    ob = floor_module('target_floor', skip=front)
    ob.location = (cx, cy, ZT)
    # real glazing: floor-to-ceiling panes, 2.0m modules, the middle two slid open
    bm = bmesh.new()
    y = cy - D / 2
    xs = [-8.0 + 2.0 * i for i in range(9)]
    for i in range(8):
        x0, x1 = xs[i], xs[i + 1]
        if i in (3, 4):
            continue                                        # the open slider
        add_box(bm, (x0 + x1) / 2, y, ZF + (FH - 0.32) / 2, x1 - x0 - 0.02, 0.02, FH - 0.32, 0)
    # the slid panels stacked behind their neighbours
    add_box(bm, -3.0, y + 0.09, ZF + (FH - 0.32) / 2, 1.98, 0.02, FH - 0.32, 0)
    add_box(bm, 3.0, y + 0.09, ZF + (FH - 0.32) / 2, 1.98, 0.02, FH - 0.32, 0)
    for x in xs:
        if abs(x) < 0.1:
            continue                                        # no mullion in the open slider
        add_box(bm, x, y, ZF + (FH - 0.32) / 2, 0.07, 0.12, FH - 0.32, 1)
    add_box(bm, 0, y, ZF + 0.02, 16.0, 0.14, 0.04, 1)      # sill track
    add_box(bm, 0, y, ZT + FH - 0.04, 16.0, 0.14, 0.08, 1)  # head
    mesh_obj('target_glass', bm, ['glass', 'alu'])

# ------------------------------------------------------------------ city, water, sky
def build_city():
    bm = bmesh.new()
    bid = bm.verts.layers.float.new('bidv')
    rn = random.Random(5)
    blocks = []
    for gx in range(-16, 17):
        for gy in range(-7, 22):
            x0, y0 = gx * 60.0 - 30 + 6, gy * 60.0 - 30 + 6
            cxb, cyb = x0 + 24, y0 + 24
            if abs(cxb) < 110 and abs(cyb - 8) < 60:
                continue                                    # the tower site / park
            if cyb < -420:
                continue                                    # the bay
            blocks.append((x0, y0))
    for x0, y0 in blocks:
        dist = math.hypot(x0 + 24, y0 + 24)
        # downtown gets taller toward the north-east
        tall = 1.0 + max(0.0, 1.0 - math.hypot(x0 - 500, y0 - 1050) / 500.0) * 4.0
        nsub = rn.choice([1, 2, 2, 3, 4])
        for k in range(nsub):
            sx = rn.uniform(14, 46) if nsub <= 2 else rn.uniform(12, 22)
            sy = rn.uniform(14, 46) if nsub <= 2 else rn.uniform(12, 22)
            px = x0 + rn.uniform(sx / 2, 48 - sx / 2); py = y0 + rn.uniform(sy / 2, 48 - sy / 2)
            h = rn.choice([9, 12, 15, 18, 22, 28, 34]) * rn.uniform(0.8, 1.3) * tall
            if rn.random() < 0.04:
                h *= rn.uniform(2.0, 4.0)
            dsite = math.hypot(px, py - 8)
            if dsite < 320:
                h = min(h, 8 + dsite * 0.07)            # low-rise around the park so the towers read
            if py < 0 and abs(px) < 260:
                h = min(h, 14.0)                        # keep the camera's foreground low
            v0 = len(bm.verts)
            add_box(bm, px, py, h / 2, sx, sy, h, 0)
            for _ in range(rn.choice([0, 1, 2, 3])):                 # rooftop plant and stair boxes
                bx_, by_ = rn.uniform(2.5, sx / 2.6), rn.uniform(2.5, sy / 2.6); bh = rn.uniform(1.5, 3.5)
                add_box(bm, px + rn.uniform(-sx / 4, sx / 4), py + rn.uniform(-sy / 4, sy / 4), h + bh / 2, bx_, by_, bh, 0)
            add_box(bm, px, py, h + 0.5, sx + 0.3, sy + 0.3, 1.0, 0) if rn.random() < 0.5 else None
            b = rn.random()
            bm.verts.ensure_lookup_table()
            for v in bm.verts[v0:]:
                v[bid] = b
    ob = mesh_obj('city', bm, ['city'])
    # move the float layer into a colour attribute the shader can read
    me = ob.data
    src = me.attributes.get('bidv')
    at = me.attributes.new('bid', 'FLOAT', 'POINT')
    vals = [0.0] * len(me.vertices); src.data.foreach_get('value', vals); at.data.foreach_set('value', vals)
    # ground and water
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    for v in bm.verts:
        v.co.x *= 2400; v.co.y = (v.co.y + 1) / 2 * 3400 - 450; v.co.z = -0.02
    g = mesh_obj('ground', bm, ['ground'])
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    for v in bm.verts:
        v.co.x *= 9000; v.co.y = (v.co.y - 1) / 2 * 9000 - 440; v.co.z = -1.2
    mesh_obj('water', bm, ['water'])
    # a seawall edge
    box('seawall', 0, -446, -1.2, 4800, 12, 1.2, 'podium', bevel=0)
    # park around the towers: lawn + trees as clustered spheres
    plain('lawn', '#3d4a2c', 0.9)
    plain('paving', '#9b968c', 0.75)
    box('plaza', 0, 8, -0.02, 210, 110, 0.04, 'paving', bevel=0)
    for i in range(60):
        x = rn.uniform(-100, 100); y = rn.uniform(-42, 58)
        if any(abs(x - t['c'][0]) < 22 and abs(y - t['c'][1]) < 17 for t in TOWERS.values()):
            continue
        r = rn.uniform(2.2, 3.6)
        cyl(f'trunk{i}', x, y, 0, 0.18, 0.18, 2.4, 'bark', verts=8)
        for j in range(3):
            sphere(f'tree{i}_{j}', x + rn.uniform(-1, 1), y + rn.uniform(-1, 1), 2.4 + r + rn.uniform(-0.5, 0.8), r, r, r * 0.85, 'leaf')

def build_sky(elev=9.0, rot=212.0, strength=0.5):
    w = bpy.data.worlds.new('sky'); scene.world = w
    nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(elev); sky.sun_rotation = math.radians(rot)
    sky.altitude = 300.0; sky.air_density = 1.3; sky.aerosol_density = 0.5; sky.sun_intensity = 0.45
    bg.inputs['Strength'].default_value = strength
    nt.links.new(sky.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 2.0; sun.angle = math.radians(0.8); sun.color = (1.0, 0.8, 0.62)
    so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so)
    # sun_rotation is measured from +Y toward +X? Blender: rotation about Z, 0 = sun at +X... aim the lamp from the sky's sun
    d = Vector((math.cos(math.radians(elev)) * math.sin(math.radians(rot)), math.cos(math.radians(elev)) * math.cos(math.radians(rot)), math.sin(math.radians(elev))))
    so.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return sky

# ------------------------------------------------------------------ the apartment (Tower B, floor 24, south)
def spot(name, x, y, z, energy=14.0, size=95.0, color=(1.0, 0.86, 0.72), radius=0.04, rot=(0, 0, 0)):
    L = bpy.data.lights.new(name, 'SPOT'); L.energy = energy; L.spot_size = math.radians(size); L.spot_blend = 0.75
    L.color = color; L.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, L); scene.collection.objects.link(ob); ob.location = (x, y, z); ob.rotation_euler = rot
    return ob

def area(name, x, y, z, sx, sy, energy, color=(1.0, 0.8, 0.6), rot=(0, 0, 0)):
    L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size = sx; L.size_y = sy; L.energy = energy; L.color = color
    ob = bpy.data.objects.new(name, L); scene.collection.objects.link(ob); ob.location = (x, y, z); ob.rotation_euler = rot
    return ob

def plant(cx, cy, z0, h=2.2, spread=0.75, n=420, pot='stoneware', seed=1):
    rn = random.Random(seed)
    cyl('pot', cx, cy, z0, 0.32, 0.32, 0.55, pot, verts=40, bevel=0.01)
    cyl('soil', cx, cy, z0 + 0.5, 0.29, 0.29, 0.04, 'soil', verts=40)
    bm = bmesh.new()
    # trunk + branches
    stems = []
    for k in range(3):
        a = rn.uniform(0, 2 * math.pi); lean = rn.uniform(0.05, 0.18)
        top = Vector((cx + math.cos(a) * lean * h * 0.4, cy + math.sin(a) * lean * h * 0.4, z0 + h * rn.uniform(0.85, 1.0)))
        stems.append((Vector((cx, cy, z0 + 0.5)), top))
    for b, t in stems:
        steps = 10
        for i in range(steps):
            p0 = b.lerp(t, i / steps); p1 = b.lerp(t, (i + 1) / steps)
            mid = (p0 + p1) / 2; d = p1 - p0
            rr = 0.025 * (1 - i / steps) + 0.008
            q = d.to_track_quat('Z', 'Y')
            mat = Matrix.Translation(mid) @ q.to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=rr, radius2=rr * 0.9, depth=d.length, matrix=mat)
    trunk = mesh_obj('trunk', bm, ['bark'])
    # leaves: olive-ish elongated blades clustered around the upper stems
    bm = bmesh.new()
    for i in range(n):
        b, t = rn.choice(stems)
        f = rn.uniform(0.35, 1.0)
        c = b.lerp(t, f)
        rad = spread * (0.35 + 0.65 * math.sin(f * math.pi)) * rn.uniform(0.2, 1.0)
        a = rn.uniform(0, 2 * math.pi)
        p = c + Vector((math.cos(a) * rad, math.sin(a) * rad, rn.uniform(-0.15, 0.15)))
        L = rn.uniform(0.09, 0.15); Wd = L * 0.32
        e = Euler((rn.uniform(-1.2, 1.2), rn.uniform(-0.6, 0.6), rn.uniform(0, 6.28)))
        M = e.to_matrix()
        pts = [Vector((0, 0, 0)), Vector((Wd / 2, L * 0.45, 0.01)), Vector((0, L, 0.0)), Vector((-Wd / 2, L * 0.45, 0.01))]
        vs = [bm.verts.new(p + M @ q) for q in pts]
        fc = bm.faces.new(vs); fc.smooth = True
    leaves = mesh_obj('leaves', bm, ['leaf'])
    return leaves

def stool(x, y):
    cyl('stool_seat', x, y, 0.72 + ZF, 0.19, 0.19, 0.06, 'leather', verts=32, bevel=0.015)
    cyl('stool_post', x, y, ZF + 0.05, 0.025, 0.025, 0.68, 'brass', verts=12)
    cyl('stool_base', x, y, ZF, 0.21, 0.21, 0.03, 'brass', verts=32)
    cyl('stool_ring', x, y, ZF + 0.28, 0.17, 0.17, 0.015, 'brass', verts=32)

def pendant(x, y, drop=0.95, r=0.11):
    zc = ZT + FH
    cyl('cord', x, y, zc - drop, 0.004, 0.004, drop, 'black', verts=6)
    m = cyl('shade', x, y, zc - drop - 0.22, r, r, 0.24, 'black', verts=40, bevel=0.0)
    cyl('shade_in', x, y, zc - drop - 0.215, r * 0.9, r * 0.9, 0.2, 'led_soft', verts=32)
    sphere('bulb', x, y, zc - drop - 0.13, 0.05, 0.05, 0.05, 'bulb')
    L = bpy.data.lights.new('pend', 'POINT'); L.energy = 18; L.shadow_soft_size = 0.05; L.color = (1, 0.74, 0.48)
    ob = bpy.data.objects.new('pendL', L); scene.collection.objects.link(ob); ob.location = (x, y, zc - drop - 0.26)

def chair(x, y, rz):
    c, s = math.cos(rz), math.sin(rz)
    def loc(dx, dy): return x + dx * c - dy * s, y + dx * s + dy * c
    sx, sy = loc(0, 0)
    soft('chair_seat', sx, sy, ZF + 0.44, 0.48, 0.48, 0.08, 'linen', r=0.03, rz=rz)
    bx, by = loc(0, -0.22)
    soft('chair_back', bx, by, ZF + 0.5, 0.46, 0.06, 0.38, 'linen', r=0.025, rz=rz)
    for dx, dy in ((-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)):
        lx, ly = loc(dx, dy)
        cyl('chair_leg', lx, ly, ZF, 0.016, 0.016, 0.44, 'walnut', verts=10)

def build_apartment():
    cx, cy = TOWERS['B']['c']
    yF, yB, xL, xR = cy - D / 2, cy - 1.0, -8.0, 8.0
    zc = ZT + FH                     # ceiling height (underside of floor 25 slab)
    H = zc - ZF
    # floor, ceiling, walls
    box('oak_floor', 0, (yF + yB) / 2, ZF - 0.02, 16.0, yB - yF, 0.02, 'oak_floor', bevel=0)
    box('ceiling', 0, (yF + yB) / 2 + 0.6, zc - 0.02, 16.0, yB - yF - 1.2, 0.02, 'ceiling', bevel=0)
    # window-head bulkhead with a hidden LED cove washing the curtains
    box('bulkhead', 0, yF + 0.6, zc - 0.22, 16.0, 1.2, 0.22, 'ceiling', bevel=0.004)
    box('cove', 0, yF + 1.22, zc - 0.235, 15.8, 0.04, 0.012, 'led', bevel=0)
    box('wall_back', 0, yB + 0.1, ZF, 16.2, 0.2, H, 'plaster', bevel=0)
    box('wall_L', xL - 0.1, (yF + yB) / 2, ZF, 0.2, yB - yF, H, 'plaster', bevel=0)
    box('wall_R', xR + 0.1, (yF + yB) / 2, ZF, 0.2, yB - yF, H, 'plaster', bevel=0)
    # skirting shadow gap
    box('skirt_b', 0, yB - 0.005, ZF, 16.0, 0.01, 0.06, 'black_matte', bevel=0)

    # ---- left wall: fluted oak with a recessed fire and floating walnut console
    x = xL + 0.02
    for i in range(int((yB - yF - 1.0) / 0.075)):
        yy = yF + 0.9 + i * 0.075
        box('slat', x + 0.03, yy, ZF, 0.05, 0.045, H - 0.22, 'oak', bevel=0.006)
    box('slat_back', x + 0.005, (yF + yB) / 2 + 0.45, ZF, 0.01, yB - yF - 0.9, H, 'black_matte', bevel=0)
    box('console', xL + 0.3, -5.5, ZF + 0.32, 0.45, 3.2, 0.42, 'walnut', bevel=0.01)
    box('tv', xL + 0.11, -5.5, ZF + 1.1, 0.04, 1.75, 0.99, 'screen', bevel=0.004)
    box('console_led', xL + 0.53, -5.5, ZF + 0.3, 0.02, 3.1, 0.01, 'led_soft', bevel=0)
    # ---- living: deep sofa, chaise, lounge chair, coffee table, rug
    box('rug', -4.7, -6.0, ZF, 4.0, 3.2, 0.012, 'rug', bevel=0.004)
    sx = -2.6
    soft('sofa_base', sx, -6.0, ZF + 0.12, 1.0, 3.2, 0.32, 'boucle', r=0.08)
    soft('sofa_back', sx + 0.38, -6.0, ZF + 0.12, 0.26, 3.2, 0.72, 'boucle', r=0.1)
    soft('sofa_armL', sx, -7.52, ZF + 0.12, 1.0, 0.24, 0.55, 'boucle', r=0.1)
    soft('sofa_armR', sx, -4.48, ZF + 0.12, 1.0, 0.24, 0.55, 'boucle', r=0.1)
    for k, yy in enumerate((-6.8, -5.95, -5.1)):
        soft(f'cush{k}', sx - 0.05, yy, ZF + 0.44, 0.72, 0.82, 0.14, 'boucle', r=0.06)
        soft(f'bcush{k}', sx + 0.24, yy, ZF + 0.5, 0.22, 0.78, 0.46, 'boucle', r=0.09)
    soft('pillow1', sx + 0.08, -7.1, ZF + 0.58, 0.16, 0.46, 0.42, 'taupe', r=0.08, rz=0.15)
    soft('pillow2', sx + 0.08, -4.85, ZF + 0.58, 0.16, 0.46, 0.42, 'linen', r=0.08, rz=-0.1)
    box('sofa_plinth', sx, -6.0, ZF, 0.9, 3.0, 0.12, 'black_matte', bevel=0.004)
    soft('coffee', -4.6, -6.0, ZF, 1.3, 0.9, 0.36, 'travertine', r=0.05)
    cyl('bowl', -4.8, -6.15, ZF + 0.36, 0.17, 0.17, 0.07, 'stoneware', verts=40)
    box('book_a', -4.3, -5.8, ZF + 0.36, 0.28, 0.22, 0.04, 'book3', bevel=0.003, rz=0.2)
    box('book_b', -4.3, -5.8, ZF + 0.40, 0.25, 0.2, 0.035, 'book1', bevel=0.003, rz=0.25)
    # lounge chair by the window
    soft('lounge', -5.5, -8.5, ZF + 0.1, 0.85, 0.85, 0.32, 'leather', r=0.12, rz=0.5)
    soft('lounge_back', -5.75, -8.25, ZF + 0.3, 0.8, 0.25, 0.5, 'leather', r=0.11, rz=0.5)
    cyl('lounge_base', -5.5, -8.5, ZF, 0.3, 0.3, 0.1, 'walnut', verts=32)
    # floor lamp
    cyl('lamp_base', -7.2, -7.6, ZF, 0.16, 0.16, 0.02, 'brass', verts=32)
    cyl('lamp_pole', -7.2, -7.6, ZF, 0.012, 0.012, 1.55, 'brass', verts=10)
    cyl('lamp_shade', -7.2, -7.6, ZF + 1.45, 0.24, 0.24, 0.32, 'shade_glass', verts=40)
    L = bpy.data.lights.new('lampL', 'POINT'); L.energy = 22; L.shadow_soft_size = 0.12; L.color = (1, 0.72, 0.45)
    o = bpy.data.objects.new('lampL', L); scene.collection.objects.link(o); o.location = (-7.2, -7.6, ZF + 1.58)
    plant(-7.0, -9.1, ZF, h=2.3, seed=3)
    plant(7.1, -1.9, ZF, h=1.9, n=320, pot='ceramic', seed=8)

    # ---- kitchen on the back wall: tall oak bank + base run with marble splash, LED shelf
    kb = yB - 0.3
    box('tall_cab', 4.05, kb, ZF, 3.1, 0.62, 2.62, 'oak', bevel=0.004)
    for i in range(5):
        box('tall_gap', 2.5 + i * 0.62, kb - 0.312, ZF + 0.02, 0.006, 0.004, 2.58, 'black_matte', bevel=0)
    box('base_cab', -0.75, kb, ZF + 0.1, 5.0, 0.62, 0.8, 'oak_h', bevel=0.004)
    box('toe', -0.75, kb + 0.04, ZF, 5.0, 0.56, 0.1, 'black_matte', bevel=0)
    box('counter', -0.75, kb - 0.01, ZF + 0.9, 5.04, 0.66, 0.04, 'marble', bevel=0.004)
    box('splash', -0.75, yB - 0.01, ZF + 0.94, 5.0, 0.02, 0.62, 'marble', bevel=0)
    box('shelf', -0.75, yB - 0.13, ZF + 1.58, 5.0, 0.26, 0.05, 'oak_h', bevel=0.004)
    box('shelf_led', -0.75, yB - 0.2, ZF + 1.575, 4.9, 0.02, 0.006, 'led', bevel=0)
    box('upper', -0.75, yB - 0.18, ZF + 1.96, 5.0, 0.36, 0.7, 'oak_h', bevel=0.004)
    box('upper_led', -0.75, yB - 0.3, ZF + 1.955, 4.9, 0.02, 0.006, 'led', bevel=0)
    box('hob', 0.6, kb - 0.04, ZF + 0.94, 0.75, 0.5, 0.006, 'screen', bevel=0)
    box('sink', -2.0, kb - 0.02, ZF + 0.935, 0.7, 0.42, 0.01, 'black', bevel=0)
    cyl('tap', -2.0, yB - 0.12, ZF + 0.94, 0.015, 0.015, 0.34, 'brass', verts=12)
    box('tap_spout', -2.0, yB - 0.22, ZF + 1.26, 0.03, 0.22, 0.03, 'brass', bevel=0.01)
    for i, (px, h) in enumerate(((-2.9, 0.22), (-2.65, 0.3), (1.6, 0.18))):
        cyl(f'jar{i}', px, yB - 0.15, ZF + 1.63, 0.06, 0.06, h, 'ceramic', verts=24)
    # island with waterfall marble
    iy = yB - 2.75
    box('island', 0.5, iy, ZF, 3.6, 1.05, 0.9, 'oak_h', bevel=0.004)
    box('island_top', 0.5, iy, ZF + 0.9, 3.7, 1.1, 0.05, 'marble', bevel=0.006)
    box('island_wfL', -1.32, iy, ZF, 0.05, 1.1, 0.9, 'marble', bevel=0.004)
    box('island_wfR', 2.32, iy, ZF, 0.05, 1.1, 0.9, 'marble', bevel=0.004)
    for sxp in (-0.5, 0.5, 1.5):
        stool(sxp, iy - 0.82)
    cyl('fruit_bowl', 1.4, iy + 0.1, ZF + 0.95, 0.18, 0.18, 0.06, 'stoneware', verts=40)
    for k in range(4):
        sphere(f'lemon{k}', 1.4 + math.cos(k * 1.7) * 0.07, iy + 0.1 + math.sin(k * 1.7) * 0.07, ZF + 1.04, 0.04, 0.04, 0.037, 'brass' if k == 9 else 'book3')
    for px in (-0.4, 0.5, 1.4):
        pendant(px, iy, drop=0.95)
    # dining by the right wall
    dy = -6.6
    box('dtable', 5.0, dy, ZF + 0.72, 2.4, 1.0, 0.05, 'walnut', bevel=0.006)
    box('dleg1', 5.0, dy, ZF, 0.12, 0.6, 0.72, 'walnut', bevel=0.01)
    box('dleg2', 4.2, dy, ZF, 0.12, 0.6, 0.72, 'walnut', bevel=0.01)
    box('dleg3', 5.8, dy, ZF, 0.12, 0.6, 0.72, 'walnut', bevel=0.01)
    for k, cxp in enumerate((4.25, 5.0, 5.75)):
        chair(cxp, dy - 0.75, 0.0)
        chair(cxp, dy + 0.75, math.pi)
    cyl('vase', 5.0, dy, ZF + 0.77, 0.08, 0.08, 0.3, 'stoneware', verts=32)
    pendant(5.0, dy, drop=1.15, r=0.22)
    # right wall: art and a low credenza
    box('credenza', xR - 0.25, -3.6, ZF + 0.18, 0.45, 2.0, 0.55, 'walnut', bevel=0.008)
    box('art_frame', xR - 0.03, -6.6, ZF + 1.15, 0.04, 1.8, 1.2, 'oak', bevel=0.004)
    plain('art', '#c7b39a', 0.9, nb=0.2, nbs=8)
    box('art_canvas', xR - 0.055, -6.6, ZF + 1.2, 0.01, 1.7, 1.1, 'art', bevel=0)
    # back wall left: doorway to a lit hall + bedroom door
    box('door_open', -6.0, yB + 0.05, ZF, 1.1, 0.25, 2.4, 'corridor', bevel=0)
    box('door_frame', -6.0, yB - 0.02, ZF + 2.4, 1.2, 0.06, 0.04, 'oak', bevel=0)
    # sheers bunched at each end of the glass
    for xs_, w_ in ((-7.55, 0.8), (7.55, 0.8)):
        bm = bmesh.new()
        n = 24
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            x0 = xs_ - w_ / 2 + w_ * t0; x1 = xs_ - w_ / 2 + w_ * t1
            y0 = yF + 0.35 + 0.07 * math.sin(t0 * math.pi * 10); y1 = yF + 0.35 + 0.07 * math.sin(t1 * math.pi * 10)
            vs = [bm.verts.new(p) for p in ((x0, y0, ZF + 0.01), (x1, y1, ZF + 0.01), (x1, y1, zc - 0.25), (x0, y0, zc - 0.25))]
            f = bm.faces.new(vs); f.smooth = True
        mesh_obj('sheer', bm, ['sheer'])
    # ---- lights: recessed 2700K downlights + window cove + kitchen strip lights
    for x_, y_ in [(-5.5, -4.5), (-5.5, -7.5), (-3.0, -4.5), (-3.0, -7.5), (5.0, -4.0), (6.5, -8.0), (3.5, -8.0), (-6.5, -2.4), (2.0, -1.6), (4.0, -1.6), (-1.0, -1.6), (-3.0, -1.6)]:
        cyl('can', x_, y_, zc - 0.03, 0.045, 0.045, 0.02, 'led', verts=24)
        spot('dl', x_, y_, zc - 0.05, energy=11, size=70)
    area('sky_fill', 0, yF + 0.4, ZF + 1.4, 15.5, 2.6, 30, color=(0.75, 0.82, 1.0), rot=(math.radians(-90), 0, 0))

# ------------------------------------------------------------------ cameras
def camera(name, loc, look, lens=24.0):
    c = bpy.data.cameras.new(name); c.lens = lens; c.clip_start = 0.05; c.clip_end = 12000
    ob = bpy.data.objects.new(name, c); scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = ob
    return ob

def look_at(ob, loc, look, roll=0.0):
    ob.location = loc
    q = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y')
    ob.rotation_euler = q.to_euler()
    if roll:
        ob.rotation_euler.rotate_axis('Z', roll)

def orbit_pose(t, n):
    """t in 0..n-1: a gentle arc around the three towers, like a drone holding position."""
    u = (t / (n - 1)) * 2 - 1                    # -1..1
    ang = math.radians(-90 + 26 * u)
    rad = 235.0
    loc = (math.cos(ang) * rad, 8 + math.sin(ang) * rad, 52.0)
    look = (0.0, 8.0, 68.0)
    return loc, look

def project(cam, p):
    from bpy_extras.object_utils import world_to_camera_view
    v = world_to_camera_view(scene, cam, Vector(p))
    return (round(v.x, 4), round(1 - v.y, 4))

def hull(points):
    pts = sorted(set(points))
    if len(pts) < 3: return pts
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def floor_polys(cam):
    """Screen-space outline of every floor of every tower (slab edge to slab edge)."""
    out = {}
    ring = rrect(W + 2 * BAL, D + 2 * BAL, R + BAL, 4)
    for key, t in TOWERS.items():
        cx, cy = t['c']; fl = {}
        for n in range(3, t['floors'] + 1):
            z0, z1 = zbase(n), zbase(n) + FH
            pts = [project(cam, (cx + x, cy + y, z)) for x, y in ring for z in (z0, z1)]
            fl[n] = [[round(a, 4), round(b, 4)] for a, b in hull(pts)]
        out[key] = fl
    return out

def render_to(path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

# ------------------------------------------------------------------ build + run
build_materials()
build_sky()
build_towers()
build_target_floor()
build_city()
if MODE in ('fly', 'pano', 'test', 'interior'):
    build_apartment()
if True:
    try:
        scene.view_settings.use_white_balance = True
        scene.view_settings.white_balance_temperature = 4700
    except Exception as e:
        print('no wb', e)
cam = camera('cam', (0, -250, 40), (0, 0, 60), lens=35)

if MODE == 'test':
    loc, look = orbit_pose(FRAMES // 2, FRAMES); look_at(cam, loc, look); cam.data.lens = 38
    render_to(os.path.join(OUT, 'test_ext.jpg'))
elif MODE == 'interior':
    cam.data.lens = 18
    look_at(cam, (0.5, -9.0, EYE), (-1.5, -2.0, EYE - 0.2))
    render_to(os.path.join(OUT, 'test_int.jpg'))
    look_at(cam, (3.0, -2.5, EYE), (-1.0, -10.0, EYE - 0.3))
    render_to(os.path.join(OUT, 'test_int2.jpg'))
elif MODE == 'orbit':
    cam.data.lens = 38
    meta = {'frames': FRAMES, 'res': RES, 'floors': {k: t['floors'] for k, t in TOWERS.items()}, 'polys': []}
    for i in range(FRAMES):
        loc, look = orbit_pose(i, FRAMES); look_at(cam, loc, look)
        bpy.context.view_layer.update()
        meta['polys'].append(floor_polys(cam))
        if (not ONLY or i in ONLY) and '--meta-only' not in ARGS:
            render_to(os.path.join(OUT, f'orbit_{i:03d}.jpg'))
    with open(os.path.join(OUT, 'orbit.json'), 'w') as f:
        json.dump(meta, f, separators=(',', ':'))
elif MODE == 'fly':
    # facade close-up -> over the balustrade -> through the open slider -> settle in the living room
    keys = [
        (0.00, (0.0, -78.0, EYE + 3.0), (0.0, -10.0, EYE - 0.6), 30),
        (0.45, (0.0, -24.0, EYE + 0.5), (0.0, -6.0, EYE - 0.2), 26),
        (0.72, (0.0, -10.8, EYE), (0.0, -2.0, EYE - 0.1), 22),
        (1.00, (0.6, -6.8, EYE), (-0.6, -1.0, EYE - 0.25), 20),
    ]
    def interp(t):
        t = 0.5 - 0.5 * math.cos(math.pi * t)       # ease in-out
        for (t0, l0, k0, f0), (t1, l1, k1, f1) in zip(keys, keys[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0); u = u * u * (3 - 2 * u)
                L = Vector(l0).lerp(Vector(l1), u); K = Vector(k0).lerp(Vector(k1), u)
                return L, K, f0 + (f1 - f0) * u
        return Vector(keys[-1][1]), Vector(keys[-1][2]), keys[-1][3]
    for i in range(FRAMES):
        if ONLY and i not in ONLY: continue
        L, K, f = interp(i / (FRAMES - 1))
        look_at(cam, L, K); cam.data.lens = f
        render_to(os.path.join(OUT, f'fly_{i:03d}.jpg'))
elif MODE == 'pano':
    cam.data.type = 'PANO'
    try: cam.data.panorama_type = 'EQUIRECTANGULAR'
    except Exception: cam.data.cycles.panorama_type = 'EQUIRECTANGULAR'
    spots = {'living': (0.6, -6.8, EYE), 'kitchen': (3.4, -3.2, EYE), 'window': (-1.2, -9.0, EYE), 'balcony': (2.6, -11.0, EYE)}
    want = arg('--rooms', default='living,kitchen,window,balcony').split(',')
    for name in want:
        loc = spots[name]
        cam.location = loc
        cam.rotation_euler = (math.radians(90), 0, 0)   # centre of the pano looks +Y (into the flat)
        render_to(os.path.join(OUT, f'pano_{name}.jpg'))
print('DONE', MODE)
