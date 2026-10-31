import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('dev_gateway', Path(__file__).resolve().parents[1]/'ops/fleet/dev_gateway.py')
adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)


class DevGatewayTests(unittest.TestCase):
    def test_new_roots_only_and_no_production_identity_in_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            source = parent/'candidate'; source.mkdir()
            (source/'fleet-artifact.json').write_text('{}')
            root = parent/'dev'
            adapter.prepare(root, source)
            config = json.loads((root/'state/openclaw.json').read_text())
            self.assertEqual(config['channels'], {})
            self.assertEqual(config['bindings'], [])
            self.assertEqual(config['tools']['allow'], ['read'])
            self.assertEqual(config['tools']['exec']['security'], 'deny')
            self.assertTrue(config['tools']['fs']['workspaceOnly'])
            self.assertFalse(config['plugins']['enabled'])
            env = adapter.environment(root)
            self.assertTrue(Path(env['HOME']).is_relative_to(root))
            self.assertNotIn('ANTHROPIC_API_KEY', env)
            with self.assertRaises(ValueError): adapter.prepare(root, source)

    def test_provider_requires_read_and_uses_actual_tool_result(self):
        with self.assertRaises(ValueError): adapter.completion({'messages': []})
        tool = {'type': 'function', 'function': {'name': 'read', 'parameters': {'properties': {'path': {}}}}}
        first = adapter.completion({'model': 'brain-fixture', 'messages': [], 'tools': [tool]})
        self.assertEqual(json.loads(first['tool_calls'][0]['function']['arguments'])['path'], 'wiki/index.md')
        final = adapter.completion({'messages': [{'role': 'tool', 'content': 'random-source-marker'}]})
        self.assertIn('random-source-marker', final['content'])
        self.assertNotIn('random-source-marker', str(first))
