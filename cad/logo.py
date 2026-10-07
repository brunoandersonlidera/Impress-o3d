"""Official Lidera SVG contours converted to exact, extruded CAD curves.

The asset is data: XML and SVG path coordinates are parsed without evaluating
scripts or fetching referenced resources. Cubic Beziers stay cubic Beziers;
the outlines are not traced, replaced with fonts, or polygonally sampled.

Coordinates here match body.py before its final Z=-18.25 translation.
Each SVG path is one coloured component; text components contain loose
letter solids, and all original counter holes remain open.
"""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import cadquery as cq
from svgpathtools import CubicBezier, Line, parse_path


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "logo_lidera_vetor01.svg"
WIDTH_MM = 38.0
CENTER_X = 0.0
CENTER_Z = 95.25
FACE_Y = -18.0
RELIEF_MM = 0.7
SUBTITLE_RELIEF_MM = 0.55


def _rgb(hex_string):
    return tuple(int(hex_string[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


TEXT_COLOR = _rgb("#3F4096")
# STEP colour is solid per component. The SVG's cyan/blue gradient has
# endpoints #1078F5 and #06F2F0; their channel midpoint is #0BB5F3.
CYAN_COLOR = _rgb("#0BB5F3")
# The original orange gradient explicitly includes this middle colour stop.
ORANGE_COLOR = _rgb("#E74E3B")

_PATH_SETTINGS = (
    ("logo_Lidera_azul", "fil0", TEXT_COLOR, RELIEF_MM),
    ("logo_subtitulo_azul", "fil0", TEXT_COLOR, SUBTITLE_RELIEF_MM),
    ("logo_simbolo_laranja_superior", "fil1", ORANGE_COLOR, RELIEF_MM),
    ("logo_simbolo_laranja_inferior", "fil2", ORANGE_COLOR, RELIEF_MM),
    ("logo_simbolo_ciano", "fil3", CYAN_COLOR, RELIEF_MM),
)


def _read_svg(svg_path):
    root = ET.parse(svg_path).getroot()
    if any("transform" in node.attrib for node in root.iter()):
        raise ValueError("This official logo importer expects SVG without transforms")
    nodes = root.findall(".//{*}path")
    if len(nodes) != len(_PATH_SETTINGS):
        raise ValueError("Expected the five paths of the official Lidera asset")
    paths = []
    for node, (_, expected_class, _, _) in zip(nodes, _PATH_SETTINGS):
        if node.attrib.get("class") != expected_class:
            raise ValueError("Unexpected path class or path order in the logo asset")
        path = parse_path(node.attrib["d"])
        if any(not isinstance(segment, (Line, CubicBezier)) for segment in path):
            raise ValueError("The official asset uses only lines and cubic Beziers")
        if not all(subpath.isclosed() for subpath in path.continuous_subpaths()):
            raise ValueError("All logo contours must be closed")
        paths.append(path)
    bboxes = [path.bbox() for path in paths]
    bounds = (
        min(bb[0] for bb in bboxes), max(bb[1] for bb in bboxes),
        min(bb[2] for bb in bboxes), max(bb[3] for bb in bboxes),
    )
    return paths, bounds


def _contains_bbox(outer, inner, tolerance=1e-7):
    return (outer[0] - tolerance <= inner[0]
            and inner[1] <= outer[1] + tolerance
            and outer[2] - tolerance <= inner[2]
            and inner[3] <= outer[3] + tolerance)


def _filled_area(path):
    # SVG paths may contain disconnected contours; svgpathtools.area() only
    # accepts one continuous closed contour, so integrate each separately.
    return sum(contour.area() for contour in path.continuous_subpaths())


def _contour_groups(path):
    """Associate each clockwise hole with its containing outer contour.

    In this official asset every outer has positive signed SVG area and every
    hole has negative signed area. This satisfies both nonzero (fil0) and
    evenodd (fil1/2/3) fill rules. Exact Bezier containment verifies each hole.
    """
    contours = path.continuous_subpaths()
    outers = [contour for contour in contours if contour.area() > 0]
    holes = [contour for contour in contours if contour.area() < 0]
    if len(outers) + len(holes) != len(contours):
        raise ValueError("Zero-area contour in official SVG")
    groups = [(outer, []) for outer in outers]
    for hole in holes:
        candidates = [i for i, outer in enumerate(outers)
                      if _contains_bbox(outer.bbox(), hole.bbox())
                      and hole.is_contained_by(outer)]
        if not candidates:
            raise ValueError("SVG hole has no containing outer contour")
        index = min(candidates, key=lambda i: abs(outers[i].area()))
        groups[index][1].append(hole)
    return groups


def _make_wire(path, point_map):
    edges = []
    for segment in path:
        if isinstance(segment, Line):
            start, end = point_map(segment.start), point_map(segment.end)
            # Relative SVG coordinates can introduce a final closure line
            # shorter than 1e-13 mm. Remove only numerical zero-length edges.
            if (end - start).Length <= 1e-7:
                continue
            edges.append(cq.Edge.makeLine(start, end))
        else:
            edges.append(cq.Edge.makeBezier([
                point_map(segment.start), point_map(segment.control1),
                point_map(segment.control2), point_map(segment.end),
            ]))
    wire = cq.Wire.assembleEdges(edges)
    if not wire.isValid() or not wire.IsClosed():
        raise ValueError("Invalid or open official-logo contour")
    return wire


def build_logo(svg_path=None):
    """Return five colour-separated exact CAD components of the official logo.

    ``svg_path`` is an optional test override. Normal repository execution
    always reads ``assets/logo_lidera_vetor01.svg``.
    """
    paths, bounds = _read_svg(Path(svg_path) if svg_path else ASSET)
    xmin, xmax, ymin, ymax = bounds
    scale = WIDTH_MM / (xmax - xmin)
    midpoint_x, midpoint_y = (xmin + xmax) / 2, (ymin + ymax) / 2

    def point_map(point):
        return cq.Vector(CENTER_X + (point.real - midpoint_x) * scale,
                         FACE_Y,
                         CENTER_Z - (point.imag - midpoint_y) * scale)

    parts = []
    for path, (name, _, color, relief) in zip(paths, _PATH_SETTINGS):
        solids = []
        groups = _contour_groups(path)
        for outer, holes in groups:
            outer_wire = _make_wire(outer, point_map)
            hole_wires = [_make_wire(hole, point_map) for hole in holes]
            solids.append(cq.Solid.extrudeLinear(
                outer_wire, hole_wires, cq.Vector(0, -relief, 0)))
        shape = (solids[0] if len(solids) == 1
                 else cq.Compound.makeCompound(solids)).clean()
        expected_volume = abs(_filled_area(path)) * scale ** 2 * relief
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError("Invalid official-logo CAD component: " + name)
        if abs(shape.Volume() - expected_volume) > max(1e-6, expected_volume * 1e-7):
            raise ValueError("CAD volume differs from exact SVG filled area: " + name)
        notes = (
            "Official SVG contours, exact cubic Beziers and original holes; "
            f"{len(solids)} solid(s), {relief:g} mm relief. "
        )
        if name == "logo_subtitulo_azul":
            notes += (
                "Subtitle only 1.757 mm high at 38 mm total logo width; "
                "strokes around 0.31 mm. Use the official SVG as a decal for "
                "faithful small text; a 0.4 mm nozzle cannot reproduce it reliably.")
        elif "simbolo_ciano" in name:
            notes += "SVG gradient represented by solid midpoint colour #0BB5F3."
        elif "laranja" in name:
            notes += "SVG orange gradient represented by its #E74E3B middle stop."
        else:
            notes += "Official text colour #3F4096; loose letter solids."
        parts.append(dict(name=name, shape=shape, color=color,
                          group="graphics", notes=notes))
    return parts


def logo_metadata(svg_path=None):
    """Report source geometry and expected manufacturing dimensions."""
    paths, bounds = _read_svg(Path(svg_path) if svg_path else ASSET)
    scale = WIDTH_MM / (bounds[1] - bounds[0])
    info = dict(bounds_svg=bounds, scale_mm_per_svg_unit=scale,
                total_width_mm=WIDTH_MM,
                total_height_mm=(bounds[3] - bounds[2]) * scale,
                transforms=0, paths=[])
    for path, (name, _, color, relief) in zip(paths, _PATH_SETTINGS):
        bb = path.bbox()
        groups = _contour_groups(path)
        info["paths"].append(dict(
            name=name, bounds_svg=bb, width_mm=(bb[1] - bb[0]) * scale,
            height_mm=(bb[3] - bb[2]) * scale,
            outer_count=len(groups), hole_count=sum(len(x[1]) for x in groups),
            filled_area_svg=_filled_area(path), expected_volume_mm3=_filled_area(path) * scale ** 2 * relief,
            relief_mm=relief, color_rgb=color,
            line_count=sum(isinstance(s, Line) for s in path),
            cubic_bezier_count=sum(isinstance(s, CubicBezier) for s in path),
        ))
    return info


if __name__ == "__main__":
    import json
    print(json.dumps(logo_metadata(), ensure_ascii=False, indent=2))
    for part in build_logo():
        print(part["name"], part["shape"].isValid(),
              round(part["shape"].Volume(), 6), len(part["shape"].Solids()))
