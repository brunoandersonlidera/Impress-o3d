"""Corpo e base do mascote Lidera. Unidades: mm; frente: -Y."""
import cadquery as cq

WHITE=(0.93,0.94,0.97)
NAVY=(0.025,0.06,0.27)
CYAN=(0.00,0.77,0.95)
ORANGE=(1.00,0.22,0.05)

def part(name,shape,color,group,notes=''):
    if isinstance(shape,cq.Workplane): shape=shape.val()
    return dict(name=name,shape=shape,color=color,group=group,notes=notes)

def cyl_y(x,z,r,y0,y1):
    return cq.Solid.makeCylinder(r,y1-y0,cq.Vector(x,y0,z),cq.Vector(0,1,0))

def rounded_plate(w,h,r,x,z,y,depth):
    return cq.Workplane('XZ',origin=(x,y,z)).rect(w,h).extrude(depth).edges('|Y').fillet(r).val()

def loft_sections(sections):
    wp=cq.Workplane('XY').workplane(offset=sections[0][0]).ellipse(sections[0][1]/2,sections[0][2]/2)
    last=sections[0][0]
    for z,w,d in sections[1:]:
        wp=wp.workplane(offset=z-last).ellipse(w/2,d/2); last=z
    return wp.loft(combine=True).val()

def clevis(body,x,z,lower_open=False):
    # Circular ears 3 mm thick, 5.4 mm interior gap, M3 clearance bore.
    for a,b in [(-5.7,-2.7),(2.7,5.7)]:
        body=body.fuse(cyl_y(x,z,6,a,b))
    body=body.cut(cyl_y(x,z,6.35,-2.7,2.7))
    if lower_open:
        slot=cq.Workplane('XY').box(12.7,5.4,15).translate((x,0,z-7.5)).val()
        body=body.cut(slot)
    return body.cut(cyl_y(x,z,1.65,-25,25)).clean()

def build_body():
    parts=[]
    torso=loft_sections([(81,32,27),(88,43,32),(98,50,34),(104,46,31),(108,37,26)])
    # Integral front badge produces a level mounting face for separately colored graphics.
    badge=rounded_plate(42,27,9,0,94.5,-18,-8)
    torso=torso.fuse(badge)
    # Bridge shoulders to the body before making the articulation cavities.
    for side in (-1,1):
        bridge=cq.Workplane('XY').box(9,11.4,10).translate((side*24.5,0,103)).edges('|Y').fillet(2).val()
        torso=torso.fuse(bridge)
        torso=clevis(torso,side*28,103)
    neck=cq.Solid.makeCylinder(7,3.7,cq.Vector(0,0,108))
    torso=torso.fuse(neck)
    # Access from underside before joining torso and pelvis: no hidden trapped screw.
    torso=torso.cut(cq.Solid.makeCylinder(1.65,36,cq.Vector(0,0,80)))
    torso=torso.cut(cq.Solid.makeCylinder(3.1,24,cq.Vector(0,0,81)))
    parts.append(part('torso_branco',torso.clean(),WHITE,'body','Ombros M3; parafuso do pescoço inserido por baixo antes de colar a cintura.'))
    pelvis=loft_sections([(63,26,23),(69,37,29),(76,41,30),(81,32,27)])
    for side in (-1,1): pelvis=clevis(pelvis,side*14,73,True)
    # Recessed bolt head and hex nut leave a true 11.4 mm clamp stack at hips.
    for x in (-14,14):
        pelvis=pelvis.cut(cyl_y(x,73,3.1,-25,-5.7))
        nut=cq.Workplane('XZ',origin=(x,5.7,73)).polygon(6,6.8).extrude(-20).val()
        pelvis=pelvis.cut(nut)
    # Torso and pelvis share a gluing face at z81; two loose registration dowels.
    for x in (-7,7):
        pelvis=pelvis.cut(cq.Solid.makeCylinder(1.7,3.2,cq.Vector(x,0,77.8)))
        parts[0]['shape']=parts[0]['shape'].cut(cq.Solid.makeCylinder(1.7,3.2,cq.Vector(x,0,81)))
        parts.append(part('alinhador_cintura_'+('E' if x<0 else 'D'),cq.Solid.makeCylinder(1.5,6,cq.Vector(x,0,78)),NAVY,'body','Pino colável Ø3; folga diametral0.4.'))
    parts.append(part('pelve_azul',pelvis.clean(),NAVY,'body','Quadris clevis M3; união colada ao torso depois de montar pescoço.'))
    collar=cq.Workplane('XY',origin=(0,0,108)).circle(10).circle(7.15).extrude(1.3).val()
    parts.append(part('colar_ciano',collar,CYAN,'body'))
    spacer=cq.Workplane('XY',origin=(0,0,109.3)).circle(8.5).circle(7.15).extrude(2.4).val()
    parts.append(part('colar_azul',spacer,NAVY,'body'))
    # Cyan U detail at the lower chest, made as an extruded swept polyline.
    pts=[(-18,86),(-13,84.5),(-8,83),(-5,81.8),(5,81.8),(8,83),(13,84.5),(18,86)]
    strip=None
    for (x1,z1),(x2,z2) in zip(pts,pts[1:]):
        import math
        dx,dz=x2-x1,z2-z1; L=math.hypot(dx,dz); nx,nz=-dz/L*0.55,dx/L*0.55
        s=cq.Workplane('XZ',origin=(0,-18,0)).polyline([(x1+nx,z1+nz),(x2+nx,z2+nz),(x2-nx,z2-nz),(x1-nx,z1-nz)]).close().extrude(0.8).val()
        strip=s if strip is None else strip.fuse(s)
    parts.append(part('friso_peito_ciano',strip.clean(),CYAN,'body','Aplique; ajustar/colar ao contorno inferior do peito.'))
    # Individual colored logo solids. Typography is reconstructed, not source vector artwork.
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    logo=cq.Workplane('XZ',origin=(4.5,-18,96.8)).text('Lidera',6.5,0.7,fontPath=font,kind='bold',combine=False).val()
    parts.append(part('logo_Lidera_azul',logo,NAVY,'graphics','Letras soltas; preferir decalque se montagem com bico0.4 for difícil.'))
    subtitle=cq.Workplane('XZ',origin=(5,-18,91.8)).text('Tecnologia e Gestão',1.55,0.55,fontPath=font,combine=False).val()
    parts.append(part('logo_subtitulo_azul',subtitle,NAVY,'graphics','Texto fino: decalque recomendado ou bico0.2; não se garante legibilidade com0.4.'))
    import math
    for label,rr,start,end,col in [('ciano',7.7,85,280,CYAN),('laranja',5.9,115,300,ORANGE)]:
        x0,z0=-12,96
        n=40
        outer=[(x0+(rr+.5)*math.cos(math.radians(start+(end-start)*i/n)),z0+(rr+.5)*math.sin(math.radians(start+(end-start)*i/n))) for i in range(n+1)]
        inner=[(x0+(rr-.5)*math.cos(math.radians(start+(end-start)*i/n)),z0+(rr-.5)*math.sin(math.radians(start+(end-start)*i/n))) for i in reversed(range(n+1))]
        s=cq.Workplane('XZ',origin=(0,-18,0)).polyline(outer+inner).close().extrude(.7).val()
        parts.append(part('logo_arco_'+label,s,col,'graphics'))
        arc_idx=len(parts)-1
        for i,a in enumerate((start,end)):
            px=x0+rr*math.cos(math.radians(a)); pz=z0+rr*math.sin(math.radians(a))
            ring=cq.Workplane('XZ',origin=(px,-18,pz)).circle(1.45).circle(.65).extrude(.7).val()
            # Trim underlying arc to avoid overlap with hollow circle applique.
            parts[arc_idx]['shape']=parts[arc_idx]['shape'].cut(cyl_y(px,pz,1.48,-19,-17.9))
            parts.append(part('logo_no_'+label+'_'+str(i),ring,col,'graphics'))
    # Rear chest accent mirrors the blue/cyan language of the reference.
    rear=rounded_plate(25,10,3,0,86,14.9,-0.9)
    parts[0]['shape']=parts[0]['shape'].cut(rear).clean()
    parts.append(part('painel_dorsal_azul',rear,NAVY,'body'))
    # Colored logo arcs give way to every node; assembled inserts do not overlap.
    nodes=[p['shape'] for p in parts if p['name'].startswith('logo_no_')]
    for p in parts:
        if p['name'].startswith('logo_arco_'):
            for node in nodes: p['shape']=p['shape'].cut(node)
            p['shape']=p['shape'].clean()
    # Reference has a large head and short legs: keep body proportions and M3
    # geometry intact, move the complete rigid body down instead of stretching.
    for p in parts: p['shape']=p['shape'].translate((0,0,-18.25))
    neck_extension=cq.Workplane('XY',origin=(0,0,93.45)).circle(7).circle(1.65).extrude(2.05).val()
    parts[0]['shape']=parts[0]['shape'].fuse(neck_extension).clean()
    for p in parts:
        if p['name']=='colar_azul':
            p['shape']=cq.Workplane('XY',origin=(0,0,91.05)).circle(8.5).circle(7.15).extrude(4.45).val()
    return parts

def build_base():
    parts=[]
    # 126 diameter; 11mm total height. No permanently captive feet.
    lower=cq.Workplane('XY',origin=(0,0,-11)).circle(63).extrude(6).edges('%Circle').fillet(.7).val()
    band=cq.Workplane('XY',origin=(0,0,-5)).circle(62.8).circle(58.8).extrude(1.7).val()
    topnavy=cq.Workplane('XY',origin=(0,0,-3.3)).circle(62.8).extrude(2.0).edges('>Z').fillet(.5).val()
    white=cq.Workplane('XY',origin=(0,0,-1.3)).circle(59.3).extrude(1.3).edges('>Z').fillet(.35).val()
    for name,s,col in [('base_inferior_azul',lower,NAVY),('base_faixa_ciano',band,CYAN),('base_superior_azul',topnavy,NAVY),('base_tampo_branco',white,WHITE)]:
        parts.append(part(name,s,col,'base','Base colável; boneco pode ficar livre ou ser fixado por baixo dos pés.'))
    return parts

if __name__=='__main__':
    for p in build_body()+build_base():
        print(p['name'],p['shape'].isValid(),round(p['shape'].Volume(),2),len(p['shape'].Solids()))
