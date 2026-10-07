"""Alternativa em vetor às letras pequenas: decalque para impressão 100%."""
from pathlib import Path
import math
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT=Path(__file__).resolve().parents[1]/'exports'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT))

def logo(c,x,y):
    c.saveState(); c.translate(x,y); c.scale(mm,mm)
    navy=(.025,.06,.27); cyan=(0,.77,.95); orange=(1,.22,.05)
    for r,a,b,col in [(7.7,85,280,cyan),(5.9,115,300,orange)]:
        c.setStrokeColorRGB(*col); c.setLineWidth(1)
        c.arc(-12-r,-r,-12+r,r,a,b-a)
        for angle in (a,b):
            xx=-12+r*math.cos(math.radians(angle)); yy=r*math.sin(math.radians(angle))
            c.setFillColorRGB(1,1,1); c.circle(xx,yy,1.45,stroke=1,fill=1)
    c.setFillColorRGB(*navy); c.setFont('DejaVu',6.5)
    c.drawCentredString(4.5,-1.3,'Lidera')
    c.setFont('DejaVu',1.55); c.drawCentredString(5,-4.8,'Tecnologia e Gestão')
    c.restoreState()

def main():
    c=canvas.Canvas(str(OUT/'decal_logo_escala_real.pdf'),pagesize=A4)
    c.setFont('DejaVu',13); c.drawString(20*mm,277*mm,'Lidera — decalques em escala real')
    c.setFont('DejaVu',9)
    c.drawString(20*mm,265*mm,'Imprimir a 100%, sem ajustar à página. Use papel decalque ou adesivo.')
    c.drawString(20*mm,258*mm,'Reconstrução da marca da referência; o vetor oficial é preferível se disponível.')
    for y in (222,185,148):
        for x in (47,110,173): logo(c,x*mm,y*mm)
    c.setStrokeColorRGB(0,0,0); c.setLineWidth(.4)
    c.line(20*mm,40*mm,70*mm,40*mm)
    c.line(20*mm,38*mm,20*mm,42*mm); c.line(70*mm,38*mm,70*mm,42*mm)
    c.setFont('DejaVu',9); c.drawString(20*mm,33*mm,'Esta linha deve medir 50 mm após imprimir.')
    c.save()

if __name__=='__main__': main()
