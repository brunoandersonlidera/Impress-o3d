"""Decalques vetoriais: contornos e degradês do SVG oficial, em escala real."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svgpathtools import svg2paths2, Line, CubicBezier

from logo import ASSET, WIDTH_MM

OUT = Path(__file__).resolve().parents[1] / 'exports'
NS = {'svg': 'http://www.w3.org/2000/svg'}
pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))


def artwork():
    # Parse data only: no script execution or external resources.
    paths, attrs, _ = svg2paths2(str(ASSET))
    boxes = [p.bbox() for p in paths]
    bounds = (min(b[0] for b in boxes), max(b[1] for b in boxes),
              min(b[2] for b in boxes), max(b[3] for b in boxes))
    root = ET.parse(ASSET).getroot()
    css = root.find('svg:defs/svg:style', NS).text
    fills = dict(re.findall(r'\.(fil\d+)\s*\{fill:([^;}]+)', css))
    gradients = {}
    for g in root.findall('svg:defs/svg:linearGradient', NS):
        href = g.get('{http://www.w3.org/1999/xlink}href')
        stop_source = root.find(f"svg:defs/svg:linearGradient[@id='{href[1:]}']", NS) if href else g
        stops = [(float(s.get('offset')), HexColor(re.search(r'stop-color:(#[0-9A-Fa-f]+)', s.get('style')).group(1)))
                 for s in stop_source.findall('svg:stop', NS)]
        gradients[g.get('id')] = ([float(g.get(k)) for k in ('x1', 'y1', 'x2', 'y2')], stops)
    return paths, attrs, bounds, fills, gradients


def pdf_path(c, svg_path):
    p = c.beginPath()
    for sub in svg_path.continuous_subpaths():
        p.moveTo(sub[0].start.real, sub[0].start.imag)
        for seg in sub:
            if isinstance(seg, Line):
                p.lineTo(seg.end.real, seg.end.imag)
            elif isinstance(seg, CubicBezier):
                p.curveTo(seg.control1.real, seg.control1.imag,
                          seg.control2.real, seg.control2.imag, seg.end.real, seg.end.imag)
            else:
                raise ValueError(f'Segmento SVG não suportado: {type(seg).__name__}')
        p.close()
    return p


def draw_logo(c, x, y, data):
    paths, attrs, (xmin, xmax, ymin, ymax), fills, gradients = data
    s = WIDTH_MM * mm / (xmax - xmin)
    c.saveState()
    c.translate(x, y)
    c.scale(s, -s)  # SVG Y cresce para baixo; mantém orientação original.
    c.translate(-xmin, -ymin)
    for path, attrs_i in zip(paths, attrs):
        fill = fills[attrs_i['class']]
        p = pdf_path(c, path)
        fill_mode = 1 if attrs_i['class'] == 'fil0' else 0
        if fill.startswith('#'):
            c.setFillColor(HexColor(fill))
            c.drawPath(p, stroke=0, fill=1, fillMode=fill_mode)
        else:
            gid = re.fullmatch(r'url\(#([^)]+)\)', fill).group(1)
            coords, stops = gradients[gid]
            c.saveState()
            c.clipPath(p, stroke=0, fill=0, fillMode=fill_mode)
            c.linearGradient(*coords, [color for _, color in stops],
                             positions=[pos for pos, _ in stops], extend=True)
            c.restoreState()
    c.restoreState()


def export_print_svg(bounds):
    xmin, xmax, ymin, ymax = bounds
    # Keep supplied paths, CSS and gradients verbatim; only crop the viewport
    # and set physical dimensions for a print-size copy.
    text = ASSET.read_text(encoding='utf-8')
    match = re.search(r'<svg\b[^>]*>', text, re.S)
    root_tag = match.group()
    for key, value in [('width', f'{WIDTH_MM:g}mm'),
                       ('height', f'{WIDTH_MM*(ymax-ymin)/(xmax-xmin):.8f}mm'),
                       ('viewBox', f'{xmin:.8f} {ymin:.8f} {xmax-xmin:.8f} {ymax-ymin:.8f}')]:
        root_tag = re.sub(rf'\b{key}="[^"]*"', f'{key}="{value}"', root_tag)
    text = text[:match.start()] + root_tag + text[match.end():]
    (OUT / 'logo_peito_38mm.svg').write_text(text, encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    data = artwork()
    bounds = data[2]
    height = WIDTH_MM * (bounds[3] - bounds[2]) / (bounds[1] - bounds[0])
    export_print_svg(bounds)
    c = canvas.Canvas(str(OUT / 'decal_logo_escala_real.pdf'), pagesize=A4)
    c.setTitle('Lidera — marca oficial para o peito do robô, 38 mm')
    c.setFont('DejaVu', 13)
    c.drawString(20*mm, 277*mm, 'Lidera — decalques da marca oficial')
    c.setFont('DejaVu', 9)
    c.drawString(20*mm, 265*mm, 'Imprimir a 100%, sem ajustar à página. Use papel decalque ou adesivo.')
    c.drawString(20*mm, 258*mm, f'Contornos e degradês do SVG enviado. Tamanho: {WIDTH_MM:g} × {height:.2f} mm.')
    for y in (230, 192, 154):
        for x in (28, 91, 154):
            draw_logo(c, x*mm, y*mm, data)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(.4)
    c.line(20*mm, 40*mm, 70*mm, 40*mm)
    c.line(20*mm, 38*mm, 20*mm, 42*mm)
    c.line(70*mm, 38*mm, 70*mm, 42*mm)
    c.setFont('DejaVu', 9)
    c.drawString(20*mm, 33*mm, 'Esta linha deve medir 50 mm após imprimir.')
    c.save()
    print(f'Decalque oficial: {WIDTH_MM:g} × {height:.3f} mm; 9 cópias vetoriais com degradês.')


if __name__ == '__main__':
    main()
