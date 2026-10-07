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
from head import build_head, neck_joint_spec
from limbs import build_limbs, limb_joint_specs
from fit_coupon import build_coupons
from logo import logo_metadata
from hardware import build_hardware, hardware_bom, JOINT_AXES

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
    result=[]
    probes=[(name,cq.Solid.makeCylinder(1.5,44,cq.Vector(x,y-22,z),cq.Vector(0,1,0))) for name,x,y,z in JOINT_AXES]
    probes.append(('pescoco',cq.Solid.makeCylinder(1.5,17,cq.Vector(0,0,86.75))))
    for name,probe in probes:
        b=probe.BoundingBox(); hits=[]
        for p in parts:
            if not bbox_overlap(b,p['shape'].BoundingBox()): continue
            cut=probe.intersect(p['shape'])
            if cut.Solids() and cut.Volume()>.01: hits.append({'part':p['name'],'volume':cut.Volume()})
        result.append({'joint':name,'probe_diameter_mm':3.0,'unobstructed':not hits,'hits':hits})
    return result

def inspect_mechanisms(printed,hardware):
    """Verify purchased stacks, supporting faces and straight tool access."""
    report={'hardware_components':len(hardware),'joints':hardware_bom(),
            'thread_geometry':'nominal cylinders, not a helical thread fit',
            'physical_test':False,'washer_contacts':[],'tool_access':[]}
    def volume_inside(probe):
        hits=[]
        for p in printed:
            a,b=probe.BoundingBox(),p['shape'].BoundingBox()
            if any(min(getattr(a,axis+'max'),getattr(b,axis+'max'))-
                   max(getattr(a,axis+'min'),getattr(b,axis+'min'))<=1e-7
                   for axis in ('x','y','z')):continue
            cut=probe.intersect(p['shape'])
            volume=cut.Volume() if cut.Solids() else 0
            if volume>.000001:hits.append({'part':p['name'],'volume_mm3':volume})
        return hits
    # Washers actually bear on the printed ears/neck seat. A 0.001 mm inward
    # displacement measures contact area without treating intended face
    # contact as interpenetration in the mounted assembly.
    for p in hardware:
        if p['kind'] not in ('washer','bearing'):continue
        neck=p['joint']=='pescoco'
        offsets=([(0,0,-.001),(0,0,.001)] if p['kind']=='bearing' else
                 [(0,0,.001)] if neck else
                 [(0,-.001 if 'traseira' in p['name'] else .001,0)])
        thickness=.3 if p['kind']=='bearing' else .5
        for offset in offsets:
            area=sum(h['volume_mm3'] for h in volume_inside(p['shape'].translate(offset)))/.001
            nominal_area=p['shape'].Volume()/thickness
            ratio=area/nominal_area
            report['washer_contacts'].append(dict(part=p['name'],offset=offset,
                    supported_fraction=ratio,supported=ratio>.90))
    # Allen-key bounding cylinder: across-flats 2.5 has a 2.887 mm corner
    # diameter, so a 3 mm cylinder provides a conservative straight corridor.
    for joint,x,y,z in JOINT_AXES:
        tools=[('Allen_2p5',cq.Solid.makeCylinder(1.5,20.8,
                  cq.Vector(x,y-30,z),cq.Vector(0,1,0))),
               ('socket_traseiro_OD8p2',cq.Solid.makeCylinder(4.1,21.4,
                  cq.Vector(x,y+8.6,z),cq.Vector(0,1,0)))]
        for name,probe in tools:
            hits=volume_inside(probe)
            report['tool_access'].append(dict(joint=joint,tool=name,clear=not hits,hits=hits))
    probe=cq.Solid.makeCylinder(1.5,38.5,cq.Vector(0,0,44.75))
    hits=volume_inside(probe)
    report['tool_access'].append(dict(joint='pescoco',tool='Allen_2p5_via_pelve',clear=not hits,hits=hits))
    for joint in report['joints']:
        end=joint['shaft_range_mm'][1]; top=joint['nut_range_mm'][1]
        joint['thread_protrusion_mm']=end-top
        joint['full_nut_engagement']=joint['shaft_range_mm'][0]<joint['nut_range_mm'][0] and end>=top
    report['all_washers_supported']=all(p['supported'] for p in report['washer_contacts'])
    report['all_tools_accessible']=all(p['clear'] for p in report['tool_access'])
    report['all_nuts_engaged']=all(p['full_nut_engagement'] for p in report['joints'])
    return report

def main():
    OUT.mkdir(exist_ok=True); (OUT/'STL').mkdir(exist_ok=True); (OUT/'cupons').mkdir(exist_ok=True)
    previous=json.loads((OUT/'pecas.json').read_text()) if (OUT/'pecas.json').exists() else []
    print('Modelando peças...',flush=True)
    printed=build_body()+build_base()+build_head()+build_limbs()
    hardware=build_hardware()
    parts=printed+hardware
    brand=logo_metadata()
    by_name={p['name']:p for p in parts}
    torso=by_name['torso_branco']['shape']
    for record in brand['paths']:
        shape=by_name[record['name']]['shape']
        record['actual_volume_mm3']=shape.Volume()
        record['volume_error_mm3']=abs(shape.Volume()-record['expected_volume_mm3'])
        record['bounds_cad_mm']=exact_bounds(shape)
        # Move the flat applique into the badge by its thickness: its complete
        # footprint must be supported by the unmodified white mounting face.
        outside=shape.translate((0,record['relief_mm'],0)).cut(torso)
        record['unsupported_volume_mm3']=outside.Volume() if outside.Solids() else 0.0
        record['supported_by_chest']=record['unsupported_volume_mm3']<1e-6
        if not record['supported_by_chest']:
            raise ValueError('Marca fora da face do peito: '+record['name'])
    (OUT/'validacao_logo.json').write_text(json.dumps(brand,indent=2,ensure_ascii=False))
    coupons=build_coupons()
    if len({p['name'] for p in parts})!=len(parts): raise ValueError('Nomes duplicados')
    rows=[]; mesh=[]
    asm=cq.Assembly(name='Lidera_articulado_180mm')
    hardware_assemblies={j:cq.Assembly(name='ferragens_'+j) for j in [r['joint'] for r in hardware_bom()]}
    for i,p in enumerate(parts):
        s=p['shape']
        if not isinstance(s,cq.Shape): raise TypeError(p['name'])
        if not s.isValid() or s.Volume()<=0: raise ValueError('Sólido inválido: '+p['name'])
        b=s.BoundingBox()
        purchased=p['group']=='hardware'
        target=hardware_assemblies[p['joint']] if purchased else asm
        target.add(s,name=p['name'],color=cq.Color(*p['color']))
        removed=0
        if not purchased:
            flat=print_orientation(p)
            removed=export_print_stl(flat,OUT/'STL'/(p['name']+'.stl'))
        cq.exporters.export(s,str(OUT/'STL'/(p['name']+'_montagem.stl')),tolerance=.075,angularTolerance=.12) if not purchased and '--assembly-stl' in sys.argv else None
        row=dict(name=p['name'],group=p['group'],color=p['color'],volume_mm3=round(s.Volume(),3),solids=len(s.Solids()),bbox_mm=[round(v,3) for v in exact_bounds(s)],stl_degenerate_facets_removed=removed,notes=p.get('notes',''),printable=not purchased)
        for key in ('joint','kind','standard','length_mm','purchased'):
            if key in p:row[key]=p[key]
        rows.append(row)
        v,f=s.tessellate(.18,.18)
        mesh.append(dict(name=p['name'],group=p['group'],kind=p.get('kind'),color=p['color'],vertices=[vv.toTuple() for vv in v],faces=f))
        # Cached editable BREP avoids expensive re-generation during inspection.
        (OUT/'BREP').mkdir(exist_ok=True)
        s.exportBrep(str(OUT/'BREP'/(p['name']+'.brep')))
    print('Exportando STEP com nomes e cores...',flush=True)
    for group in hardware_assemblies.values():asm.add(group)
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
    (OUT/'ferragens.json').write_text(json.dumps(hardware_bom(),indent=2,ensure_ascii=False))
    (OUT/'articulacoes.json').write_text(json.dumps(limb_joint_specs()+[neck_joint_spec()],indent=2,ensure_ascii=False))
    print('Inspecionando interferências da pose...',flush=True)
    overlaps=inspect_overlap(parts)
    bore_tests=inspect_bores(printed)
    mechanisms=inspect_mechanisms(printed,hardware)
    (OUT/'validacao_articulacoes.json').write_text(json.dumps(mechanisms,indent=2,ensure_ascii=False))
    compound=cq.Compound.makeCompound([p['shape'] for p in parts]); b=compound.BoundingBox()
    report={'cadquery_version':cq.__version__,'parts':len(parts),'printable_parts':len(printed),'hardware_components':len(hardware),'solids':len(compound.Solids()),'all_valid':all(p['shape'].isValid() for p in parts),'bounds_mm':exact_bounds(compound),'overlaps':overlaps,'bore_tests':bore_tests,'bore_scope':'printed pieces; purchased screw occupies each bore in assembled STEP','physical_test':False,'range_of_motion_verified':False}
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
    if not all(mechanisms[k] for k in ('all_washers_supported','all_tools_accessible','all_nuts_engaged')):
        raise ValueError('Articulação requer correção de apoio, engate da porca ou acesso de ferramenta')
    print('STEP reimportado e válido.',flush=True)

if __name__=='__main__': main()
