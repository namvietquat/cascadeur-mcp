"""AI-animator extensions to the bridge operations (app side, runs inside Cascadeur).

Composite, file-based and verification operations built on the core
operations. Nothing here enables scripting or exports animation data in bulk:
sampling is limited to positions for evaluation, and FBX export still goes
through the licence-checked core operation.
"""

from __future__ import annotations

import json
import math

from .operations import context, file_path, frame_number, object_id

# Action IDs from Cascadeur's published action reference that are safe to call
# by ID (no app exit / file dialogs). Prefix allowlist.
ACTION_PREFIXES = (
    "Scene.Undo", "Scene.Redo", "Scene.Edit mode.", "Scene.Set key on change",
    "Timeline.", "View.", "AutoPhysicsTool.", "AutoPosingTool.", "BallisticTrajectoryTool.",
    "Copier.", "GhostTool.", "InbetweeningTool.", "MirrorTool.", "AttractorTool.",
    "TrajectoryTool.", "FixCollisionsTool.", "AnimationUnbakingTool.",
)
MAX_FILE_KEYFRAMES = 5000


def _sample(dispatch, state, objects, first, last, step=1):
    return dispatch("sample_motion", dict(objects=objects, first=first, last=last, step=step), state)


def _displacement(before, after):
    out = {}
    for a, b in zip(before["objects"], after["objects"]):
        d = [math.dist(p, q) for p, q in zip(a["positions"], b["positions"])]
        out[a["name"]] = dict(max_change=max(d, default=0.0), mean_change=sum(d) / max(len(d), 1))
    return out


def dispatch_ext(method, p, state, dispatch):
    if method == "animate_from_file":
        path = file_path(p["path"], state, exists=True, suffix={".json"})
        data = json.loads(path.read_text(encoding="utf-8"))
        args = data.get("arguments", data)
        kfs = args.get("keyframes") or []
        if not kfs or len(kfs) > MAX_FILE_KEYFRAMES:
            raise ValueError(f"Expected 1..{MAX_FILE_KEYFRAMES} keyframes in the file.")
        for kf in kfs:
            if not 1 <= len(kf.get("transforms", [])) <= 200:
                raise ValueError(f"Frame {kf.get('frame')} needs 1..200 transforms.")
        interp = p.get("interpolation") or args.get("interpolation", "BEZIER")
        updated = 0
        for i in range(0, len(kfs), 500):
            res = dispatch("animate_transforms", dict(keyframes=kfs[i:i + 500], interpolation=interp), state)
            updated += res.get("updated_values", 0) if isinstance(res, dict) else 0
        frames = [k["frame"] for k in kfs]
        return dict(path=str(path), keyframes=len(kfs), first=min(frames), last=max(frames),
                    updated_values=updated, interpolation=interp,
                    note="Rig solving can alter requested values. Sample motion and render to verify.")

    if method == "sample_motion_to_file":
        path = file_path(p["path"], state, overwrite=p.get("overwrite", False), suffix={".json"})
        res = _sample(dispatch, state, p["objects"], p["first"], p["last"], p.get("step", 1))
        path.write_text(json.dumps(res), encoding="utf-8")
        return dict(path=str(path), frames=len(res["frames"]),
                    objects={o["name"]: dict(path_length=round(o["path_length"], 3),
                                             max_step=round(o["max_step_distance"], 3)) for o in res["objects"]})

    if method == "center_of_mass":
        _, _, view, scene = context()
        mv = scene.model_viewer()
        ids = [o for o in mv.get_objects() if mv.get_object_type_name(o) == "Center of Mass"]
        if not ids:
            raise ValueError("No 'Center of Mass' object in this scene (rig has no physics model).")
        names = [str(i) for i in ids]
        res = _sample(dispatch, state, names, p["first"], p["last"], p.get("step", 1))
        if p.get("path"):
            path = file_path(p["path"], state, overwrite=p.get("overwrite", False), suffix={".json"})
            path.write_text(json.dumps(res), encoding="utf-8")
            res = dict(path=str(path), objects=[o["name"] for o in res["objects"]], frames=len(res["frames"]))
        return res

    if method == "run_action_verified":
        _, _, view, _ = context()
        if p["expected_scene"] != view.name():
            raise ValueError("Active scene changed; inspect before editing.")
        before = _sample(dispatch, state, p["watch"], p["first"], p["last"], p.get("step", 1))
        if p.get("action_id"):
            aid = p["action_id"]
            if not aid.startswith(ACTION_PREFIXES):
                raise ValueError("Action ID not in the allowlist: " + ", ".join(ACTION_PREFIXES))
            import csc

            csc.app.get_application().get_action_manager().call_action(aid)
        else:
            dispatch("run_action", dict(name=p["name"], expected_scene=p["expected_scene"]), state)
        after = _sample(dispatch, state, p["watch"], p["first"], p["last"], p.get("step", 1))
        diff = _displacement(before, after)
        changed = any(v["max_change"] > p.get("tolerance", 1e-4) for v in diff.values())
        return dict(action=p.get("action_id") or p.get("name"), changed=changed, displacement=diff,
                    note=("Measured before/after positions in the same bridge tick. Effects computed later by "
                          "the app (idle/physics solving) appear only on a later sample: re-sample before concluding "
                          "it did nothing."))

    if method == "health":
        import csc

        app = csc.app.get_application()
        out = dict(export_available=bool(app.is_export_available()))
        try:
            out["pro_features_available"] = bool(app.is_pro_features_available())
        except Exception:
            pass
        view = app.get_scene_manager().current_scene()
        out["scene"] = view.name() if view else None
        out["scene_path"] = view.get_path_name() if view else None
        out["scenes_open"] = len(app.get_scene_manager().scenes())
        return out

    raise ValueError("Unknown bridge operation: " + method)
