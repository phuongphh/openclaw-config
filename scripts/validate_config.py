"""Offline snapshot checks; does not apply config, start Gateway or call providers."""
import json
from pathlib import Path
import re
import subprocess


def validate(config, known_agents):
    if not isinstance(config, dict) or not isinstance(config.get('agents'), dict):
        raise ValueError('Config must contain an agents object')
    entries = config['agents'].get('list', [])
    if not isinstance(entries, list):
        raise ValueError('agents.list must be a list')
    ids = [a.get('id') for a in entries if isinstance(a, dict)]
    if len(ids) != len(entries) or any(not isinstance(i, str) or not i for i in ids):
        raise ValueError('Every declared agent needs an id')
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate agent id')
    available = set(ids) | set(known_agents)
    bindings = config.get('bindings', [])
    if not isinstance(bindings, list):
        raise ValueError('bindings must be a list')
    for binding in bindings:
        if not isinstance(binding, dict) or binding.get('agentId') not in available:
            raise ValueError('Binding references an undeclared agent')
    channels = config.get('channels', {})
    if not isinstance(channels, dict):
        raise ValueError('channels must be an object')
    for channel in channels.values():
        if not isinstance(channel, dict) or not isinstance(channel.get('accounts', {}), dict):
            raise ValueError('Channel accounts must be an object')


def validate_jobs(value, known_agents):
    jobs = value.get('jobs') if isinstance(value, dict) else None
    if not isinstance(jobs, list):
        raise ValueError('Cron snapshot needs a jobs list')
    seen = set()
    for job in jobs:
        if not isinstance(job, dict) or not job.get('id') or job['id'] in seen:
            raise ValueError('Cron job ids must be present and unique')
        seen.add(job['id'])
        if job.get('agentId') not in known_agents or type(job.get('enabled')) is not bool:
            raise ValueError('Invalid cron agent or enabled flag')
        if not isinstance(job.get('payload'), dict) or not job['payload'].get('kind'):
            raise ValueError('Cron payload kind required')


def check_checkout(root):
    root = Path(root)
    names = subprocess.check_output(['git', 'ls-files', '*.json'], cwd=root, text=True).splitlines()
    for name in names:
        text = (root / name).read_text()
        json.loads(text)
        if re.search(r'\b(?:\d{7,}:[A-Za-z0-9_-]{30,}|(?:sk-ant-|sk-proj-|github_pat_|ghp_)[A-Za-z0-9_-]{20,})', text):
            raise ValueError('Credential-shaped value in tracked JSON: ' + name)
    config = json.loads((root / 'openclaw.json').read_text())
    known = {p.name for p in (root / 'agents').iterdir() if p.is_dir()}
    validate(config, known)
    known |= {entry['id'] for entry in config['agents'].get('list', [])}
    validate_jobs(json.loads((root / 'cron/jobs.json').read_text()), known)
    return {'json_files_checked': len(names), 'known_agent_count': len(known), 'runtime_compatibility': 'not_verified', 'config_applied': False}


if __name__ == '__main__':
    print(json.dumps(check_checkout(Path(__file__).resolve().parents[1])))
