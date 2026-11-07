"""AI-animator extensions: tool surface, allowlist, workspace guards, Windows status races."""

import time
import uuid
from pathlib import Path

import pytest

from cascadeur_mcp import actions, app_bridge, extensions, server
from cascadeur_mcp.bridge import Bridge

EXTENSION_TOOLS = {
    "cascadeur_health",
    "cascadeur_animate_from_file",
    "cascadeur_sample_motion_to_file",
    "cascadeur_center_of_mass",
    "cascadeur_run_action_verified",
    "cascadeur_contacts",
    "cascadeur_autoposing",
    "cascadeur_inbetweening",
    "cascadeur_render_sheet",
}


@pytest.fixture
def bridge(tmp_path):
    directory, workspace = tmp_path / "bridge", tmp_path / "workspace"
    directory.mkdir()
    workspace.mkdir()
    app_bridge.atomic_json(
        directory / "status.json",
        dict(
            version="0.1.0",
            protocol=1,
            pid=1,
            instance=uuid.uuid4().hex,
            heartbeat=time.time(),
            workspace=str(workspace),
            allow_scripts=False,
        ),
    )
    return Bridge(directory, workspace)


async def test_extension_tools_registered(bridge):
    names = {t.name for t in await server.create_server(bridge).list_tools()}
    assert EXTENSION_TOOLS <= names
    assert "cascadeur_run_script" not in names


async def test_render_sheet_rejects_directory_outside_workspace(bridge, tmp_path):
    s = server.create_server(bridge)
    with pytest.raises(Exception, match="inside the workspace"):
        await s.call_tool(
            "cascadeur_render_sheet",
            dict(directory=str(tmp_path / "elsewhere"), target="pelvis", frames=[0]),
        )
    assert not (tmp_path / "elsewhere").exists()


def test_status_retries_transient_permission_error(bridge, monkeypatch):
    real = Path.read_text
    calls = {"n": 0}

    def flaky(self, *a, **k):
        if self.name == "status.json" and calls["n"] < 2:
            calls["n"] += 1
            raise PermissionError("being replaced")
        return real(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", flaky)
    assert bridge.status()["protocol"] == 1
    assert calls["n"] == 2


def test_allowlist_blocks_dangerous_prefixes():
    for bad in ("File.Exit", "File.Export.Fbx", "Window.Preferences", "Scripts.Run"):
        assert not bad.startswith(extensions.ACTION_PREFIXES)
    for ok in (
        "Timeline.Create cycle",
        "TweenMachine.Attract to next position.Selected frames",
    ):
        assert ok.startswith(extensions.ACTION_PREFIXES)


def test_curated_actions_are_unique_and_allowlisted_or_reviewed():
    ids = [a["id"] for a in actions.ACTIONS.values()]
    assert len(ids) == len(set(ids))
    assert len(actions.ACTIONS) >= 61
