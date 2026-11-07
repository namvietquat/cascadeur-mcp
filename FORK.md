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

## Rules kept
- Never work around the licence: FBX export stays licence-checked; no bulk joint dumps.
- Scripting stays opt-in; menu actions only by curated name or prefix allowlist (no File./Window./exit/dialogs).

## Lessons (measured, not assumed)
- Depths from `contacts` include each point's collision radius (~4.2 on UE5 Manny): judge the excess.
- `capture_viewport` output must be waited on until complete (size stable); the server does this.
- Setting keys past the animation size fails silently; core ops call `fit_animation_size_by_layers`.
- Pro-only: retargeting, AutoPhysics environment interaction, quadruped AutoPosing.
