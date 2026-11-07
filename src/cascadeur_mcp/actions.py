"""Curated animation actions from Cascadeur's published action ID reference.
These commands have no completion acknowledgement; always verify their result.
https://cascadeur.com/help/category/301
"""

ACTIONS = {}


def group(category, values):
    for name, action_id in values.items():
        ACTIONS[name] = {"id": action_id, "category": category}


group("history", {"undo": "Scene.Undo", "redo": "Scene.Redo"})
group(
    "physics",
    {
        "physics_preview_toggle": "AutoPhysicsTool.Switch Auto Physics",
        "physics_snap": "AutoPhysicsTool.Snap to Auto Physics",
        "physics_priority_frame": "AutoPhysicsTool.Set priority frame",
        "physics_freeze_toggle": "AutoPhysicsTool.Switch Frozen Auto Physics",
        "show_fulcrum_points": "AutoPhysicsTool.Show all fucrum points",
        "clean_foot_contacts": "View.FixFoot",
        "clean_foot_contacts_keep_keys": "View.FixFoot_KeepKeyFrames",
        "add_ballistic_trajectory": "BallisticTrajectoryTool.Add ballistic trajectory",
        "snap_centers_of_mass": "BallisticTrajectoryTool.Snap centers of mass to selected trajectory",
        "ballistic_ghosts_toggle": "BallisticTrajectoryTool.Switch ballistic ghosts",
    },
)
group(
    "posing",
    {
        "autoposing_toggle": "AutoPosingTool.AutoPosing",
        "autoposing_update": "AutoPosingTool.Update",
        "autoposing_unlock": "AutoPosingTool.AutoUnlock",
        "autoposing_lock_toggle": "AutoPosingTool.SwitchLock",
        "show_fingers_toggle": "AutoPosingTool.SwitchFingersDrawing",
        "edit_current_frame": "Scene.Edit mode.Current frame",
        "edit_selected_interval": "Scene.Edit mode.Selection",
        "set_key_on_change": "Scene.Set key on change",
    },
)
group(
    "animation",
    {
        "unbake_animation": "View.Animation unbaking",
        "auto_interpolation_keys": "View.AutoInterpolation_Keys",
        "auto_interpolation_intervals": "View.AutoInterpolation_Interpolations",
        "retarget_copy": "View.Retargeting_Copy",
        "retarget_paste": "View.Retargeting_Paste",
        "play_toggle": "Timeline.Play",
        "next_key": "Timeline.Next key frame",
        "previous_key": "Timeline.Previous key frame",
        "create_cycle": "Timeline.Create cycle",
        "create_cycle_with_offsets": "Timeline.Create cycle with position and rotation offsets",
        "remove_cycles": "Timeline.Remove cycles",
        "key_fk": "Timeline.Change to FK key",
        "key_ik": "Timeline.Change to IK key",
        "key_fulcrum": "Timeline.Change to fulcrum key",
        "copy_pose": "Copier.Copy",
        "paste_pose": "Copier.Paste",
        "copy_interval": "Copier.Copy interval",
        "paste_interval": "Copier.Paste interval",
    },
)
group(
    "review",
    {
        "center_camera": "View.Center camera",
        "silhouette_toggle": "View.Silhouette mode",
        "ghost_keyframes": "GhostTool.Keyframe ghosts",
        "ghost_neighbors": "GhostTool.Neighbor frame ghosts",
        "ghost_disable": "GhostTool.Disable ghost",
        "show_graph_editor": "Window.Graph editor",
        "show_event_log": "Window.Event log",
        "show_physics_settings": "Window.Physics settings",
    },
)


# Added from the official action ID reference (https://cascadeur.com/help/category/301).
group(
    "cycles",
    {
        "create_cycle_with_position_offset": "Timeline.Create cycle with position offset",
        "resize_cycles": "Timeline.Resize cycles",
    },
)
group(
    "interval",
    {
        "fulcrum_key_on_interval": "Timeline.Change to fulcrum key on interval",
        "clear_custom_tangents_on_interval": "Timeline.Clear custom tangents on selected interval",
        "inbetween_interpolation_switch": "Scene.Inbetween interpolation switcher",
        "autoposing_lock_on_interval": "AutoPosingTool.SwitchLockOnInterval",
    },
)
group(
    "mirror",
    {
        "mirror_pelvis_position": "MirrorTool.Mirror pelvis position",
        "mirror_plane_yz": "MirrorTool.Planes.YZ",
    },
)
group(
    "tween",
    {
        "tween_to_previous": "TweenMachine.Attract to previous position.Selected frames",
        "tween_to_next": "TweenMachine.Attract to next position.Selected frames",
        "tween_to_interpolation": "TweenMachine.Attract to interpolation position.Selected frames",
        "tween_to_average": "TweenMachine.Attract to average position.Selected frames",
        "tween_inertial": "TweenMachine.Attract to inertial position.Selected frames",
    },
)
group(
    "ballistic",
    {
        "ballistic_fix_rotation_frame": "BallisticTrajectoryTool.Set fixation frame for free rotation",
        "ballistic_snap_orientation": "BallisticTrajectoryTool.Snap orientation to the ghosts of free rotation",
    },
)
