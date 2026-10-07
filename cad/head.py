"""Lidera robot head, millimetres; front is negative Y.

The single artwork fixes appearance, not manufacturing dimensions. These
dimensions reconstruct the character at 180 mm and leave separate colour
inserts, an opening shell and an M3 neck swivel. No reference mesh is used.
"""
from __future__ import annotations

import math
import cadquery as cq

WHITE = (0.95, 0.955, 0.98)
NAVY = (0.025, 0.065, 0.27)
CYAN = (0.0, 0.82, 0.97)
BLACK = (0.003, 0.015, 0.065)
CORAL = (1.0, 0.20, 0.28)

# Final-coordinate dimensions of the serviceable M3 head swivel. Hardware
# remains separate from the printed head: no adhesive on these bearing faces.
NECK_BOTTOM_Z = 95.8
NECK_BORE_DIAMETER = 3.3
NECK_NUT_BOTTOM_Z = 98.8
NECK_NUT_POCKET_TOP_Z = 101.5
NECK_BOSS_TOP_Z = 104.0
NECK_NUT_VERTEX_DIAMETER = 6.8


def neck_joint_spec():
    """Dimensions and assembly intent for the purchased neck hardware."""
    return {
        "axis": [0.0, 0.0, 1.0],
        "pivot_xyz_mm": [0.0, 0.0, 95.65],
        "shaft_bore_diameter_mm": NECK_BORE_DIAMETER,
        "printed_head_bottom_z_mm": NECK_BOTTOM_Z,
        "printed_head_boss_radius_mm": 7.5,
        "printed_head_boss_top_z_mm": NECK_BOSS_TOP_Z,
        "nut_pocket_bottom_z_mm": NECK_NUT_BOTTOM_Z,
        "nut_pocket_top_z_mm": NECK_NUT_POCKET_TOP_Z,
        "nut_pocket_across_flats_mm": NECK_NUT_VERTEX_DIAMETER * math.sqrt(3) / 2,
        "nut_retaining_roof_thickness_mm": NECK_BOSS_TOP_Z - NECK_NUT_POCKET_TOP_Z,
        "nut_seat_floor_thickness_mm": NECK_NUT_BOTTOM_Z - NECK_BOTTOM_Z,
        "nut_axial_clearance_mm": NECK_NUT_POCKET_TOP_Z - NECK_NUT_BOTTOM_Z - 2.4,
        "nut_iso4032_across_flats_mm": 5.5,
        "nut_iso4032_height_mm": 2.4,
        "nut_installed_z_mm": [98.8, 101.2],
        "screw_iso4762_size": "M3x16",
        "screw_shaft_z_mm": [86.25, 102.25],
        "screw_head_z_mm": [83.25, 86.25],
        "screw_head_diameter_mm": 5.5,
        "screw_head_socket_across_flats_mm": 2.5,
        "washer_din433_z_mm": [86.25, 86.75],
        "washer_din433_outer_diameter_mm": 6.0,
        "washer_din433_inner_diameter_mm": 3.2,
        "bearing_washer_material": "smooth PTFE or PET sheet, cut to size",
        "bearing_washer_z_mm": [95.5, 95.8],
        "bearing_washer_outer_diameter_mm": 12.0,
        "bearing_washer_inner_diameter_mm": 3.3,
        "shaft_projection_beyond_nut_mm": 1.05,
        "nut_insertion": "Side-load into the half-hex pocket through open head seam Y=0, then close both white shells.",
        "tool_access": "2.5 mm Allen key inserted upward along Z through the pelvis service hole and torso counterbore.",
        "assembly": "Insert nut while head is open. Insert screw and DIN433 washer through torso underside before closing waist. Place bearing washer between torso collar and head. Tighten only enough to hold the head pose; keep moving bearing surfaces free of glue.",
    }


def _box(w, d, h, xyz):
    return cq.Workplane("XY").box(w, d, h).translate(xyz).val()


def _round_xz(w, h, r, thickness, x=0, y=-26, z=139.5):
    return (cq.Workplane("XZ", origin=(x, y, z)).rect(w, h)
            .extrude(thickness).edges("|Y").fillet(r).val())


def _ellipse_xz(w, h, thickness, x, y, z):
    return (cq.Workplane("XZ", origin=(x, y, z)).ellipse(w / 2, h / 2)
            .extrude(thickness).val())


def _cylinder(r, h, xyz, direction):
    return cq.Solid.makeCylinder(r, h, cq.Vector(*xyz), cq.Vector(*direction))


def _ring_x(side, outer, inner, start, depth, z=140):
    xyz = (side * start, 0, z)
    direction = (side, 0, 0)
    return _cylinder(outer, depth, xyz, direction).cut(
        _cylinder(inner, depth, xyz, direction))


def _build_unscaled_head(cut_antenna_recesses=True):
    parts = []

    def add(name, shape, color, notes=""):
        shape = shape.clean()
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError("Invalid head component: " + name)
        parts.append(dict(name=name, shape=shape, color=color,
                          group="head", notes=notes))

    outer = (cq.Workplane("XY").box(78, 52, 54).edges().fillet(11)
             .translate((0, 0, 139)).val())
    inner = (cq.Workplane("XY").box(72, 46, 48).edges().fillet(8)
             .translate((0, 0, 139)).val())
    shell = outer.cut(inner)

    # An opening rather than a plate pushed into the white shell. The cyan
    # bezel and navy screen sit exactly against one another without overlap.
    shell = shell.cut(_round_xz(66, 44, 14, 23, y=-17))
    screen = _round_xz(64, 42, 13, 2.0, y=-24)
    bezel = _round_xz(66, 44, 14, 2.0, y=-24).cut(screen)
    # A backing lip connects the bezel to the edge of the white opening.
    bezel_back = _round_xz(66, 44, 14, 5, y=-19).cut(
        _round_xz(64, 42, 13, 5, y=-19))
    bezel = bezel.fuse(bezel_back)

    # Inset top panel, flush around its edges; a removable cover crosses the
    # head seam and must be fitted after closing both white shells.
    top_panel = (cq.Workplane("XY").box(34, 23, 1.2)
                 .edges("|Z").fillet(4).translate((0, 0, 165.8)).val())
    shell = shell.cut(top_panel)

    # Back panel tapered like the broad blue stripe in the rear reference.
    def back_blank(y, depth):
        return (cq.Workplane("XZ", origin=(0, y, 0))
                .moveTo(-17, 158).lineTo(17, 158)
                .lineTo(10, 137).threePointArc((0, 134), (-10, 137))
                .close().extrude(depth).val())

    back_profile = back_blank(28.5, 4.1)
    # It is recessed into the rounded back skin, so trim to the silhouette.
    back_panel = back_profile.intersect(outer)
    # A local internal pad retains 3 mm of white wall beneath the recessed
    # rear insert instead of leaving a thin unsupported white skin.
    shell = shell.fuse(back_blank(24.4, 3.0)).cut(back_profile)

    # Internal bottom reinforcement: a captive M3 hex nut is inserted from
    # inside before the shell halves close. Minimum bottom wall is 2.7 mm.
    neck_reinforcement = _cylinder(5.5, 5, (0, 0, 112), (0, 0, 1))
    shell = shell.fuse(neck_reinforcement)
    shell = shell.cut(_cylinder(1.65, 10, (0, 0, 110), (0, 0, 1)))
    nut = (cq.Workplane("XY", origin=(0, 0, 114.7))
           .polygon(6, 6.5).extrude(5).val())
    shell = shell.cut(nut)

    # Two short internal alignment dowels on the bottom edge. These guide the
    # shell halves and have 0.15 mm radial assembly clearance.
    front_mask = _box(140, 80, 100, (0, -40, 140))
    rear_mask = _box(140, 80, 100, (0, 40, 140))

    ear_shapes = []
    for side, tag in [(-1, "left"), (1, "right")]:
        # Axial removable ear pegs; drill the head before dividing its shell.
        shell = shell.cut(_cylinder(1.65, 6, (side * 34, 0, 140),
                                    (side, 0, 0)))
        housing = _cylinder(16, 4, (side * 39, 0, 140), (side, 0, 0))
        housing = housing.fuse(_ring_x(side, 16, 13, 43, 1))
        housing = housing.fuse(_cylinder(1.5, 3, (side * 36, 0, 140),
                                           (side, 0, 0)))
        ear_shapes.extend([
            (f"head_ear_{tag}_white", housing, WHITE,
             "Remove the ear before opening the white head shells; peg diameter 3 mm."),
            (f"head_ear_{tag}_outer_navy", _ring_x(side, 16.8, 16, 39.2, 4.8), NAVY,
             "0.8 mm outer navy outline, glued to white ear."),
            (f"head_ear_{tag}_navy_ring", _ring_x(side, 13, 10.7, 43, 1), NAVY,
             "Concentric ear insert."),
            (f"head_ear_{tag}_cyan_ring", _ring_x(side, 10.7, 8.7, 43, 1), CYAN,
             "Concentric ear insert."),
            (f"head_ear_{tag}_navy_center", _cylinder(8.7, 1,
              (side * 43, 0, 140), (side, 0, 0)), NAVY,
             "Solid navy ear centre disk."),
        ])

    antenna_shapes = []
    for side, tag in [(-1, "left"), (1, "right")]:
        p = cq.Vector(side * 32, 0, 163.8)
        q = cq.Vector(side * 35, 0, 174)
        v = q - p
        axis = v.normalized()
        stem = cq.Solid.makeCone(2.5, 1.6, v.Length, p, axis)
        # A 2.5 mm deep shank seats in a close-fitting recess. The same cone
        # clears both the white shell and the cyan ball, so solids never cross.
        clearance = cq.Solid.makeCone(2.65, 1.75, v.Length, p, axis)
        if cut_antenna_recesses:
            shell = shell.cut(clearance)
        ball = cq.Solid.makeSphere(5, cq.Vector(side * 35, 0, 175),
                                  angleDegrees1=-90, angleDegrees2=90)
        ball = ball.cut(clearance)
        antenna_shapes.extend([
            (f"head_antenna_{tag}_stem", stem, NAVY,
             "Glue into shell recess; upper end fits inside the cyan ball."),
            (f"head_antenna_{tag}_ball", ball, CYAN,
             "5 mm-radius sphere, maximum assembly height 180 mm."),
        ])

    front = shell.intersect(front_mask)
    rear = shell.intersect(rear_mask)
    for x in (-17, 17):
        front_tab = _box(6, 5, 6, (x, -2.5, 116.4))
        rear_tab = _box(6, 5, 6, (x, 2.5, 116.4))
        front = front.fuse(front_tab).fuse(
            _cylinder(1.5, 3.5, (x, 0, 116.7), (0, 1, 0)))
        rear = rear.fuse(rear_tab).cut(
            _cylinder(1.65, 4.0, (x, 0, 116.7), (0, 1, 0)))

    add("head_white_front_shell", front, WHITE,
        "3 mm shell; M3 swivel bore 3.3 mm; insert captive nut before closing. Front half has two alignment pegs.")
    add("head_white_rear_shell", rear, WHITE,
        "3 mm shell; alignment sockets have 0.15 mm radial clearance. Head opens at Y=0.")
    add("head_visor_navy", screen, NAVY,
        "Rounded 64 by 42 mm face plate; glue all face colour inserts to its flat front.")
    add("head_visor_cyan_bezel", bezel, CYAN,
        "1 mm-wide cyan rim, rear lip; glue into front head opening.")
    add("head_top_navy_panel", top_panel, NAVY,
        "Remove inset top cover before separating head shells.")
    add("head_back_navy_panel", back_panel, NAVY,
        "Tapered rear panel, supported by recessed white skin.")
    for entry in ear_shapes + antenna_shapes:
        add(*entry)

    # Eyes: four contiguous colour patches per eye, all supported by the navy
    # face plate, and two captive white highlights. No overlapping solids.
    detail_y, detail_depth = -26.0, 1.2
    for side, tag in [(-1, "left"), (1, "right")]:
        eye = _ellipse_xz(16, 18, detail_depth,
                          side * 16.5, detail_y, 143.5)
        iris = _ellipse_xz(11.0, 15.0, detail_depth,
                           side * 14.9, detail_y, 143.0).intersect(eye)
        pupil = _ellipse_xz(8.4, 11.6, detail_depth,
                            side * 14.5, detail_y, 144.0).intersect(iris)
        large_spark = _cylinder(1.35, detail_depth,
                               (side * 13.0, detail_y, 147.4), (0, -1, 0)).intersect(pupil)
        small_spark = _cylinder(0.60, detail_depth,
                               (side * 12.5, detail_y, 143.9), (0, -1, 0)).intersect(pupil)
        add(f"head_eye_{tag}_white", eye.cut(iris), WHITE,
            "White eye patch 1.2 mm deep, aligns to cyan iris.")
        add(f"head_eye_{tag}_cyan", iris.cut(pupil), CYAN,
            "Iris fitted into eye, 1.2 mm deep.")
        add(f"head_eye_{tag}_pupil", pupil.cut(large_spark).cut(small_spark), BLACK,
            "Dark pupil with small cavities for white highlights.")
        add(f"head_eye_{tag}_highlight_large", large_spark, WHITE,
            "Small 2.7 mm white highlight; use 0.08-0.12 mm layers.")
        add(f"head_eye_{tag}_highlight_small", small_spark, WHITE,
            "1.2 mm white highlight; useful optional tiny insert, or paint this detail.")

        brow = (cq.Workplane("XZ", origin=(side * 17, detail_y, 155.0))
                .moveTo(-6.5, 0).threePointArc((0, 2.9), (6.5, 0))
                .lineTo(6.5, -1.4).threePointArc((0, 1.1), (-6.5, -1.4))
                .close().extrude(1.0).val())
        add(f"head_brow_{tag}_cyan", brow, CYAN,
            "Curved cyan brow, 1 mm thick.")
        # The outside eyelashes flare upward from the eyes like the reference.
        lash_points = [(side * 23.3, 148.0), (side * 25.2, 148.5),
                       (side * 26.8, 150.0), (side * 25.8, 147.5),
                       (side * 24.0, 146.6)]
        lash = (cq.Workplane("XZ", origin=(0, detail_y, 0))
                .polyline(lash_points).close().extrude(0.9).val()).cut(eye)
        add(f"head_lash_{tag}_cyan", lash, CYAN,
            "Separate outward eyelash, glue to visor.")

    mouth = (cq.Workplane("XZ", origin=(0, detail_y, 0))
             .moveTo(-12, 132.5).threePointArc((0, 130.4), (12, 132.5))
             .threePointArc((9, 124.6), (0, 121.8))
             .threePointArc((-9, 124.6), (-12, 132.5))
             .close().extrude(detail_depth).val())
    teeth = (cq.Workplane("XZ", origin=(0, detail_y, 0))
             .moveTo(-10.9, 132.3).threePointArc((0, 130.4), (10.9, 132.3))
             .lineTo(9.5, 130.0).threePointArc((0, 128.1), (-9.5, 130.0))
             .close().extrude(detail_depth).val()).intersect(mouth)
    tongue = _ellipse_xz(14, 6.0, detail_depth, 0, detail_y, 123.1).intersect(mouth)
    add("head_smile_mouth_dark", mouth.cut(teeth).cut(tongue), BLACK,
        "Open smile with recesses for white teeth and coral tongue.")
    add("head_smile_teeth_white", teeth, WHITE,
        "Curved upper row of white teeth.")
    add("head_smile_tongue_coral", tongue, CORAL,
        "Coral tongue inset in lower smile.")

    return parts


def build_head():
    """Return the proportion-corrected 180 mm character head.

    Scale the visual shell and inserts 1.3 about the crown at Z=166. Neck
    hardware and antenna dimensions are rebuilt rather than scaled, because
    a visually scaled M3 bore would otherwise become an unusable 4.29 mm.
    """
    factor = 1.3
    offset = (0, 0, 166 * (1 - factor))
    # Omit obsolete antenna bores before scaling. This avoids rebuilding
    # coincident cone faces with white filler plugs at the head seam.
    original = _build_unscaled_head(cut_antenna_recesses=False)
    parts = []
    for item in original:
        if "_antenna_" in item["name"]:
            continue
        result = dict(item)
        result["shape"] = item["shape"].scale(factor).translate(offset)
        if "shell" in result["name"]:
            result["notes"] = (
                "3.9 mm shell; bottom Z95.8; M3 bore 3.3 mm. Captive-nut "
                "pocket AF5.89 at Z98.8..101.5, seat floor 3 mm and retaining "
                "roof 2.5 mm. Insert ISO4032 M3 nut sideways through open "
                "head seam Y=0 before closing shells. Use M3x16 with DIN433 "
                "washer and separate 0.3 mm PTFE/PET bearing washer below "
                "head; do not glue bearing surfaces. Alignment dowels 3.9 mm "
                "and sockets 4.29 mm. Remove ears and crown cover to open.")
        elif result["name"] == "head_visor_navy":
            result["notes"] = (
                "Rounded 83.2 by 54.6 mm face plate, 2.6 mm thick; "
                "glue face inserts to the flat front.")
        elif result["name"] == "head_visor_cyan_bezel":
            result["notes"] = "1.3 mm-wide cyan contour; glue rear lip into white opening."
        elif "_ear_" in result["name"] and "_white" in result["name"]:
            result["notes"] = "White ear with 3.9 mm removable axial peg; remove ear before opening head."
        elif "_highlight_small" in result["name"]:
            result["notes"] = "1.56 mm white highlight, 1.56 mm thick; glue carefully or paint."
        elif "_highlight_large" in result["name"]:
            result["notes"] = "3.51 mm white highlight, 1.56 mm thick."
        elif "_eye_" in result["name"]:
            result["notes"] = "Eye insert 1.56 mm thick, laid flat for printing and glued to visor."
        parts.append(result)

    by_name = {item["name"]: item for item in parts}
    front = by_name["head_white_front_shell"]["shape"]
    rear = by_name["head_white_rear_shell"]["shape"]
    front_mask = _box(180, 100, 150, (0, -50, 135))
    rear_mask = _box(180, 100, 150, (0, 50, 135))

    # Fill the scaled old bore/hex completely, then cut true M3 dimensions.
    # The new 8.2 mm boss leaves a 3 mm nut seat and a 2.5 mm retaining roof.
    # Its external bearing face remains Z95.8, preserving the 180 mm figure.
    boss = _cylinder(7.5, NECK_BOSS_TOP_Z - NECK_BOTTOM_Z,
                     (0, 0, NECK_BOTTOM_Z), (0, 0, 1))
    front = front.fuse(boss.intersect(front_mask))
    rear = rear.fuse(boss.intersect(rear_mask))
    bore = _cylinder(NECK_BORE_DIAMETER / 2, NECK_BOSS_TOP_Z - 94.0,
                     (0, 0, 94.5), (0, 0, 1))
    nut = (cq.Workplane("XY", origin=(0, 0, NECK_NUT_BOTTOM_Z))
           .polygon(6, NECK_NUT_VERTEX_DIAMETER)
           .extrude(NECK_NUT_POCKET_TOP_Z - NECK_NUT_BOTTOM_Z).val())
    front = front.cut(bore).cut(nut)
    rear = rear.cut(bore).cut(nut)

    for side, tag in [(-1, "left"), (1, "right")]:
        # Keep the entire mounting bore off Y=0. A cone lying exactly on the
        # shell seam can yield unreliable OCC classification after meshing
        # and BREP reimport even when the basic validity check succeeds.
        p = cq.Vector(side * 41.6, -4, 160.8)
        q = cq.Vector(side * 45.5, -4, 173.8)
        v = q - p
        axis = v.normalized()
        stem = cq.Solid.makeCone(2.5, 1.6, v.Length, p, axis)
        recess = cq.Solid.makeCone(2.65, 1.75, v.Length, p, axis)
        # Rotate the tool seam away from the sphere meridian. This changes
        # only surface parametrisation, not geometry or radial clearance.
        recess = recess.rotate(p.toTuple(), (p + axis).toTuple(), 25)
        front = front.cut(recess)
        rear = rear.cut(recess)
        # Extend the blind bore 0.4 mm beyond the stem cap for axial assembly
        # clearance, while keeping the same 0.15 mm radial cone clearance.
        axial = 0.4
        ball_recess = cq.Solid.makeCone(2.65, 1.75 - 0.9 * axial / v.Length,
                                        v.Length + axial, p, axis)
        ball_recess = ball_recess.rotate(p.toTuple(), (p + axis).toTuple(), 25)
        ball = cq.Solid.makeSphere(5, cq.Vector(side * 45.5, -4, 175),
                                  angleDegrees1=-90, angleDegrees2=90).cut(ball_recess)
        parts.extend([
            dict(name=f"head_antenna_{tag}_stem", shape=stem, color=NAVY,
                 group="head", notes="Tapered stem seats in rebuilt shell recess; glue cyan ball at upper end."),
            dict(name=f"head_antenna_{tag}_ball", shape=ball, color=CYAN,
                 group="head", notes="5 mm-radius ball at Z175; top of figure exactly Z180."),
        ])

    by_name["head_white_front_shell"]["shape"] = front
    by_name["head_white_rear_shell"]["shape"] = rear
    for item in parts:
        item["shape"] = item["shape"].clean()
        if not item["shape"].isValid() or item["shape"].Volume() <= 0:
            raise ValueError("Invalid scaled head component: " + item["name"])
    return parts


if __name__ == "__main__":
    result = build_head()
    print(f"Head: {len(result)} colour-separated components")
    for item in result:
        bb = item["shape"].BoundingBox()
        print(item["name"], round(item["shape"].Volume(), 3),
              item["shape"].isValid(),
              tuple(round(v, 2) for v in (bb.xlen, bb.ylen, bb.zlen)))
