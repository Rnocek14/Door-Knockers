"""Bronze Artistry cinematic master scene.
Run: blender -b --python tools/build_forge_scene.py -- /absolute/path/to/bronze_bull_knocker_compressed.glb
Creates a Blender scene and a 180-frame master animation. Requires Blender 4.1+.
This is art-directed geometry and lighting, not a physically simulated fluid pour.
"""
import bpy, math, sys, os, random
from mathutils import Vector
random.seed(14)
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if not argv or not os.path.isfile(argv[0]):
    raise SystemExit("Supply the local .glb path after --; no model was imported.")
model_path=os.path.abspath(argv[0])
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=64
scene.render.resolution_x=1440; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.frame_start=1; scene.frame_end=180; scene.render.fps=30
scene.world.color=(.008,.006,.004)
def material(name, color, metallic=0, roughness=.35, emission=None, strength=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metallic;bs.inputs['Roughness'].default_value=roughness
    if emission:
        bs.inputs['Emission Color'].default_value=(*emission,1)
        bs.inputs['Emission Strength'].default_value=strength
    return m
molten=material('01 - luminous liquid bronze',(.65,.17,.012),.78,.14,(1,.19,.015),4.5)
raw=material('02 - cast bronze',(.26,.11,.038),.88,.34)
finished=material('03 - finished bronze',(.42,.23,.10),.94,.22)
black=material('black foundry',(.012,.010,.009),.35,.55)
bpy.ops.import_scene.gltf(filepath=model_path)
imported=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not imported:raise RuntimeError('GLB contains no mesh objects')
root=bpy.data.objects.new('BULL - animated master',None);scene.collection.objects.link(root)
for o in imported:
    if o.parent is None:o.parent=root
# Center and normalize geometry using world-space bounding box before scaling.
bpy.context.view_layer.update()
coords=[o.matrix_world @ Vector(corner) for o in imported for corner in o.bound_box]
minimum=Vector((min(v[i] for v in coords) for i in range(3)))
maximum=Vector((max(v[i] for v in coords) for i in range(3)))
center=(minimum+maximum)/2
extent=max((maximum-minimum))
if extent<=0:raise RuntimeError('Model has invalid bounding dimensions')
for o in imported:
    if o.parent==root:o.location-=center
root.scale=(3.4/extent,)*3
# Duplicate source meshes for a warm raw-cast version and a refined final version.
for o in imported:
    if o.type=='MESH':
        o.data=o.data.copy()
        o.data.materials.clear();o.data.materials.append(finished)
root.rotation_euler=(0,0,-.1)
# Real model is kept intact; the liquid flow is a separate deliberately art-directed effect.
curve=bpy.data.curves.new('Molten stream spline','CURVE');curve.dimensions='3D';curve.resolution_u=48;curve.bevel_depth=.18;curve.bevel_resolution=5
spline=curve.splines.new('BEZIER');spline.bezier_points.add(5)
points=[(-1.3,3.8,.25),(-1.2,2.6,.22),(-.8,1.5,.17),(-.3,.55,.1),(.1,-.5,.15),(.5,-1.8,.25)]
for bp,xyz in zip(spline.bezier_points,points):
    bp.co=xyz;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
flow=bpy.data.objects.new('MOLTEN BRONZE - directed stream',curve);scene.collection.objects.link(flow)
flow.data.materials.append(molten)
for frame,amount in [(1,0.001),(18,.18),(50,1),(76,1),(108,.001),(180,.001)]:
    curve.bevel_factor_end=amount;curve.keyframe_insert('bevel_factor_end',frame=frame)
# Falling droplets (individually timed, no simulation).
for i in range(48):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.018,.065))
    drop=bpy.context.object;drop.name='Molten droplet %02d'%i;drop.data.materials.append(molten)
    drop.location=(random.uniform(-1.1,.3),random.uniform(1.4,3.4),random.uniform(-.2,.4))
    start=random.randint(8,66);end=start+random.randint(12,28)
    drop.hide_render=True;drop.keyframe_insert('hide_render',frame=1)
    drop.hide_render=False;drop.keyframe_insert('hide_render',frame=start)
    drop.location.y-=random.uniform(2.8,4.5);drop.location.x+=random.uniform(-.5,.6)
    drop.keyframe_insert('location',frame=end)
    drop.hide_render=True;drop.keyframe_insert('hide_render',frame=end+1)
# Dramatic light rig.
def area(name,location,power,color,size,target=(0,0,0)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=location
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj
key=area('molten amber key',(-3,2,5),1900,(1,.35,.11),4)
area('soft bronze fill',(4,1,3),1250,(1,.72,.4),5)
area('cool sculptural rim',(0,3,-4),2200,(.58,.72,1),3)
for f,p in [(1,2500),(70,1900),(115,700),(180,500)]:
    key.data.energy=p;key.data.keyframe_insert('energy',frame=f)
bpy.ops.object.camera_add(location=(0,-8,1))
camera=bpy.context.object;camera.name='One continuous cinematic camera';scene.camera=camera
def camera_key(frame,loc,target):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
camera_key(1,(-1.7,-4.8,1.3),(-.9,1.3,0))
camera_key(55,(-.65,-3.5,.8),(0,0,0))
camera_key(102,(.15,-2.7,.2),(0,0,0))
camera_key(180,(.1,-7.5,.35),(0,0,0))
# Master sculpture emerges gradually from the darkness via camera, light and flow.
root.scale=(.001,)*3;root.keyframe_insert('scale',frame=1)
root.scale=(3.4/extent,)*3;root.keyframe_insert('scale',frame=105)
root.keyframe_insert('scale',frame=180)
for f,rotation in [(1,-.6),(105,-.25),(180,.16)]:
    root.rotation_euler.z=rotation;root.keyframe_insert('rotation_euler',frame=f)
for obj in (camera,root):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for key in fc.keyframe_points:key.interpolation='BEZIER'
scene.view_settings.view_transform='AgX'
scene.render.filepath=os.path.abspath('bronze_artistry_forge_')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('bronze_artistry_forge.blend'))
print('Saved bronze_artistry_forge.blend; render frames 1-180 for review.')
