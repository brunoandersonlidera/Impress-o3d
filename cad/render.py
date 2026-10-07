"""Preview da geometria CAD real (rodar com Blender --background --python)."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]/'exports'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
data=json.loads((ROOT/'render_meshes.json').read_text())
def linear(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for p in data:
    me=bpy.data.meshes.new(p['name']); me.from_pydata(p['vertices'],[],p['faces']); me.update()
    ob=bpy.data.objects.new(p['name'],me); bpy.context.collection.objects.link(ob)
    mat=bpy.data.materials.new(p['name']); mat.diffuse_color=(*p['color'],1); mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*(linear(v) for v in p['color']),1)
    shader.inputs['Roughness'].default_value=.32
    shader.inputs['Metallic'].default_value=.08
    ob.data.materials.append(mat)
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except: pass
    ob.select_set(False)

scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=48
scene.cycles.use_denoising=False; scene.cycles.device='CPU'
scene.render.resolution_x=1100; scene.render.resolution_y=1300; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.world.color=(.27,.28,.32)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.115,.16,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.55
scene.view_settings.view_transform='AgX'

def light(name,pos,energy,size):
    d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=pos
    o.rotation_euler=(Vector((0,0,90))-o.location).to_track_quat('-Z','Y').to_euler()

light('principal',(-120,-180,270),1100000,160)
light('preenchimento',(180,-80,170),650000,130)
light('recorte',(10,180,240),1500000,100)
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-11.2))
floor=bpy.context.object
mat=bpy.data.materials.new('floor'); mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.09,.115,.16,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.82
floor.data.materials.append(mat)

camd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',camd)
bpy.context.collection.objects.link(cam); scene.camera=cam; camd.type='ORTHO'; camd.ortho_scale=220
def render(name,position,scale=220,target=(0,0,83)):
    cam.location=position; camd.ortho_scale=scale
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(ROOT/name); bpy.ops.render.render(write_still=True)

render('Lidera_preview.png',(215,-380,190))
scene.render.resolution_x=900; scene.render.resolution_y=1100
render('vista_frontal.png',(0,-400,90))
render('vista_lateral.png',(400,0,90))
render('vista_traseira.png',(0,400,90))
scene.render.resolution_x=1200; scene.render.resolution_y=800
render('logo_peito_detalhe.png',(8,-240,82),52,(0,-18,77))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Lidera_preview.blend'))
