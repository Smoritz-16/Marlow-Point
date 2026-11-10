import bpy, bmesh, math, random
from mathutils import Vector
MATS = {}
# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf, out

def setin(bsdf, key, val):
    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = val

def hexc(h, a=1.0):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)

def tex_coord(nt, scale=(1, 1, 1)):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs['Vector']

def bump(nt, bsdf, height_socket, strength=0.1, distance=0.02):
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    if 'Distance' in b.inputs:
        b.inputs['Distance'].default_value = distance
    nt.links.new(height_socket, b.inputs['Height'])
    nt.links.new(b.outputs['Normal'], bsdf.inputs['Normal'])

def ramp(nt, fac_socket, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], stops[0][1]
    els[1].position, els[1].color = stops[-1][0], stops[-1][1]
    for pos, col in stops[1:-1]:
        e = els.new(pos)
        e.color = col
    nt.links.new(fac_socket, r.inputs['Fac'])
    return r

MATS = {}
def wood(name, light, dark, along='x', rough=0.42, planks=False):
    """Oak/walnut: fine straight grain running along one axis, with gentle figure; optional planks."""
    m, nt, bsdf, _ = node_mat(name)
    stretch = {'x': (0.08, 1.0, 1.0), 'y': (1.0, 0.08, 1.0), 'z': (1.0, 1.0, 0.08)}[along]
    across = {'x': 'Y', 'y': 'X', 'z': 'X'}[along]
    vec = tex_coord(nt, stretch)
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    try:
        wave.bands_direction = across
    except Exception:
        pass
    wave.inputs['Scale'].default_value = 9.0
    wave.inputs['Distortion'].default_value = 2.2
    wave.inputs['Detail'].default_value = 3.0
    wave.inputs['Detail Scale'].default_value = 0.6
    nt.links.new(vec, wave.inputs['Vector'])
    col = ramp(nt, wave.outputs['Fac'], [(0.0, hexc(dark)), (0.35, hexc(light)), (1.0, hexc(light))])
    # large soft tone variation so boards don't look printed
    fig = nt.nodes.new('ShaderNodeTexNoise')
    fig.inputs['Scale'].default_value = 1.2
    nt.links.new(tex_coord(nt, stretch), fig.inputs['Vector'])
    tone = nt.nodes.new('ShaderNodeMix'); tone.data_type = 'RGBA'; tone.blend_type = 'MULTIPLY'
    tone.inputs['Factor'].default_value = 0.25
    nt.links.new(col.outputs['Color'], tone.inputs['A'])
    nt.links.new(fig.outputs['Color'], tone.inputs['B'])
    color_out = tone.outputs['Result']
    if planks:
        br = nt.nodes.new('ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Mortar Size'].default_value = 0.003
        br.inputs['Brick Width'].default_value = 2.2
        br.inputs['Row Height'].default_value = 0.22
        br.inputs['Color1'].default_value = (1, 1, 1, 1)
        br.inputs['Color2'].default_value = (0.85, 0.83, 0.8, 1)
        br.inputs['Mortar'].default_value = (0.4, 0.34, 0.28, 1)
        br.offset = 0.37
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(color_out, mix.inputs['A'])
        nt.links.new(br.outputs['Color'], mix.inputs['B'])
        color_out = mix.outputs['Result']
        bump(nt, bsdf, br.outputs['Fac'], 0.25, 0.002)
    nt.links.new(color_out, bsdf.inputs['Base Color'])
    setin(bsdf, 'Roughness', rough)
    if planks:
        setin(bsdf, 'Coat Weight', 0.2)
        setin(bsdf, 'Coat Roughness', 0.3)
    MATS[name] = m
    return m

def stone(name, base, vein, scale=1.6, vein_width=0.035, rough=0.18, travertine=False):
    """Marble (thin veins) or travertine (soft horizontal banding)."""
    m, nt, bsdf, _ = node_mat(name)
    if travertine:
        vec = tex_coord(nt, (0.6, 0.6, 9.0))
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = 2.5
        n.inputs['Detail'].default_value = 10
        n.inputs['Roughness'].default_value = 0.65
        nt.links.new(vec, n.inputs['Vector'])
        col = ramp(nt, n.outputs['Fac'], [(0.3, hexc(vein)), (0.6, hexc(base)), (1.0, hexc(base))])
        nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
        pits = nt.nodes.new('ShaderNodeTexNoise')
        pits.inputs['Scale'].default_value = 90
        nt.links.new(vec, pits.inputs['Vector'])
        bump(nt, bsdf, pits.outputs['Fac'], 0.15, 0.002)
        setin(bsdf, 'Roughness', 0.55)
    else:
        vec = tex_coord(nt, (scale, scale, scale))
        cloud = nt.nodes.new('ShaderNodeTexNoise')
        cloud.inputs['Scale'].default_value = 0.8
        cloud.inputs['Detail'].default_value = 4
        nt.links.new(vec, cloud.inputs['Vector'])
        base_col = ramp(nt, cloud.outputs['Fac'], [(0.3, hexc('#e6e2db')), (0.7, hexc(base))])
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = 0.55
        n.inputs['Detail'].default_value = 10
        n.inputs['Roughness'].default_value = 0.6
        n.inputs['Distortion'].default_value = 1.4
        nt.links.new(vec, n.inputs['Vector'])
        veins = ramp(nt, n.outputs['Fac'], [(0.0, (1, 1, 1, 1)), (0.5 - vein_width, (1, 1, 1, 1)), (0.5, hexc(vein)), (0.5 + vein_width, (1, 1, 1, 1)), (1.0, (1, 1, 1, 1))])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 0.6
        nt.links.new(base_col.outputs['Color'], mix.inputs['A'])
        nt.links.new(veins.outputs['Color'], mix.inputs['B'])
        nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
        setin(bsdf, 'Roughness', rough)
        setin(bsdf, 'Coat Weight', 0.3)
        setin(bsdf, 'Coat Roughness', 0.05)
    MATS[name] = m
    return m

def emissive(name, color, strength):
    m, nt, bsdf, out = node_mat(name)
    nt.nodes.remove(bsdf)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = hexc(color)
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    MATS[name] = m
    return m

def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj

def box(name, cx, cy, z0, sx, sy, sz, mat, bevel=0.006, seg=2, smooth=False, rz=0.0):
    """Box by its footprint centre (cx, cy), bottom height z0 and size."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.scale = (sx, sy, sz)
    ob.location = (cx, cy, z0 + sz / 2)
    ob.rotation_euler = (0, 0, rz)
    ob.data.materials.append(MATS[mat])
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = seg
        md.limit_method = 'NONE'
        md.use_clamp_overlap = True
        # bevel works in object space; compensate the non-uniform scale by applying it
    apply_scale(ob)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob

def apply_scale(ob):
    me = ob.data
    s = ob.scale.copy()
    for v in me.vertices:
        v.co.x *= s.x; v.co.y *= s.y; v.co.z *= s.z
    ob.scale = (1, 1, 1)

def cyl(name, cx, cy, z0, rx, ry, h, mat, verts=48, bevel=0.0, seg=2, smooth=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=1.0, radius2=1.0, depth=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.scale = (rx, ry, h)
    ob.location = (cx, cy, z0 + h / 2)
    apply_scale(ob)
    ob.data.materials.append(MATS[mat])
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = seg
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(50)
        md.harden_normals = False
    return ob

def sphere(name, cx, cy, cz, rx, ry, rz, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.scale = (rx, ry, rz)
    ob.location = (cx, cy, cz)
    apply_scale(ob)
    ob.data.materials.append(MATS[mat])
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob

def soft(name, cx, cy, z0, sx, sy, sz, mat, r=0.06, rz=0.0):
    """Upholstery: a box with a big rounded bevel and smooth shading."""
    return box(name, cx, cy, z0, sx, sy, sz, mat, bevel=r, seg=5, smooth=True, rz=rz)

