import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "fleet_product_adapter", ROOT / "ops/fleet/verify_dev.py"
)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class DeploymentTests(unittest.TestCase):
    def test_fresh_profile_cannot_attach_live_channels_or_gateway(self):
        with tempfile.TemporaryDirectory() as root:
            config = adapter.isolated_config(root)
            self.assertEqual(config["gateway"]["port"], 28789)
            self.assertEqual(config["gateway"]["bind"], "loopback")
            self.assertEqual(config["channels"], {})
            self.assertFalse(config["plugins"]["enabled"])
            self.assertTrue(config["agents"]["defaults"]["workspace"].startswith(root))
            self.assertNotIn("auth", config)
