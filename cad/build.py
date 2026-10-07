"""Gera montagem STEP, STLs separados, dados de inspeção e malhas para render.
Rodar na raiz do repositório: python3 cad/build.py
"""
from pathlib import Path
import json, math, sys, time
import cadquery as cq
import struct
import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from body import build_body, build_base
from head import build_head
from limbs import build_limbs
from fit_coupon import build_coupons

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports'

def exact_bounds(s):
    box=Bnd_Box()
    # Ignore cached preview triangulations; use the actual CAD surfaces.
    BRepBndLib.AddOptimal_s(s.wrapped,box,False,False)
    return list(box.Get())

def export_print_stl(shape,path):
    cq.exporters.export(shape,str(path),tolerance=.075,angularTolerance=.12)
    raw=path.read_bytes(); n=struct.unpack('<I',raw[80:84])[0]
    dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
    data=np.frombuffer(raw,offset=84,count=n,dtype=dtype).copy()
    t=data['v'].astype(float)
    area2=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
    # OCC emits occasional zero-area seam facets; removing them changes no surface.
    data=data[area2>1e-12]
    data['v'][:,:,2]-=data['v'][:,:,2].min()
    path.write_bytes(raw[:80]+struct.pack('<I',len(data))+data.tobytes())
    return n-len(data)

def print_orientation(p):
    s=p['shape']; name=p['name'].lower(); group=p['group']
    # Split shells and face appliques lie on their assembly planes.
    if group=='graphics' or (group=='head' and any(t in name for t in ['visor','rim','eye','brow','mouth','tooth','teeth','tongue','pupil','iris','lash','face','highlight','sclera'])):
        s=s.rotate((0,0,0),(1,0,0),-90)
    elif group=='head' and 'shell' in name:
        angle=90 if any(t in name for t in ['rear','back']) else -90
        s=s.rotate((0,0,0),(1,0,0),angle)
    elif group=='head' and any(t in name for t in ['ear','disc']):
        s=s.rotate((0,0,0),(0,1,0),90)
    elif group=='head' and 'back_navy_panel' in name:
        s=s.rotate((0,0,0),(1,0,0),90)
    elif 'boot' in group and name.endswith(('_left','_right')):
        s=s.rotate((0,0,0),(0,1,0),-90 if name.endswith('_left') else 90)
    elif group!='base' and any(t in name for t in ['arm','forearm','thigh','shin','hand','leg','bra','coxa','canela','mao']):
        s=s.rotate((0,0,0),(1,0,0),90 if 'back' in name else -90)
    b=s.BoundingBox()
    return s.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))

def bbox_overlap(a,b):
    return min(a.xmax,b.xmax)-max(a.xmin,b.xmin)>0.015 and min(a.ymax,b.ymax)-max(a.ymin,b.ymin)>0.015 and min(a.zmax,b.zmax)-max(a.zmin,b.zmin)>0.015

def inspect_overlap(parts):
    boxes=[p['shape'].BoundingBox() for p in parts]; hits=[]
    for i,p in enumerate(parts):
        for j in range(i+1,len(parts)):
            q=parts[j]
            if not bbox_overlap(boxes[i],boxes[j]): continue
            c=p['shape'].intersect(q['shape'])
            v=abs(c.Volume()) if c.Solids() else 0
            if v>0.01:
                hits.append({'a':p['name'],'b':q['name'],'volume_mm3':round(v,4)})
    return hits

def inspect_bores(parts):
    """Direct geometry checks that the 13 actual M3 axes are unobstructed."""
    axes=[('ombro_E',-28,84.75),('ombro_D',28,84.75),
          ('cotovelo_E',-51,69.75),('cotovelo_D',43,66.75),
          ('punho_E',-61.027119,88.065481),('punho_D',31,59.75),
          ('quadril_E',-14,54.75),('quadril_D',14,54.75),
          ('joelho_E',-15,34.5),('joelho_D',15,34.5),
          ('tornozelo_E',-15,17.25),('tornozelo_D',15,17.25)]
    result=[]
    probes=[(name,cq.Solid.makeCylinder(1.5,44,cq.Vector(x,-22,z),cq.Vector(0,1,0))) for name,x,z in axes]
    probes.append(('pescoco',cq.Solid.makeCylinder(1.5,17,cq.Vector(0,0,86.75))))
    for name,probe in probes:
        b=probe.BoundingBox(); hits=[]
        for p in parts:
            if not bbox_overlap(b,p['shape'].BoundingBox()): continue
            cut=probe.intersect(p['shape'])
            if cut.Solids() and cut.Volume()>.01: hits.append({'part':p['name'],'volume':cut.Volume()})
        result.append({'joint':name,'probe_diameter_mm':3.0,'unobstructed':not hits,'hits':hits})
    return result

def main():
    OUT.mkdir(exist_ok=True); (OUT/'STL').mkdir(exist_ok=True); (OUT/'cupons').mkdir(exist_ok=True)
    previous=json.loads((OUT/'pecas.json').read_text()) if (OUT/'pecas.json').exists() else []
    print('Modelando peças...',flush=True)
    parts=build_body()+build_base()+build_head()+build_limbs()
    coupons=build_coupons()
    if len({p['name'] for p in parts})!=len(parts): raise ValueError('Nomes duplicados')
    rows=[]; mesh=[]
    asm=cq.Assembly(name='Lidera_articulado_180mm')
    for i,p in enumerate(parts):
        s=p['shape']
        if not isinstance(s,cq.Shape): raise TypeError(p['name'])
        if not s.isValid() or s.Volume()<=0: raise ValueError('Sólido inválido: '+p['name'])
        b=s.BoundingBox()
        asm.add(s,name=p['name'],color=cq.Color(*p['color']))
        flat=print_orientation(p)
        removed=export_print_stl(flat,OUT/'STL'/(p['name']+'.stl'))
        cq.exporters.export(s,str(OUT/'STL'/(p['name']+'_montagem.stl')),tolerance=.075,angularTolerance=.12) if '--assembly-stl' in sys.argv else None
        rows.append(dict(name=p['name'],group=p['group'],color=p['color'],volume_mm3=round(s.Volume(),3),solids=len(s.Solids()),bbox_mm=[round(v,3) for v in exact_bounds(s)],stl_degenerate_facets_removed=removed,notes=p.get('notes','')))
        v,f=s.tessellate(.18,.18)
        mesh.append(dict(name=p['name'],color=p['color'],vertices=[vv.toTuple() for vv in v],faces=f))
        # Cached editable BREP avoids expensive re-generation during inspection.
        (OUT/'BREP').mkdir(exist_ok=True)
        s.exportBrep(str(OUT/'BREP'/(p['name']+'.brep')))
    print('Exportando STEP com nomes e cores...',flush=True)
    asm.export(str(OUT/'Lidera_articulado_180mm.step'))
    for p in coupons:
        if not p['shape'].isValid(): raise ValueError(p['name'])
        export_print_stl(print_orientation(p),OUT/'cupons'/(p['name']+'.stl'))
    cq.exporters.export(cq.Compound.makeCompound([p['shape'].translate((i*50,0,0)) for i,p in enumerate(coupons)]),str(OUT/'cupons'/'cupons_encaixes.step'))
    # Remove only obsolete outputs explicitly recorded by the previous run.
    for name in {r['name'] for r in previous}-{p['name'] for p in parts}:
        for folder,ext in [('STL','.stl'),('BREP','.brep')]:
            old=OUT/folder/(name+ext)
            if old.exists(): old.unlink()
    (OUT/'pecas.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
    (OUT/'render_meshes.json').write_text(json.dumps(mesh))
    print('Inspecionando interferências da pose...',flush=True)
    overlaps=inspect_overlap(parts)
    bore_tests=inspect_bores(parts)
    compound=cq.Compound.makeCompound([p['shape'] for p in parts]); b=compound.BoundingBox()
    report={'cadquery_version':cq.__version__,'parts':len(parts),'solids':len(compound.Solids()),'all_valid':all(p['shape'].isValid() for p in parts),'bounds_mm':exact_bounds(compound),'overlaps':overlaps,'bore_tests':bore_tests,'physical_test':False,'range_of_motion_verified':False}
    (OUT/'validacao.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2),flush=True)
    print('Reimportando STEP...',flush=True)
    re=cq.importers.importStep(str(OUT/'Lidera_articulado_180mm.step')).val()
    report['step_reimport_valid']=re.isValid()
    report['step_reimport_solids']=len(re.Solids())
    report['step_volume_mm3']=round(re.Volume(),3)
    report['step_bounds_mm']=exact_bounds(re)
    report['step_bounds_error_mm']=max(abs(a-b) for a,b in zip(report['bounds_mm'],report['step_bounds_mm']))
    (OUT/'validacao.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    if not re.isValid() or len(re.Solids())!=len(compound.Solids()) or report['step_bounds_error_mm']>.001: raise ValueError('Reimportação STEP divergente')
    if overlaps or not all(r['unobstructed'] for r in bore_tests):
        raise ValueError('Montagem requer correção de interferência ou eixo bloqueado')
    print('STEP reimportado e válido.',flush=True)

if __name__=='__main__': main()
