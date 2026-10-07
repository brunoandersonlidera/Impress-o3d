"""Purchased M3 hardware shown in its assembled position, never print parts.

The screw heads, hex sockets, washers and hex nuts have useful mechanical
envelopes. M3 x 0.5 threads are represented by nominal, smooth 3 mm cylinders
and bores: no cosmetic helix is generated and no printed screw is implied.
Dimensions are nominal; inspect the actual supplier's hardware and test the
printed fits before assembly. A normal ISO 4032 nut is not a taller nyloc nut.
"""
from __future__ import annotations

import math

import cadquery as cq


METAL_COLOR = (0.70, 0.72, 0.76)
SCREW_LENGTH_MM = 16.0
THREAD_DIAMETER_MM = 3.0
THREAD_PITCH_MM = 0.5
HEAD_DIAMETER_MM = 5.5
HEAD_HEIGHT_MM = 3.0
SOCKET_AF_MM = 2.5
SOCKET_DEPTH_MM = 1.5
NUT_AF_MM = 5.5
NUT_HEIGHT_MM = 2.4
WASHER_ID_MM = 3.2
WASHER_OD_MM = 6.0
WASHER_HEIGHT_MM = 0.5
BEARING_ID_MM = 3.3
BEARING_OD_MM = 12.0
BEARING_HEIGHT_MM = 0.3

# Four entries: joint, X, Y and Z of the limb pivot. The right hand is offset
# by -1 mm in Y; its complete hardware stack follows that actual pivot.
JOINT_AXES = (
    ("ombro_E", -28.0, 0.0, 84.75),
    ("ombro_D", 28.0, 0.0, 84.75),
    ("cotovelo_E", -51.0, 0.0, 69.75),
    ("cotovelo_D", 43.0, 0.0, 66.75),
    ("punho_E", -61.027119, 0.0, 88.065481),
    ("punho_D", 31.0, -1.0, 59.75),
    ("quadril_E", -14.0, 0.0, 54.75),
    ("quadril_D", 14.0, 0.0, 54.75),
    ("joelho_E", -15.0, 0.0, 34.5),
    ("joelho_D", 15.0, 0.0, 34.5),
    ("tornozelo_E", -15.0, 0.0, 17.25),
    ("tornozelo_D", 15.0, 0.0, 17.25),
)


def _cylinder(radius, height, z=0.0):
    return cq.Solid.makeCylinder(radius, height, cq.Vector(0, 0, z))


def _cone(radius1, radius2, height, z):
    return cq.Solid.makeCone(radius1, radius2, height, cq.Vector(0, 0, z))


def _hex_prism(across_flats, height, z=0.0):
    # CadQuery's polygon diameter passes through the six vertices.
    return (cq.Workplane("XY", origin=(0, 0, z))
            .polygon(6, 2 * across_flats / math.sqrt(3))
            .extrude(height).val())


def _screw():
    """ISO 4762 M3 x 16 envelope, under-head plane at local Z=0."""
    # Small external chamfers leave the head within its nominal 5.5 x 3 mm
    # envelope and preserve the actual bearing plane at Z=0.
    head = _cone(2.55, 2.75, 0.20, -3.0)
    head = head.fuse(_cylinder(2.75, 2.70, -2.8))
    head = head.fuse(_cone(2.75, 2.65, 0.10, -0.1))
    socket = _hex_prism(SOCKET_AF_MM, SOCKET_DEPTH_MM, -HEAD_HEIGHT_MM)
    head = head.cut(socket)
    # The final 0.25 mm is a physical lead-in chamfer, not a thread helix.
    shaft = _cylinder(THREAD_DIAMETER_MM / 2, SCREW_LENGTH_MM - 0.25)
    tip = _cone(1.5, 1.25, 0.25, SCREW_LENGTH_MM - 0.25)
    return head.fuse(shaft).fuse(tip).clean()


def _nut():
    """ISO 4032 M3 normal nut, nominal bore and entry chamfers."""
    hexagon = _hex_prism(NUT_AF_MM, NUT_HEIGHT_MM)
    # Circular external chamfers, rather than six decorative planar cuts.
    # They do not change across-flats, height or the anti-rotation fit.
    corner_radius = NUT_AF_MM / math.sqrt(3)
    chamfer_height = 0.25
    envelope = _cone(NUT_AF_MM / 2, corner_radius, chamfer_height, 0.0)
    envelope = envelope.fuse(_cylinder(
        corner_radius, NUT_HEIGHT_MM - 2 * chamfer_height, chamfer_height))
    envelope = envelope.fuse(_cone(
        corner_radius, NUT_AF_MM / 2, chamfer_height,
        NUT_HEIGHT_MM - chamfer_height))
    nut = hexagon.intersect(envelope)
    bore = _cylinder(THREAD_DIAMETER_MM / 2, NUT_HEIGHT_MM)
    bore = bore.fuse(_cone(1.62, 1.5, 0.12, 0.0))
    bore = bore.fuse(_cone(1.5, 1.62, 0.12, NUT_HEIGHT_MM - 0.12))
    return nut.cut(bore).clean()


def _washer():
    """DIN 433 / ISO 7092 small-series M3 washer: 3.2 x 6 x 0.5."""
    return _cylinder(WASHER_OD_MM / 2, WASHER_HEIGHT_MM).cut(
        _cylinder(WASHER_ID_MM / 2, WASHER_HEIGHT_MM)).clean()


def _neck_bearing():
    """Sliding washer cut from PTFE/PET sheet, not a 0.3 mm printed part."""
    return _cylinder(BEARING_OD_MM / 2, BEARING_HEIGHT_MM).cut(
        _cylinder(BEARING_ID_MM / 2, BEARING_HEIGHT_MM)).clean()


def _on_y(shape, x, y, z):
    # A proper rotation maps local +Z to global +Y. No reflection is used.
    return shape.rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y, z))


def _part(name, shape, joint, kind, standard, notes, length=None):
    part = dict(name=name, shape=shape, color=METAL_COLOR, group="hardware",
                joint=joint, kind=kind, standard=standard, notes=notes,
                purchased=True, printable=False)
    if length is not None:
        part["length_mm"] = length
    return part


def build_hardware():
    """Return the 52 purchased/cut components in their assembled positions.

    Each limb has screw, front washer, rear washer and normal nut. The neck
    has screw, lower steel washer, captive normal nut and PTFE/PET sliding
    washer between the neck boss and head. No washer under the nut is assumed.
    Never export these parts as printable STLs.
    """
    screw, nut, washer = _screw(), _nut(), _washer()
    parts = []
    screw_notes = (
        "Purchased steel socket-head screw ISO 4762 M3x16, pitch 0.5 mm; "
        "head diameter 5.5 x 3 mm, Allen socket AF 2.5 x 1.5 mm deep. "
        "Nominal smooth 3 mm shaft substitutes for the thread in CAD; "
        "not a printable screw or a thread-fit certification.")
    nut_notes = (
        "Purchased normal hex nut ISO 4032 M3, pitch 0.5 mm; AF 5.5 x "
        "2.4 mm high. Nominal smooth 3 mm bore substitutes for the thread. "
        "Not a nyloc nut; secure the chosen assembly without locking its pivot.")
    washer_notes = (
        "Purchased small-series M3 washer DIN 433 / ISO 7092; "
        "ID 3.2 x OD 6 x thickness 0.5 mm. Larger ISO 7089 / DIN 125 "
        "washers have a different outside diameter and require revised seats.")
    for joint, x, center_y, z in JOINT_AXES:
        parts.extend([
            _part("parafuso_M3x16_" + joint,
                  _on_y(screw, x, center_y - 6.2, z), joint, "screw",
                  "ISO 4762", screw_notes, SCREW_LENGTH_MM),
            _part("arruela_M3_frontal_" + joint,
                  _on_y(washer, x, center_y - 6.2, z), joint, "washer",
                  "DIN 433 / ISO 7092", washer_notes),
            _part("arruela_M3_traseira_" + joint,
                  _on_y(washer, x, center_y + 5.7, z), joint, "washer",
                  "DIN 433 / ISO 7092", washer_notes),
            _part("porca_M3_" + joint,
                  _on_y(nut, x, center_y + 6.2, z), joint, "nut",
                  "ISO 4032", nut_notes),
        ])
    joint = "pescoco"
    parts.extend([
        _part("parafuso_M3x16_" + joint, screw.translate((0, 0, 86.25)),
              joint, "screw", "ISO 4762", screw_notes, SCREW_LENGTH_MM),
        _part("arruela_M3_inferior_" + joint, washer.translate((0, 0, 86.25)),
              joint, "washer", "DIN 433 / ISO 7092", washer_notes),
        _part("porca_M3_" + joint, nut.translate((0, 0, 98.8)),
              joint, "nut", "ISO 4032", nut_notes),
    ])
    bearing = _part(
        "arruela_deslizamento_PTFE_PET_pescoco",
        _neck_bearing().translate((0, 0, 95.5)), joint, "bearing",
        "Custom cut PTFE/PET sheet",
        "Sliding washer cut from purchased 0.3 mm PTFE or PET sheet; "
        "ID 3.3 x OD 12 x thickness 0.3 mm, Z 95.5..95.8 mm. "
        "Separates the body neck boss from the head bearing face. "
        "Not a DIN steel washer or a printable 0.3 mm part; inspect real "
        "sheet thickness and adjust assembly without forcing the swivel.")
    bearing["color"] = (0.86, 0.90, 0.92)
    parts.append(bearing)
    if len(parts) != 52 or len({part["name"] for part in parts}) != 52:
        raise ValueError("Expected 13 screws, 13 nuts, 25 steel washers and one bearing")
    if any(not part["shape"].isValid() or len(part["shape"].Solids()) != 1
           or part["shape"].Volume() <= 0 for part in parts):
        raise ValueError("Invalid purchased-hardware envelope")
    return parts


def hardware_bom():
    """Return one purchasing/stack record for each of the 13 pivots."""
    rows = []
    joints = [(joint, "Y", (x, y, z), 2)
              for joint, x, y, z in JOINT_AXES]
    joints.append(("pescoco", "Z", (0.0, 0.0, 86.75), 1))
    for joint, axis, center, washer_quantity in joints:
        limb = axis == "Y"
        origin = center[1] if limb else 0.0
        rows.append(dict(
            joint=joint, axis=axis, position_mm=list(center),
            thread="M3x0.5", length_mm=SCREW_LENGTH_MM,
            screw_standard="ISO 4762", screw_quantity=1,
            nut_standard="ISO 4032", nut_quantity=1,
            washer_standard="DIN 433 / ISO 7092",
            washer_quantity=washer_quantity,
            washer_size_mm=[WASHER_ID_MM, WASHER_OD_MM, WASHER_HEIGHT_MM],
            shaft_range_mm=([origin - 6.2, origin + 9.8]
                            if limb else [86.25, 102.25]),
            head_range_mm=([origin - 9.2, origin - 6.2]
                           if limb else [83.25, 86.25]),
            nut_range_mm=([origin + 6.2, origin + 8.6]
                          if limb else [98.8, 101.2]),
            washer_ranges_mm=([[origin - 6.2, origin - 5.7],
                               [origin + 5.7, origin + 6.2]]
                              if limb else [[86.25, 86.75]]),
            bearing_quantity=0 if limb else 1,
            bearing_material=None if limb else "0.3 mm PTFE or PET sheet",
            bearing_size_mm=None if limb else [BEARING_ID_MM, BEARING_OD_MM,
                                               BEARING_HEIGHT_MM],
            bearing_range_mm=None if limb else [95.5, 95.8],
            printable=False,
            notes=("Commercial hardware. Thread represented by nominal "
                   "cylinders; verify real fasteners and physical fit. "
                   + ("Two small-series washers outside the 11.4 mm clevis."
                      if limb else "Only lower steel washer; nut sits in head "
                      "pocket. One cut PTFE/PET sliding washer supports the head.")),
        ))
    return rows


if __name__ == "__main__":
    import json
    parts = build_hardware()
    print(json.dumps(hardware_bom(), ensure_ascii=False, indent=2))
    print("Purchased components:", len(parts),
          "screws:", sum(p["kind"] == "screw" for p in parts),
          "nuts:", sum(p["kind"] == "nut" for p in parts),
          "washers:", sum(p["kind"] == "washer" for p in parts),
          "sliding bearings:", sum(p["kind"] == "bearing" for p in parts))
