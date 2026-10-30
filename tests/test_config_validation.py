import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('validate_config', Path(__file__).resolve().parents[1] / 'scripts/validate_config.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class ConfigValidationTests(unittest.TestCase):
    def test_legacy_default_agent_layout_is_supported(self):
        checks.validate({'agents': {'defaults': {}}, 'channels': {}}, {'main', 'pm'})

    def test_declared_binding_is_supported(self):
        checks.validate({'agents': {'list': [{'id': 'devops'}]}, 'bindings': [{'agentId': 'devops'}]}, set())

    def test_duplicate_agent_is_rejected(self):
        with self.assertRaises(ValueError):
            checks.validate({'agents': {'list': [{'id': 'pm'}, {'id': 'pm'}]}}, set())

    def test_binding_to_missing_agent_is_rejected(self):
        with self.assertRaises(ValueError):
            checks.validate({'agents': {}, 'bindings': [{'agentId': 'missing'}]}, {'main'})

    def test_wrong_accounts_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            checks.validate({'agents': {}, 'channels': {'telegram': {'accounts': []}}}, {'main'})

    def test_duplicate_cron_job_is_rejected(self):
        job = {'id': 'one', 'agentId': 'main', 'enabled': True, 'payload': {'kind': 'agentTurn'}}
        with self.assertRaises(ValueError):
            checks.validate_jobs({'jobs': [job, job]}, {'main'})

    def test_unknown_cron_agent_is_rejected(self):
        with self.assertRaises(ValueError):
            checks.validate_jobs({'jobs': [{'id': 'one', 'agentId': 'other', 'enabled': True, 'payload': {'kind': 'agentTurn'}}]}, {'main'})
