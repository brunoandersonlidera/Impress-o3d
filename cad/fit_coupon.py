"""Corpos de prova: folga M3 e ajuste clevis. Imprimir antes do boneco."""
import cadquery as cq

def build_coupons():
    out=[]
    colors=(.22,.25,.32)
    block=cq.Workplane('XY').box(40,15,6,centered=(True,True,False)).val()
    for x,d in [(-12,3.2),(0,3.3),(12,3.4)]:
        block=block.cut(cq.Solid.makeCylinder(d/2,6,cq.Vector(x,0,0)))
        txt=cq.Workplane('XY',origin=(x,4,6)).text(str(d),2,0.45,combine=False).val()
        block=block.fuse(txt)
    out.append(dict(name='cupom_furos_M3',shape=block,color=colors,group='coupon',notes='Da esquerda para direita: Ø3.2,3.3,3.4mm. Medir com seu parafuso M3.'))
    # Independent clevis and tongue; no print-in-place surfaces.
    bridge=cq.Workplane('XY').box(16,11.4,3,centered=(True,True,False)).val()
    for y in (-4.2,4.2):
        ear=cq.Workplane('XY').box(16,3,14,centered=(True,True,False)).translate((0,y,0)).edges('|Y').fillet(1).val()
        bridge=bridge.fuse(ear)
    bore=cq.Solid.makeCylinder(1.65,20,cq.Vector(0,-10,9),cq.Vector(0,1,0))
    bridge=bridge.cut(bore)
    tongue=cq.Workplane('XY').box(10,4.8,11,centered=(True,True,False)).translate((0,0,3.3)).val().cut(bore)
    out.append(dict(name='cupom_clevis_5p4',shape=bridge,color=colors,group='coupon',notes='Vão5.4; lingueta4.8; folga nominal0.3 por lado.'))
    out.append(dict(name='cupom_lingueta_4p8',shape=tongue,color=(.05,.65,.85),group='coupon',notes='Usar com cupom clevis e parafuso M3.'))
    return out
