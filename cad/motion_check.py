"""Check discrete rigid-joint poses against every stationary assembly component.

Read the final build's BREP cache; do not rebuild or modify the CAD.  A clear
sample is not a guarantee that the complete path to that sample is clear.
Run after cad/build.py: python3 cad/motion_check.py
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
from pathlib import Path

import cadquery as cq

from hardware import JOINT_AXES


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports"
VOLUME_TOLERANCE_MM3 = 0.01
BBOX_TOLERANCE_MM = 0.001

# Descendants rotate as a rigid assembly.  The current joint's own screw,
# washers and nut stay with its stationary parent, while the hardware at every
# downstream joint follows the moving link.  The neck is a rotor exception:
# its screw and captive nut rotate together with the head, sliding at washers;
# the captive hex nut must not rotate relative to its capture in the head.
# This also catches collisions with
# the opposite limb, torso, head, chest graphics and presentation base.
KINEMATICS = {
    "ombro_E": (["left_upper_arm", "left_forearm", "left_hand"],
                 ["cotovelo_E", "punho_E"]),
    "ombro_D": (["right_upper_arm", "right_forearm", "right_hand"],
                 ["cotovelo_D", "punho_D"]),
    "cotovelo_E": (["left_forearm", "left_hand"], ["punho_E"]),
    "cotovelo_D": (["right_forearm", "right_hand"], ["punho_D"]),
    "punho_E": (["left_hand"], []),
    "punho_D": (["right_hand"], []),
    "quadril_E": (["left_thigh", "left_shin", "left_boot"],
                  ["joelho_E", "tornozelo_E"]),
    "quadril_D": (["right_thigh", "right_shin", "right_boot"],
                  ["joelho_D", "tornozelo_D"]),
    "joelho_E": (["left_shin", "left_boot"], ["tornozelo_E"]),
    "joelho_D": (["right_shin", "right_boot"], ["tornozelo_D"]),
    "tornozelo_E": (["left_boot"], []),
    "tornozelo_D": (["right_boot"], []),
    "pescoco": (["head"], []),
}


def bounds_overlap(a, b):
    return (
        min(a.xmax, b.xmax) - max(a.xmin, b.xmin) > BBOX_TOLERANCE_MM
        and min(a.ymax, b.ymax) - max(a.ymin, b.ymin) > BBOX_TOLERANCE_MM
        and min(a.zmax, b.zmax) - max(a.zmin, b.zmin) > BBOX_TOLERANCE_MM
    )


def load_parts():
    path = OUT / "pecas.json"
    payload = path.read_bytes()
    rows = json.loads(payload)
    if len({p["name"] for p in rows}) != len(rows):
        raise ValueError("Duplicate component names in pecas.json")
    for row in rows:
        file = OUT / "BREP" / (row["name"] + ".brep")
        if not file.is_file():
            raise ValueError("Missing final-build BREP: " + str(file))
        row["shape"] = cq.Shape.importBrep(str(file))
        if abs(row["shape"].Volume() - row["volume_mm3"]) > 0.01:
            raise ValueError("Stale BREP or manifest: " + row["name"])
        if row["group"] == "hardware" and "joint" not in row:
            raise ValueError("Hardware needs joint metadata: " + row["name"])
        row["box"] = row["shape"].BoundingBox()
    hardware_joints = {p["joint"] for p in rows if p["group"] == "hardware"}
    missing = set(KINEMATICS) - hardware_joints
    if missing:
        raise ValueError("Run the updated cad/build.py first; hardware missing at "
                         + ", ".join(sorted(missing)))
    return rows, hashlib.sha256(payload).hexdigest()


def check_pose(moving, fixed, center, axis, angle):
    end = tuple(center[i] + axis[i] for i in range(3))
    collisions = []
    errors = []
    candidates = 0
    for part in moving:
        shape = (part["shape"] if angle == 0 else
                 part["shape"].rotate(center, end, angle))
        box = shape.BoundingBox()
        for other in fixed:
            if not bounds_overlap(box, other["box"]):
                continue
            candidates += 1
            try:
                common = shape.intersect(other["shape"])
                volume = abs(common.Volume()) if common.Solids() else 0.0
                if volume > VOLUME_TOLERANCE_MM3:
                    collisions.append({
                        "moving": part["name"],
                        "fixed": other["name"],
                        "moving_group": part["group"],
                        "fixed_group": other["group"],
                        "common_volume_mm3": round(volume, 6),
                    })
            except Exception as exc:
                # A failed boolean cannot be interpreted as a clear sample.
                errors.append({"moving": part["name"], "fixed": other["name"],
                               "error": str(exc)[:500]})
    non_base = [hit for hit in collisions if hit["fixed_group"] != "base"]
    return {
        "angle_deg_from_delivered_pose": angle,
        "collision_free_full_assembly": not collisions and not errors,
        "collision_free_without_base": not non_base and not errors,
        "collision_pairs": collisions,
        "boolean_errors": errors,
        "bbox_candidates_checked": candidates,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joints", nargs="+", choices=list(KINEMATICS),
                        help="Inspect only named joints; requires --output.")
    parser.add_argument("--output", type=Path,
                        help="Alternative report path (default exports/movimento_local.json).")
    args = parser.parse_args()
    if args.joints and not args.output:
        parser.error("A subset requires --output, preserving the complete report.")

    started = time.monotonic()
    parts, manifest_hash = load_parts()
    axes = {name: ((x, y, z), (0, 1, 0)) for name, x, y, z in JOINT_AXES}
    axes["pescoco"] = ((0, 0, 95.5), (0, 0, 1))
    selected = args.joints or list(KINEMATICS)
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Discrete rigid rotations of final-build BREP descendants against all stationary assembly components, including hardware and base.",
        "parts_manifest_sha256": manifest_hash,
        "parts": len(parts),
        "hardware_parts": sum(p["group"] == "hardware" for p in parts),
        "common_volume_tolerance_mm3": VOLUME_TOLERANCE_MM3,
        "bbox_overlap_tolerance_mm": BBOX_TOLERANCE_MM,
        "physical_test": False,
        "full_range_verified": False,
        "other_robot_components_checked": True,
        "base_checked": True,
        "sampling_does_not_certify_continuous_motion_between_angles": True,
        "simultaneous_joint_motion_checked": False,
        "own_joint_hardware_moves_with": "stationary parent",
        "neck_hardware_exception": "Neck screw and captive nut move together with the head as a locked threaded pair. The lower washer and circular sliding bearing stay with the body; rotation occurs at washer interfaces, not between nut and thread.",
        "downstream_joint_hardware_moves_with": "moving descendant assembly",
        "angle_sign_convention": "CadQuery positive rotation about global +Y; neck about global +Z. Zero is the delivered pose.",
        "base_removal_note": "The presentation base is stationary. Inclining a foot can intersect it; without-base flags report only removal of the base, not any other component.",
        "joints": [],
    }
    for name in selected:
        groups, hardware_joints = KINEMATICS[name]
        moving = [p for p in parts if p["group"] in groups or
                  (p["group"] == "hardware" and (p["joint"] in hardware_joints or
                   (name == "pescoco" and p["joint"] == "pescoco" and
                    p.get("kind") in ("screw", "nut"))))]
        if not moving:
            raise ValueError("No moving descendants found: " + name)
        moving_names = {p["name"] for p in moving}
        fixed = [p for p in parts if p["name"] not in moving_names]
        center, axis = axes[name]
        angles = [0, -15, 15, -30, 30] if name == "pescoco" else [0, -5, 5, -10, 10, -20, 20]
        joint = {
            "joint": name, "pivot_xyz_mm": center, "axis_xyz": axis,
            "moving_groups": groups,
            "moving_hardware_joints": hardware_joints,
            "own_joint_hardware_moves_with": (
                "screw and captive nut with head; washers/bearing with body"
                if name == "pescoco" else "stationary parent"),
            "moving_parts": sorted(moving_names),
            "stationary_parts": len(fixed), "tests": [],
        }
        print("Checking " + name + "...", flush=True)
        for angle in angles:
            sample = check_pose(moving, fixed, center, axis, angle)
            joint["tests"].append(sample)
            print(f"  {angle:+g} deg: {len(sample['collision_pairs'])} collisions; "
                  f"{len(sample['boolean_errors'])} boolean errors", flush=True)
        joint["clear_nonzero_sample_angles_full_assembly"] = [
            t["angle_deg_from_delivered_pose"] for t in joint["tests"]
            if t["angle_deg_from_delivered_pose"] and t["collision_free_full_assembly"]]
        joint["clear_nonzero_sample_angles_without_base"] = [
            t["angle_deg_from_delivered_pose"] for t in joint["tests"]
            if t["angle_deg_from_delivered_pose"] and t["collision_free_without_base"]]
        report["joints"].append(joint)
        report["elapsed_seconds"] = round(time.monotonic() - started, 2)
        # Write after every completed joint to preserve evidence during long checks.
        target = args.output or OUT / "movimento_local.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    report["all_13_joints_checked"] = len(report["joints"]) == 13
    report["all_tested_joints_have_a_collision_free_nonzero_sample"] = all(
        j["clear_nonzero_sample_angles_full_assembly"] for j in report["joints"])
    report["all_tested_joints_have_a_collision_free_nonzero_sample_without_base"] = all(
        j["clear_nonzero_sample_angles_without_base"] for j in report["joints"])
    report["zero_pose_collision_pairs"] = [
        dict(joint=j["joint"], **hit) for j in report["joints"]
        for t in j["tests"] if t["angle_deg_from_delivered_pose"] == 0
        for hit in t["collision_pairs"]]
    report["boolean_errors"] = [
        dict(joint=j["joint"], angle_deg=t["angle_deg_from_delivered_pose"], **err)
        for j in report["joints"] for t in j["tests"] for err in t["boolean_errors"]]
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {target} ({report['elapsed_seconds']} s)", flush=True)
    if report["zero_pose_collision_pairs"] or report["boolean_errors"]:
        raise SystemExit("Pose-zero collisions or boolean errors require review; see report.")


if __name__ == "__main__":
    main()
