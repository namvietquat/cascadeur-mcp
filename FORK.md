# Fork notes (namvietquat/cascadeur-mcp)

Upstream: https://github.com/gprethesh/cascadeur-mcp (MIT). This fork adds what an automated
animation pipeline ("AI Animator": Cascadeur -> UE5 Control Rig / Blender -> FBX) needed.
Work happens on branch `ai-animator-extensions`; keep `origin` = upstream for pulls.

## Added (all verified live on Cascadeur 2026.2.3, free licence)
| Tool | Why |
|---|---|
| `cascadeur_health` | licence (`export_available`) + open scenes in one call |
| `cascadeur_animate_from_file` | big plans (<=5000 keyframes) from a workspace JSON instead of chat payloads |
| `cascadeur_sample_motion_to_file` | full trajectories to disk, summary back |
| `cascadeur_center_of_mass` | true physics CoM for balance checks |
| `cascadeur_run_action_verified` | run curated/allowlisted action IDs and measure before/after |
| `cascadeur_contacts` | Cascadeur's own contact solver (FulcrumCollisionInfo): fulcrum/touch/collision, penetration |
| `cascadeur_autoposing` | honest probe: add/update(session) from a script moves nothing (2026.1 and 2026.2.3) |
| `cascadeur_inbetweening` | AI inbetweening flag |
| `cascadeur_render_sheet` | frames x angles contact sheet that follows the character |

Curated actions: 46 -> 61 (cycles, interval fulcrum/tangents, mirror, Tween Machine, ballistic rotation).

## Fixes
- Windows: `status.json` read racing the app's atomic replace raised PermissionError and was reported as
  "bridge is not connected"; now retried briefly (`bridge.status`).
- Windows: symlink test is skipped where symlinks need admin rights.
- Lint: extensions are ruff-clean (CI runs `ruff check` + pytest on 3.11-3.13).

## Which actions really work from a script (measured 2026-11-07, Cascadeur 2026.2.3, free licence)
Probe: `ai_animator.probe_actions` on a copy of a 22-frame run (all Points + frames 3-8 selected),
`run_action_verified` before/after, re-sampled after 2 s and 10 s, then undo (all restored).

| Action | Effect from script | Measured gain on walk / run (evaluator + Cascadeur contacts) |
|---|---|---|
| `View.FixFoot` | yes (feet up to 1.5 cm) | run: toe penetration 0.0109 -> 0.0009 L, smoother; walk: re-crouches stance knee (score 90 -> 75). Accept only if the score holds. |
| `TweenMachine.Attract to {interpolation,average,inertial,previous,next} position.{Selected frames,Current frame}` | yes (0.5-2.5 cm) | interpolation/average: max accel -4 % (walk), -13 % (run), no new issues; previous/next pull poses, not a smoother |
| `View.Animation unbaking` | yes (3.3 cm) | changes keys/interpolation; not evaluated as a polish |
| `View.FixFoot_KeepKeyFrames` | no change on a keyed-every-frame clip | - |
| `AutoPhysicsTool.Switch Auto Physics` / `Set priority frame` / `Switch Frozen Auto Physics` | **no change** (even after 10 s) | - |
| `AutoPhysicsTool.Snap to Auto Physics` | error "No working Autophysics" | - |
| `BallisticTrajectoryTool.Add ballistic trajectory` | no change | - |
| `View.AutoInterpolation_Interpolations`, `Timeline.Create cycle` | no change on this clip | - |
| `AutoPosingTool.add/update(session)` (API) | no change | - |

AutoPhysics and AutoPosing appear to need the interactive UI; they are not usable headless here.

## Rules kept
- Never work around the licence: FBX export stays licence-checked; no bulk joint dumps.
- Scripting stays opt-in; menu actions only by curated name or prefix allowlist (no File./Window./exit/dialogs).

## Lessons (measured, not assumed)
- Depths from `contacts` include each point's collision radius (~4.2 on UE5 Manny): judge the excess.
- `capture_viewport` output must be waited on until complete (size stable); the server does this.
- Setting keys past the animation size fails silently; core ops call `fit_animation_size_by_layers`.
- Pro-only: retargeting, AutoPhysics environment interaction, quadruped AutoPosing.
