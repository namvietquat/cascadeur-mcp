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
    "TrajectoryTool.", "FixCollisionsTool.", "AnimationUnbakingTool.", "TweenMachine.", "Visible.AutoPhysics",
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

    if method == "contacts":
        # Cascadeur's own physics view of ground contact (same API as the bundled
        # ml/editable_animation.py): fulcrum = planted support point, touch = touching,
        # collision info carries penetration depth. Read-only.
        import csc

        _, _, view, scene = context()
        first, last = frame_number(p["first"]), frame_number(p["last"])
        if last < first or last - first > 2000:
            raise ValueError("Expected 0..2000 frames.")
        bv = scene.behaviour_viewer()
        cms = bv.get_behaviours("CenterOfMass")
        if not cms:
            raise ValueError("No CenterOfMass behaviour: the rig has no physics model.")
        rbs = bv.get_behaviour_reference_range(cms[0], "rigid_bodies")
        info = csc.tools.FulcrumCollisionInfo(first, last, scene, csc.tools.StaticPointsTypes(scene, rbs))
        mv = scene.model_viewer()
        names = {}

        def nm(oid):
            if oid not in names:
                names[oid] = mv.get_object_name(oid)
            return names[oid]

        def per_object(frames_to_ids):
            out = {}
            for f, ids in frames_to_ids.items():
                for oid in ids:
                    out.setdefault(nm(oid), []).append(int(f))
            return {k: sorted(v) for k, v in sorted(out.items())}

        res = dict(first=first, last=last, fulcrum=per_object(info.get_fulcrum_points()),
                   touch=per_object(info.get_touch_points()), collision=per_object(info.get_collision_points()))
        deepest = {}
        for f, objs in info.get_frame_collision_info_points().items():
            for oid, ci in objs.items():
                d = ci.penetration_depth
                d = float(d() if callable(d) else d)
                if d > deepest.get(nm(oid), (0.0, None))[0]:
                    deepest[nm(oid)] = (d, int(f))
        res["max_penetration"] = {k: dict(depth=round(v[0], 4), frame=v[1]) for k, v in sorted(deepest.items())}
        res["note"] = "Contacts as Cascadeur's physics sees them; compare with your evaluator's height-based contacts."
        return res

    if method == "autoposing":
        # AutoPosingTool.add/update(session) as used by the bundled rig_mode/off.py.
        # Measured before/after: earlier experience (Cascadeur 2026.1) saw update() change nothing.
        import csc

        _, _, view, scene = context()
        if p["expected_scene"] != view.name():
            raise ValueError("Active scene changed; inspect before editing.")
        op = p["op"]
        if op not in ("add", "update"):
            raise ValueError("op must be 'add' or 'update'.")
        tool = csc.app.get_application().get_tools_manager().get_tool("AutoPosingTool").editor(view)
        watch = p.get("watch") or []
        frame = scene.get_current_frame()
        before = _sample(dispatch, state, watch, p["first"], p["last"]) if watch else None
        ok = scene.modify_with_session("MCP AutoPosing " + op,
                                       lambda model, update, sc, session: getattr(tool, op)(session))
        out = dict(op=op, modify_ok=bool(ok), frame=frame)
        if watch:
            diff = _displacement(before, _sample(dispatch, state, watch, p["first"], p["last"]))
            out.update(changed=any(v["max_change"] > 1e-4 for v in diff.values()), displacement=diff)
        return out

    if method == "inbetweening":
        import csc

        _, _, view, _ = context()
        tool = csc.app.get_application().get_tools_manager().get_tool("InbetweeningTool").editor(view)
        if p.get("enabled") is not None:
            tool.set_update_parameter(bool(p["enabled"]))
        return dict(update_enabled=bool(tool.get_update_parameter()),
                    note="Keys with interpolation 'AI' are inbetweened by Cascadeur's model when enabled.")

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
