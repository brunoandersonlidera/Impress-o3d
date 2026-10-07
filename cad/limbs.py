"""Lidera robot limbs; dimensions in mm, global X/Y/Z as documented.

Each coloured cover is a separate printable, glue-on shell. The navy frames
carry the M3 pivots. Fingers are fixed, not articulated.
"""
from __future__ import annotations

import math
import cadquery as cq

WHITE = (0.94, 0.94, 0.91)
NAVY = (0.025, 0.055, 0.28)
CYAN = (0.00, 0.78, 0.96)

PIN_D = 3.3
TONGUE_T = 4.8
EAR_T = 3.0
EAR_Y = 4.2
JOINT_R = 6.0
WRIST_R = 4.5
COVER_GAP = 0.18


def _v(p):
    return cq.Vector(*p)


def _add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _mul(a, n):
    return tuple(n * x for x in a)


def _unit(a):
    n = math.sqrt(sum(x * x for x in a))
    return tuple(x / n for x in a)


def _fuse(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.fuse(shape)
    return result.clean()


def _cyl(a, b, radius):
    d = _sub(b, a)
    length = math.sqrt(sum(x * x for x in d))
    return cq.Solid.makeCylinder(radius, length, _v(a), _v(_unit(d)))


def _cy(p, radius, thickness):
    return cq.Solid.makeCylinder(
        radius, thickness, cq.Vector(p[0], p[1] - thickness / 2, p[2]), cq.Vector(0, 1, 0)
    )


def _xz_box(center, direction, width, depth, length):
    angle = math.degrees(math.atan2(direction[0], direction[2]))
    return cq.Solid.makeBox(
        width, depth, length, cq.Vector(-width / 2, -depth / 2, -length / 2)
    ).rotate((0, 0, 0), (0, 1, 0), angle).translate(center)


def _ellipsoid(center, axes, direction=(0, 0, 1)):
    matrix = cq.Matrix([
        [axes[0], 0, 0, 0], [0, axes[1], 0, 0],
        [0, 0, axes[2], 0], [0, 0, 0, 1],
    ])
    shape = cq.Solid.makeSphere(1, angleDegrees1=-90).transformGeometry(matrix)
    angle = math.degrees(math.atan2(direction[0], direction[2]))
    return shape.rotate((0, 0, 0), (0, 1, 0), angle).translate(center)


def _capsule(a, b, radius):
    return _fuse([
        _cyl(a, b, radius),
        cq.Solid.makeSphere(radius, _v(a), angleDegrees1=-90),
        cq.Solid.makeSphere(radius, _v(b), angleDegrees1=-90),
    ])


def _halfspace_y(front=True, y=0.0):
    return cq.Solid.makeBox(300, 150, 250, cq.Vector(-150, y - 150 if front else y, -20))


def _part(name, shape, color, group, notes):
    return dict(name=name, shape=shape.clean(), color=color, group=group, notes=notes)


def _frame(a, b, top_r=JOINT_R, end_r=JOINT_R, throat=8.5, clearance=0.0):
    """A central tongue, a continuous load path and the B twin-ear clevis."""
    d = _unit(_sub(b, a))
    xzd = _unit((d[0], 0, d[2]))
    c = clearance
    tongue = _cy(a, top_r + c, TONGUE_T + 2 * c)
    tail = _xz_box(_add(a, _mul(xzd, throat / 2)), xzd,
                   5.6 + 2 * c, TONGUE_T + 2 * c, throat + 2 * c)
    start = _add(a, _mul(d, throat - 1.5))
    end = _add(b, _mul(d, -(end_r + 2.1)))
    distance = sum((end[i] - start[i]) * d[i] for i in range(3))
    members = [tongue, tail]
    if distance > 0.15:
        members.append(_cyl(start, end, 3.3 + c))
    # The crossbar is radially clear of the child tongue by at least 0.6 mm.
    bridge_center = _add(b, _mul(xzd, -(end_r + 2.1)))
    bridge = _xz_box(bridge_center, xzd, 6.6 + 2 * c,
                     11.4 + 2 * c, 3.0 + 2 * c)
    ears = [bridge]
    rail_length = end_r + 3.6
    for sign in (-1, 1):
        p = (b[0], b[1] + sign * EAR_Y, b[2])
        ears.extend([
            _cy(p, end_r + c, EAR_T + 2 * c),
            _xz_box(_add(p, _mul(xzd, -rail_length / 2)), xzd,
                    4.8 + 2 * c, EAR_T + 2 * c, rail_length + 2 * c),
        ])
    clevis = _fuse(ears)
    # Short forearms need this relief so their far clevis cannot touch the
    # upstream parent's ears. It preserves the central structural tongue.
    clevis = clevis.cut(_cy(a, top_r + 0.25 + c, 40))
    members.append(clevis)
    solid = _fuse(members)
    hole_r = max(0.2, PIN_D / 2 - c)
    return solid.cut(_cy(a, hole_r, 50)).cut(_cy(b, hole_r, 50)).clean()


def _segment(parts, name, a, b, radius=8.4, end_r=JOINT_R,
             throat=8.5, upper_z_clip=None, stripe_at=0.67):
    group = name
    d = _unit(_sub(b, a))
    length = math.sqrt(sum(x * x for x in _sub(b, a)))
    center = _mul(_add(a, b), 0.5)
    core = _frame(a, b, end_r=end_r, throat=throat)
    parts.append(_part(name + "_frame", core, NAVY, group,
                       "Structural frame. A tongue 4.8 mm, B clevis gap 5.4 mm; M3 bores 3.3 mm along Y."))
    outer = _ellipsoid(center, (radius, radius * 1.02, length * 0.53), d)
    outer = outer.cut(_cy(a, JOINT_R + 0.55, 50))
    outer = outer.cut(_cy(b, end_r + 0.55, 50))
    if upper_z_clip is not None:
        outer = outer.intersect(cq.Solid.makeBox(300, 100, upper_z_clip + 20,
                                               cq.Vector(-150, -50, -20)))
    shell = outer.cut(_frame(a, b, end_r=end_r, throat=throat, clearance=COVER_GAP))
    stripe_center = _add(a, _mul(d, length * stripe_at))
    stripe_slab = _xz_box(stripe_center, d, 60, 60, 1.6)
    # Cyan is only a 1.1 mm surface inlay. The white shell continues underneath,
    # so one cosmetic stripe does not split a half-cover into loose fragments.
    inner_skin = _ellipsoid(center, (radius - 1.1, radius * 1.02 - 1.1,
                                      length * 0.53 - 1.1), d)
    stripe = shell.intersect(stripe_slab).cut(inner_skin)
    white = shell.cut(stripe)
    for material, shape, color in (("white", white, WHITE), ("cyan", stripe, CYAN)):
        for front in (True, False):
            half = shape.intersect(_halfspace_y(front, center[1]))
            if half.Volume() > 0.02:
                parts.append(_part(name + "_" + material + ("_front" if front else "_back"),
                                   half, color, group,
                                   "Open half-cover; glue around the structural frame. Nominal cavity allowance 0.18 mm."))


def _hand(parts, name, wrist, palm_center, wave):
    group = name
    r = WRIST_R
    direction = _unit((palm_center[0] - wrist[0], 0, palm_center[2] - wrist[2]))
    palm_axes = (8.3, 6.2, 8.6) if wave else (6.3, 4.4, 6.5)
    palm = _ellipsoid(palm_center, palm_axes)
    palm = palm.cut(_cy(wrist, r + 0.3, 45))
    tongue = _cy(wrist, r, TONGUE_T)
    tail = _xz_box(_add(wrist, _mul(direction, 4.0)), direction, 5.2, TONGUE_T, 8.0)
    fingers = []
    cuffs = []
    if wave:
        # The reference has three upright fingers plus an inward thumb.
        specs = [
            ((-59.0, -0.4, 123.0), (-61.0, -0.9, 126.5)),
            ((-54.8, -0.3, 125.0), (-56.0, -0.8, 129.5)),
            ((-50.5, -0.3, 125.4), (-50.5, -0.8, 129.0)),
            ((-45.0, -0.5, 116.0), (-45.0, -1.0, 120.0)),
        ]
    else:
        specs = [
            ((25.0, -6.5, 75.0), (23.8, -6.8, 72.0)),
            ((27.5, -7.0, 74.0), (26.4, -7.3, 70.8)),
            ((30.0, -7.0, 74.1), (29.3, -7.3, 71.0)),
            ((24.5, -5.7, 79.2), (23.2, -6.6, 77.0)),
        ]
    for index, (a, b) in enumerate(specs):
        # Fixed continuous finger cores, bulbous navy fingertips, white cuffs.
        d = _unit(_sub(b, a))
        finger = _capsule(a, b, 2.25)
        fingertip = cq.Solid.makeSphere(2.5, _v(b), angleDegrees1=-90)
        fingers.extend((finger, fingertip))
        cuff_end = _add(a, _mul(d, 2.1))
        cuff = _cyl(a, cuff_end, 3.25).cut(_cyl(_add(a, _mul(d, -0.5)),
                                              _add(cuff_end, _mul(d, 0.5)), 2.43))
        cuffs.append((index, cuff))
    body = _fuse([palm, tongue, tail] + fingers)
    body = body.cut(_cy(wrist, PIN_D / 2, 45))
    # Cyan palm ring is a real, flush separate inlay, not a displayed decal.
    front_y = palm_center[1] - palm_axes[1] + 1.5
    disk = _cy(palm_center, 4.35 if wave else 3.35, 40)
    inner = _cy(palm_center, 3.05 if wave else 2.25, 45)
    ring = body.intersect(disk.cut(inner)).intersect(_halfspace_y(True, front_y))
    body = body.cut(ring)
    parts.append(_part(name + "_navy", body, NAVY, group,
                       "Four fixed digits (three fingers and a thumb); wrist tongue radius 4.5 mm, thickness 4.8 mm, Y-axis M3 bore 3.3 mm."))
    if ring.Volume() > 0.05:
        parts.append(_part(name + "_palm_cyan", ring, CYAN, group,
                           "Flush palm inlay; glue to the hand."))
    # Merge touching cuffs into glove shells, avoiding interpenetrating separate
    # white rings between adjacent fingers. Split disconnected thumb patches.
    glove = _fuse([shape for _, shape in cuffs]).cut(body).cut(ring)
    plane_y = sum((a[1] + b[1]) / 2 for a, b in specs) / len(specs)
    for front in (True, False):
        half = glove.intersect(_halfspace_y(front, plane_y))
        for index, solid in enumerate(half.Solids()):
            if solid.Volume() > 0.15:
                parts.append(_part(name + "_glove_white_" + ("front" if front else "back")
                                   + "_" + str(index + 1), solid, WHITE, group,
                                   "Open fixed-digit glove patch, nominal cuff thickness 0.82 mm; glue after printing."))


def _boot(parts, name, x):
    group = name
    pivot = (x, 0, 17.25)
    sole = (cq.Workplane("XY").center(x, -4.5).rect(25.6, 34.0).extrude(3.0)
            .edges("|Z").fillet(4.6).val())
    tongue = _cy(pivot, JOINT_R, TONGUE_T)
    tail = _xz_box((x, 0, 13.0), (0, 0, 1), 5.6, TONGUE_T, 8.0)
    post = _cyl((x, 0, 3), (x, 0, 11), 3.3)
    structural = _fuse([sole, tongue, tail, post]).cut(_cy(pivot, PIN_D / 2, 50))
    parts.append(_part(name + "_sole_and_joint", structural, NAVY, group,
                       "Integral flat sole and ankle tongue. M3 bore 3.3 mm along Y; sole z0..3 mm."))
    # A dome with its widest section at the sole reproduces the broad boots
    # in the artwork; a full centred oval would leave an oversized sole flange.
    boot = _ellipsoid((x, -4.5, 3.18), (12.25, 16.0, 14.0))
    boot = boot.intersect(cq.Solid.makeBox(50, 60, 30, cq.Vector(x - 25, -30, 3.18)))
    boot = boot.cut(_cy(pivot, JOINT_R + 0.5, 45))
    cavity = _fuse([_cy(pivot, JOINT_R + COVER_GAP, TONGUE_T + 2 * COVER_GAP),
                    _xz_box((x, 0, 13.0), (0, 0, 1), 5.6 + 2 * COVER_GAP,
                            TONGUE_T + 2 * COVER_GAP, 8.0 + 2 * COVER_GAP),
                    _cyl((x, 0, 2.5), (x, 0, 11.3), 3.3 + COVER_GAP)])
    boot = boot.cut(cavity)
    toe_tool = cq.Solid.makeBox(60, 30, 50, cq.Vector(x - 30, -40, -5))
    toe = boot.intersect(toe_tool)
    white = boot.cut(toe_tool)
    # A thin cyan stripe under the ankle identifies the colour seen in the art.
    stripe_tool = cq.Solid.makeBox(60, 60, 1.6, cq.Vector(x - 30, -30, 11.4))
    stripe = white.intersect(stripe_tool).cut(_ellipsoid((x, -4.5, 3.18), (11.15, 14.9, 12.9)))
    white = white.cut(stripe)
    parts.append(_part(name + "_toe_navy", toe, NAVY, group,
                       "Separate rounded front toe cap; glue above the flat sole."))
    for material, shape, color in (("white", white, WHITE), ("cyan", stripe, CYAN)):
        # Split at x through the boot centre so the covers install around ankle post.
        for side in (-1, 1):
            clip = cq.Solid.makeBox(50, 70, 45,
                                    cq.Vector(x - 50 if side < 0 else x, -35, -5))
            half = shape.intersect(clip)
            if half.Volume() > 0.02:
                parts.append(_part(name + "_" + material + ("_left" if side < 0 else "_right"),
                                   half, color, group, "Open boot half-cover, cavity allowance 0.18 mm; glue onto sole."))


def _bbox_overlap(a, b):
    if not a.Solids() or not b.Solids():
        return False
    a, b = a.BoundingBox(), b.BoundingBox()
    return (min(a.xmax, b.xmax) - max(a.xmin, b.xmin) > 0.01 and
            min(a.ymax, b.ymax) - max(a.ymin, b.ymin) > 0.01 and
            min(a.zmax, b.zmax) - max(a.zmin, b.zmin) > 0.01)


def _frame_clearance(name, fallback):
    wrist_left = (-51 - 6 * math.cos(math.radians(12)) - 20 * math.sin(math.radians(12)),
                  0, 69.75 - 6 * math.sin(math.radians(12)) + 20 * math.cos(math.radians(12)))
    endpoints = {
        "left_upper_arm_frame": ((-28, 0, 84.75), (-51, 0, 69.75), JOINT_R),
        "left_forearm_frame": ((-51, 0, 69.75), wrist_left, WRIST_R),
        "right_upper_arm_frame": ((28, 0, 84.75), (43, 0, 66.75), JOINT_R),
        "right_forearm_frame": ((43, 0, 66.75), (31, -1, 59.75), WRIST_R),
    }
    if name in endpoints:
        a, b, r = endpoints[name]
        return _frame(a, b, end_r=r, clearance=0.2)
    # Legs are straight in the supplied pose and did not need mutual relief.
    return fallback


def _upper_arm_envelope(group):
    a, b = (((-28, 0, 84.75), (-51, 0, 69.75)) if group == "left_upper_arm" else
            ((28, 0, 84.75), (43, 0, 66.75)))
    d = _unit(_sub(b, a))
    length = math.sqrt(sum(x * x for x in _sub(b, a)))
    shape = _ellipsoid(_mul(_add(a, b), .5), (8.6, 8.4 * 1.02 + .2, length * .53 + .2), d)
    # Leave the hinge opening clear while providing 0.2 mm outward skin relief.
    return shape.cut(_cy(a, JOINT_R + .35, 50)).cut(_cy(b, JOINT_R + .35, 50))


def _relieve_pose(parts):
    """Clear static elbow/wrist creases, preserving each main frame.

    This validates the delivered pose only. It does not establish full angular
    motion limits. Small cosmetic patches are split into physical components.
    """
    frames = [p for p in parts if p["name"].endswith("_frame") or
              p["name"].endswith("_sole_and_joint")]
    tools = {}
    for p in parts:
        if p in frames:
            continue
        for frame in frames:
            if p["group"] == frame["group"] or not _bbox_overlap(p["shape"], frame["shape"]):
                continue
            collision = p["shape"].intersect(frame["shape"]).Volume()
            if collision > 0.005:
                key = frame["name"]
                if key not in tools:
                    tools[key] = _frame_clearance(key, frame["shape"])
                p["shape"] = p["shape"].cut(tools[key]).clean()
                p["notes"] += " Static relief against adjacent frame; 0.2 mm parametric allowance."
    # The two elbow folds otherwise place cosmetic biceps and forearm covers
    # in the same volume. Trim only child covers, retaining the rigid frames.
    for parent, child in [("left_upper_arm", "left_forearm"),
                          ("right_upper_arm", "right_forearm")]:
        downstream = [p for p in parts if p["group"] == child and p not in frames]
        tool = _upper_arm_envelope(parent)
        for q in downstream:
            if _bbox_overlap(tool, q["shape"]):
                q["shape"] = q["shape"].cut(tool).clean()
                q["notes"] += " Elbow crease relieved for the displayed pose."
    # A 0.08 mm3 palm-edge contact remained just outside the original 5.05 mm
    # wrist pocket. A 5.45 mm pocket provides radial clearance while retaining
    # every structural wrist tongue and clevis exactly as designed.
    left_wrist = (-51 - 6 * math.cos(math.radians(12)) - 20 * math.sin(math.radians(12)),
                  0, 69.75 - 6 * math.sin(math.radians(12)) + 20 * math.cos(math.radians(12)))
    for p in parts:
        if p["group"] in ("left_forearm", "right_forearm") and p not in frames:
            wrist = left_wrist if p["group"] == "left_forearm" else (31, -1, 59.75)
            p["shape"] = p["shape"].cut(_cy(wrist, 5.45, 50)).clean()
    result = []
    for p in parts:
        if p in frames or p["name"].endswith("_navy"):
            solids = p["shape"].Solids()
            if len(solids) != 1:
                raise ValueError("Disconnected structural member after relief: " + p["name"])
            p["shape"] = solids[0]
            result.append(p)
        else:
            solids = [s for s in p["shape"].Solids() if s.Volume() > 0.5]
            for i, solid in enumerate(solids):
                q = dict(p, shape=solid)
                if len(solids) > 1:
                    q["name"] += "_patch_" + str(i + 1)
                result.append(q)
    return result


def build_limbs():
    parts = []
    _segment(parts, "left_upper_arm", (-28, 0, 103), (-51, 0, 88), radius=8.4)
    forearm_start = len(parts)
    _segment(parts, "left_forearm", (-43, 0, 88), (-49, 0, 108), radius=8.8,
             end_r=WRIST_R, stripe_at=0.68)
    _hand(parts, "left_hand", (-49, 0, 108), (-52, 0, 119), True)
    for p in parts[forearm_start:]:
        p["shape"] = p["shape"].translate((-8, 0, 0))
    _segment(parts, "right_upper_arm", (28, 0, 103), (43, 0, 85), radius=8.4)
    _segment(parts, "right_forearm", (43, 0, 85), (31, -1, 78), radius=8.5,
             end_r=WRIST_R, stripe_at=0.60)
    _hand(parts, "right_hand", (31, -1, 78), (28, -4, 77), False)
    for p in parts:
        p["shape"] = p["shape"].translate((0, 0, -18.25))
        if p["group"] in ("left_forearm", "left_hand"):
            p["shape"] = p["shape"].rotate((-51, 0, 69.75), (-51, 1, 69.75), -12)
    for side, sign in (("left", -1), ("right", 1)):
        _segment(parts, side + "_thigh", (sign * 14, 0, 54.75), (sign * 15, 0, 34.5),
                 radius=8.8, throat=12.5, upper_z_clip=44.25, stripe_at=0.65)
        _segment(parts, side + "_shin", (sign * 15, 0, 34.5), (sign * 15, 0, 17.25),
                 radius=8.6, stripe_at=0.62)
        _boot(parts, side + "_boot", sign * 15)
    return _relieve_pose(parts)


if __name__ == "__main__":
    items = build_limbs()
    bad = []
    for item in items:
        shape = item["shape"]
        volume = shape.Volume()
        solids = len(shape.Solids())
        if not shape.isValid() or volume <= 0:
            bad.append(item["name"])
        print(item["name"], "valid", shape.isValid(), "volume", round(volume, 3), "solids", solids)
    print("PARTS", len(items), "INVALID", bad)
