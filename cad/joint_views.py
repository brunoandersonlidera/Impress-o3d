"""Cortes reais de sete tipos de junta e montagem STEP explodida para inspeção.

Executar depois de cad/build.py: python3 cad/joint_views.py
Não gera STLs. Os recortes e afastamentos são somente vistas de inspeção.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

import cadquery as cq
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from hardware import JOINT_AXES, build_hardware, hardware_bom


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports"
VIEWS = OUT / "juntas"
FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

CASES = [
    dict(key="ombro", title="Ombro", joint="ombro_E", fixed=["torso_branco"],
         moving=["left_upper_arm_frame"], quantity=2,
         detail="Torso branco recebe a lingueta do braço superior."),
    dict(key="cotovelo", title="Cotovelo", joint="cotovelo_E", fixed=["left_upper_arm_frame"],
         moving=["left_forearm_frame"], quantity=2,
         detail="Suporte do braço superior recebe a lingueta do antebraço."),
    dict(key="punho", title="Punho", joint="punho_E", fixed=["left_forearm_frame"],
         moving=["left_hand_navy"], quantity=2,
         detail="Suporte menor de raio 4,5 mm; mesma largura axial de 11,4 mm."),
    dict(key="quadril", title="Quadril", joint="quadril_E", fixed=["pelve_azul"],
         moving=["left_thigh_frame"], quantity=2,
         detail="Pelve possui acessos rebaixados para cabeça, arruela e porca."),
    dict(key="joelho", title="Joelho", joint="joelho_E", fixed=["left_thigh_frame"],
         moving=["left_shin_frame"], quantity=2,
         detail="Suporte da coxa recebe a lingueta da canela."),
    dict(key="tornozelo", title="Tornozelo", joint="tornozelo_E", fixed=["left_shin_frame"],
         moving=["left_boot_sole_and_joint"], quantity=2,
         detail="Lingueta e sola são uma estrutura; capas das botas são fixas."),
    dict(key="pescoco", title="Pescoço", joint="pescoco", fixed=["torso_branco"],
         moving=["head_white_front_shell", "head_white_rear_shell"], quantity=1,
         detail="Porca, parafuso e cabeça giram juntos; o apoio usa PTFE/PET."),
]

FIXED_COLOR = (0.33, 0.48, 0.70)
MOVING_COLOR = (0.93, 0.62, 0.25)
METAL_COLOR = (0.62, 0.66, 0.72)
BEARING_COLOR = (0.32, 0.69, 0.64)


def imported(name):
    path = OUT / "BREP" / (name + ".brep")
    if not path.exists():
        raise FileNotFoundError(f"Falta {path.name}; execute primeiro python3 cad/build.py")
    shape = cq.Shape.importBrep(str(path))
    if not shape.isValid() or shape.Volume() <= 0:
        raise ValueError("BREP inválido: " + name)
    return shape


def fused(names):
    result = imported(names[0])
    for name in names[1:]:
        result = result.fuse(imported(name))
    return result.clean()


def translated_axis(case, amount):
    return (0, 0, amount) if case["key"] == "pescoco" else (0, amount, 0)


def local_xy(case, point):
    x, y, z = point
    px, py, pz = case["pivot"]
    return (z - pz, y - py) if case["key"] == "pescoco" else (y - py, z - pz)


def radial_offset(case, moving):
    if case["key"] == "pescoco":
        return (0.0, 0.0, 13.0)
    box = moving.BoundingBox()
    px, py, pz = case["pivot"]
    dx = (box.xmin + box.xmax) / 2 - px
    dz = (box.zmin + box.zmax) / 2 - pz
    length = math.hypot(dx, dz)
    if length < .01:
        raise ValueError("Não foi possível identificar o sentido radial da lingueta")
    # True 3D radial movement in XZ, not an axial path through a clevis ear.
    factor = 25 / length
    return (dx * factor, 0.0, dz * factor)


def cropped(case, shape):
    x, y, z = case["pivot"]
    if case["key"] == "pescoco":
        tool = cq.Solid.makeBox(28, 16, 25, cq.Vector(x - 14, y - 8, z - 4))
    else:
        tool = cq.Solid.makeBox(27, 35, 28, cq.Vector(x - 13.5, y - 17.5, z - 14))
    return shape.intersect(tool).clean()


def section(case, shape):
    x, y, z = case["pivot"]
    plane = cq.Face.makePlane(120, 120, cq.Vector(x, y, z), cq.Vector(1, 0, 0))
    cut = shape.intersect(plane)
    triangles, contours = [], []
    for face in cut.Faces():
        vertices, facets = face.tessellate(.045, .09)
        projected = [local_xy(case, vertex.toTuple()) for vertex in vertices]
        triangles.extend([[projected[i] for i in facet] for facet in facets])
        for edge in face.Edges():
            points, _ = edge.sample(max(2, min(90, math.ceil(edge.Length() / .13))))
            contours.append([local_xy(case, point.toTuple()) for point in points])
    if not triangles:
        raise ValueError("Corte sem faces na junta " + case["key"])
    return dict(triangles=triangles, contours=contours, area_mm2=cut.Area())


def component(case, name, shape, color, role, offset):
    cut = section(case, shape)
    shift = local_xy(case, tuple(case["pivot"][i] + offset[i] for i in range(3)))
    return dict(name=name, shape=shape, color=color, role=role, offset=offset,
                projected_offset=shift, section=cut)


def assemble_case(case, hardware, positions):
    case = dict(case)
    case["pivot"] = positions[case["joint"]]
    fixed = fused(case["fixed"])
    parts = [
        component(case, "C_suporte_" + case["key"], cropped(case, fixed), FIXED_COLOR,
                  "C", (0, 0, 0)),
    ]
    if case["key"] == "pescoco":
        # The roof traps the nut axially. Opening at the Y=0 seam is its real
        # assembly route, so show separate shells and lateral nut insertion.
        for name, role, offset, color in [
            (case["moving"][0], "Df", (0, -18, 13), MOVING_COLOR),
            (case["moving"][1], "Dt", (0, 18, 13), (0.86, 0.56, 0.24)),
        ]:
            parts.append(component(case, name, cropped(case, imported(name)), color, role, offset))
    else:
        moving = fused(case["moving"])
        parts.append(component(case, "D_movel_" + case["key"], cropped(case, moving), MOVING_COLOR,
                               "D", radial_offset(case, moving)))
    # Section colours identify functions; the STEP retains the same legend.
    for item in hardware:
        if item["joint"] != case["joint"]:
            continue
        kind = item["kind"]
        if kind == "screw":
            role, offset = "A", translated_axis(case, -27)
        elif kind == "nut":
            role = "F"
            offset = (0, -10, 0) if case["key"] == "pescoco" else translated_axis(case, 28)
        elif kind == "bearing":
            role, offset = "G", translated_axis(case, 8)
        elif "traseira" in item["name"]:
            role, offset = "E", translated_axis(case, 15)
        else:
            role, offset = "B", translated_axis(case, -11)
        parts.append(component(case, item["name"], item["shape"],
                               BEARING_COLOR if kind == "bearing" else METAL_COLOR,
                               role, offset))
    case["components"] = parts
    return case


def font_setup():
    if FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont("JointFont", str(FONT_PATH)))
        return "JointFont"
    return "Helvetica"


def text(c, x, y, value, font, size=9, color=colors.HexColor("#25334b")):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x * mm, y * mm, value)


def wrapped(c, x, y, value, font, size=8.5, width=175, leading=4.2):
    line = ""
    for word in value.split():
        test = (line + " " + word).strip()
        if pdfmetrics.stringWidth(test, font, size) > width * mm and line:
            text(c, x, y, line, font, size)
            y -= leading
            line = word
        else:
            line = test
    if line:
        text(c, x, y, line, font, size)
        y -= leading
    return y


def draw_piece(c, part, center, scale, exploded=False):
    dx, dy = part["projected_offset"] if exploded else (0, 0)
    ox, oy = center
    c.setFillColor(colors.Color(*part["color"]))
    for triangle in part["section"]["triangles"]:
        p = c.beginPath()
        for i, (x, y) in enumerate(triangle):
            point = ((ox + scale * (x + dx)) * mm, (oy + scale * (y + dy)) * mm)
            (p.moveTo if i == 0 else p.lineTo)(*point)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    c.setStrokeColor(colors.HexColor("#293849"))
    c.setLineWidth(.16 * mm)
    for points in part["section"]["contours"]:
        p = c.beginPath()
        for i, (x, y) in enumerate(points):
            point = ((ox + scale * (x + dx)) * mm, (oy + scale * (y + dy)) * mm)
            (p.moveTo if i == 0 else p.lineTo)(*point)
        c.drawPath(p, stroke=1, fill=0)


def dimension(c, center, scale, start, end, height, value, font):
    ox, oy = center
    a, b = ox + start * scale, ox + end * scale
    line_y = oy + height * scale
    c.setStrokeColor(colors.HexColor("#4e6077"))
    c.setLineWidth(.18 * mm)
    c.line(a * mm, (line_y - 1.3) * mm, a * mm, (line_y + 1.3) * mm)
    c.line(b * mm, (line_y - 1.3) * mm, b * mm, (line_y + 1.3) * mm)
    c.line(a * mm, line_y * mm, b * mm, line_y * mm)
    c.setFont(font, 8)
    c.setFillColor(colors.HexColor("#25334b"))
    c.drawCentredString((a + b) / 2 * mm, (line_y + 1.8) * mm, value)


def axis(c, center, scale, extent, label, font):
    ox, oy = center
    c.setStrokeColor(colors.HexColor("#8f9bae"))
    c.setDash(2 * mm, 1 * mm)
    c.setLineWidth(.18 * mm)
    c.line((ox + extent[0] * scale) * mm, oy * mm,
           (ox + extent[1] * scale) * mm, oy * mm)
    c.setDash()
    text(c, ox + extent[1] * scale - 12, oy + 2, label, font, 8)


def label_roles(c, case, center, scale, font):
    ox, oy = center
    for part in case["components"]:
        triangles = part["section"]["triangles"]
        pts = [p for triangle in triangles for p in triangle]
        minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
        miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
        dx, dy = part["projected_offset"]
        px, py = ox + scale * ((minx + maxx) / 2 + dx), oy + scale * (maxy + dy) + 3.5
        c.setFillColor(colors.HexColor("#ffffff"))
        c.setStrokeColor(colors.HexColor("#465a72"))
        c.circle(px * mm, py * mm, 2.5 * mm, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#25334b"))
        c.setFont(font, 8)
        c.drawCentredString(px * mm, (py - .9) * mm, part["role"])


def exploded_bounds(case):
    points = []
    for part in case["components"]:
        dx, dy = part["projected_offset"]
        points.extend((x + dx, y + dy) for triangle in part["section"]["triangles"] for x, y in triangle)
    return min(p[0] for p in points), max(p[0] for p in points), min(p[1] for p in points), max(p[1] for p in points)


def svg_case(case):
    # Same real CAD section as the PDF; triangle fill preserves actual holes.
    width, height = 1020, 750
    xmin, xmax, ymin, ymax = exploded_bounds(case)
    scale = min(930 / (xmax - xmin + 8), 445 / (ymax - ymin + 8), 11)
    ox, oy = 510 - (xmin + xmax) / 2 * scale, 327.5 + (ymin + ymax) / 2 * scale
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
              '<rect width="100%" height="100%" fill="white"/>',
              f'<text x="35" y="43" font-family="sans-serif" font-size="25">{escape(case["title"])} — corte explodido CAD</text>',
              '<text x="35" y="70" font-family="sans-serif" font-size="15">Afastamentos somente de exibição; ferragens comerciais não impressas.</text>',
              f'<line x1="45" y1="{oy:.3f}" x2="970" y2="{oy:.3f}" stroke="#abb5c4" stroke-dasharray="8 5"/>']
    for part in case["components"]:
        dx, dy = part["projected_offset"]
        color = "#" + "".join(f"{round(v * 255):02x}" for v in part["color"])
        for triangle in part["section"]["triangles"]:
            points = " ".join(f"{ox + scale * (x + dx):.3f},{oy - scale * (y + dy):.3f}" for x, y in triangle)
            pieces.append(f'<polygon points="{points}" fill="{color}"/>')
        for contour in part["section"]["contours"]:
            points = " ".join(f"{ox + scale * (x + dx):.3f},{oy - scale * (y + dy):.3f}" for x, y in contour)
            pieces.append(f'<polyline points="{points}" fill="none" stroke="#26364a" stroke-width="1.5"/>')
    legend = ["A: parafuso M3 × 16 (metal)", "B: arruela frontal/inferior Ø6 × Ø3,2 × 0,5",
              "C: suporte impresso fixo (azul técnico)",
              "Df/Dt: cascos frontal/traseiro, abertos pela união" if case["key"] == "pescoco" else "D: lingueta impressa móvel (laranja técnico)",
              "E: arruela traseira (somente membros)", "F: porca M3, 5,5 entre faces × 2,4",
              "G: apoio PTFE/PET Ø12 × Ø3,3 × 0,3 (somente pescoço)"]
    for i, line in enumerate(legend):
        pieces.append(f'<text x="35" y="{590 + i * 21}" font-family="sans-serif" font-size="15">{escape(line)}</text>')
    for part in case["components"]:
        dx, dy = part["projected_offset"]
        points = [point for triangle in part["section"]["triangles"] for point in triangle]
        px = ox + ((min(p[0] for p in points) + max(p[0] for p in points)) / 2 + dx) * scale
        py = oy - (max(p[1] for p in points) + dy) * scale - 12
        pieces.append(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="12" fill="white" stroke="#465a72"/>')
        pieces.append(f'<text x="{px:.3f}" y="{py + 5:.3f}" text-anchor="middle" font-family="sans-serif" font-size="14">{part["role"]}</text>')
    pieces.append('</svg>')
    return "\n".join(pieces)


def pdf(cases):
    font = font_setup()
    c = canvas.Canvas(str(OUT / "Guia_articulacoes_M3.pdf"), pagesize=A4)
    c.setTitle("Lidera — articulações M3, cortes e vistas explodidas")
    for page, case in enumerate(cases, 1):
        neck = case["key"] == "pescoco"
        text(c, 15, 278, "LIDERA / ARTICULAÇÕES", font, 10)
        text(c, 15, 265, case["title"] + f" — {case['quantity']} junta(s)", font, 20)
        wrapped(c, 15, 255, case["detail"], font, 9)
        text(c, 15, 244, "1. Corte local montado — estruturas, ferragens e vazios reais", font, 10)
        center, scale = ((72, 211), 4.0) if neck else ((105, 211), 4.0)
        axis(c, center, scale, (-13, 24) if neck else (-15, 15), "+Z" if neck else "+Y", font)
        for part in case["components"]:
            draw_piece(c, part, center, scale)
        if neck:
            dimension(c, center, scale, -.5, 15.5, -10, "16,0 sob a cabeça", font)
            dimension(c, center, scale, 8.75, 9.05, -13, "PTFE/PET 0,3", font)
        else:
            dimension(c, center, scale, -5.7, 5.7, -10, "11,4", font)
            dimension(c, center, scale, -2.7, 2.7, 10, "vão 5,4", font)
            text(c, 15, 164, "Lingueta 4,8 | orelhas 3,0 cada | folga 0,3 por lado | furo Ø3,3", font, 8)
        text(c, 15, 153, "2. Cortes por peça afastados — vista explodida para identificação", font, 10)
        xmin, xmax, ymin, ymax = exploded_bounds(case)
        scale = min(180 / (xmax - xmin + 8), 55 / (ymax - ymin + 10), 1.75)
        center = (105 - (xmin + xmax) / 2 * scale, 116 - (ymin + ymax) / 2 * scale)
        axis(c, center, scale, (xmin - 3, xmax + 3), "+Z" if neck else "+Y", font)
        for part in case["components"]:
            draw_piece(c, part, center, scale, True)
        label_roles(c, case, center, scale, font)
        text(c, 15, 79, "A parafuso    B arruela frontal/inferior    C suporte    " +
             ("Df/Dt cascos frente/trás" if neck else "D peça móvel"), font, 8)
        text(c, 15, 74, "E arruela traseira    F porca    G apoio PTFE/PET (pescoço)", font, 8)
        instruction = ("Abra os cascos em Y e insira a porca lateralmente pela união: o teto impede saída axial. "
                       "Parafuso e arruela entram por baixo do torso. "
                       "Instale o apoio deslizante; cabeça, porca e parafuso giram juntos. "
                       "Trava-rosca removível de baixa resistência somente entre os metais."
                       if neck else
                       "A lingueta entra radialmente pela abertura do suporte, sem atravessar uma orelha. "
                       "Alinhe os furos e passe o parafuso em +Y. Arruelas ficam fora das orelhas. "
                       "Aperte em pequenos incrementos; não deforme o suporte para eliminar a folga.")
        wrapped(c, 15, 62, instruction, font, 8.3)
        text(c, 15, 39, "Azul/laranja: identificação técnica das estruturas; capas decorativas omitidas.", font, 7.5)
        text(c, 15, 34, "Cortes do CAD, ampliados. Cotas em mm. Afastamentos explodidos não são cotas de montagem.", font, 7.5)
        text(c, 15, 29, "As seções de cada peça acompanham seu afastamento; o STEP permite examinar o recorte em 3D.", font, 7.5)
        text(c, 15, 22, "Sem ensaio físico, torque validado ou certificação de amplitude. Consulte cad/JOINTS.md.", font, 7.5)
        text(c, 182, 12, f"{page}/7", font, 8)
        c.showPage()
    c.save()


def main():
    VIEWS.mkdir(parents=True, exist_ok=True)
    hardware = build_hardware()
    positions = {joint: (x, y, z) for joint, x, y, z in JOINT_AXES}
    positions["pescoco"] = (0, 0, 86.75)
    cases = [assemble_case(case, hardware, positions) for case in CASES]
    pdf(cases)
    assembly = cq.Assembly(name="Articulacoes_explodidas_inspecao")
    records = []
    for i, case in enumerate(cases):
        (VIEWS / (case["key"] + ".svg")).write_text(svg_case(case), encoding="utf-8")
        grid = ((i % 3) * 110.0, (i // 3) * 100.0, 0.0)
        case_rows = []
        for part in case["components"]:
            source = part["shape"]
            center_offset = tuple(-v for v in case["pivot"])
            display = source.translate(center_offset).translate(part["offset"]).translate(grid)
            if not display.isValid() or display.Volume() <= 0:
                raise ValueError("Recorte inválido: " + part["name"])
            assembly.add(display, name=case["key"] + "_" + part["name"],
                         color=cq.Color(*part["color"]))
            row = dict(name=part["name"], role=part["role"],
                       exploded_offset_mm=list(part["offset"]),
                       section_area_mm2=round(part["section"]["area_mm2"], 5),
                       solids=len(source.Solids()), volume_mm3=round(source.Volume(1e-8), 5))
            case_rows.append(row)
        records.append(dict(case=case["key"], example=case["joint"],
                            axis="Z" if case["key"] == "pescoco" else "Y",
                            actual_pivot_xyz_mm=list(case["pivot"]),
                            inspection_grid_xyz_mm=list(grid), components=case_rows))
    step = OUT / "Articulacoes_explodidas.step"
    assembly.export(str(step))
    reimported = cq.importers.importStep(str(step)).val()
    expected_solids = sum(r["solids"] for case in records for r in case["components"])
    # Adaptive integration avoids the coarse default OCC integration of curved
    # cropped surfaces. Compare at one part per million of total volume.
    expected_volume = sum(part["shape"].Volume(1e-8) for case in cases for part in case["components"])
    actual_volume = reimported.Volume(1e-8)
    relative_volume_error = abs(actual_volume - expected_volume) / expected_volume
    if not reimported.isValid() or len(reimported.Solids()) != expected_solids:
        raise ValueError("Reimportação do STEP explodido divergente")
    if relative_volume_error > 1e-6:
        raise ValueError("Volume do STEP explodido divergente")
    box = reimported.BoundingBox()
    report = dict(description="Local CAD crops and sections, exploded for inspection only.",
                  pdf_pages=7, svg_files=7, cases=records,
                  all_valid=True,
                  step_reimport_valid=reimported.isValid(),
                  step_solids=len(reimported.Solids()), expected_solids=expected_solids,
                  bounds_mm=[box.xmin, box.ymin, box.zmin, box.xmax, box.ymax, box.zmax],
                  step_volume_mm3=round(actual_volume, 5),
                  expected_volume_mm3=round(expected_volume, 5),
                  step_volume_error_mm3=round(abs(actual_volume - expected_volume), 7),
                  volume_integration_relative_tolerance=1e-8,
                  step_volume_error_relative=relative_volume_error,
                  volume_comparison_relative_tolerance=1e-6,
                  physical_test=False, range_of_motion_verified=False,
                  hardware_bom=hardware_bom())
    (OUT / "validacao_explodido.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["pdf_pages", "svg_files", "step_reimport_valid", "step_solids"]}))


if __name__ == "__main__":
    main()
