"""Validate a credential-free isolated OpenClaw profile, without restarting any Gateway."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def isolated_config(root):
    return {
        "gateway": {"mode": "local", "bind": "loopback", "port": 28789},
        "agents": {"defaults": {"workspace": str(Path(root) / "workspace")}},
        "channels": {},
        "plugins": {"enabled": False},
    }


def verify(binary):
    with tempfile.TemporaryDirectory(prefix="fleet-openclaw-") as temporary:
        root = Path(temporary)
        config = root / "openclaw.json"
        config.write_text(json.dumps(isolated_config(root)))
        env = {k: os.environ[k] for k in ("PATH", "HOME") if k in os.environ}
        env.update(OPENCLAW_STATE_DIR=str(root), OPENCLAW_CONFIG_PATH=str(config))
        result = subprocess.run(
            [binary, "config", "validate", "--json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode:
            raise RuntimeError(
                "Isolated OpenClaw schema validation failed; inspect private output"
            )
        return {
            "config_schema": True,
            "isolation": True,
            "production_config_read": False,
            "gateway_restarted": False,
            "channels": False,
            "user_path": False,
            "ready_for_uat": False,
            "next": "Ops must review a minimal config patch against current live values, then verify an isolated Gateway and separately approved test channel.",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openclaw", default="openclaw")
    print(json.dumps(verify(parser.parse_args().openclaw), indent=2))
