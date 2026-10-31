"""Credential-free local Gateway fixture. Never imports a Production config.

The deterministic provider verifies transport/tool wiring, not model quality.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 28789
PROVIDER_PORT = 28790
MARKER = '.fleet-openclaw-dev.json'


def private_root(value, create=False):
    root = Path(value).absolute()
    if root.resolve() != root or root.is_symlink():
        raise ValueError('Dev root cannot traverse symlinks')
    marker = root / MARKER
    if create:
        if root.exists() and any(root.iterdir()):
            raise ValueError('Use a new empty Dev root')
        root.mkdir(parents=True, mode=0o700, exist_ok=True)
        marker.write_text(json.dumps({'environment': 'dev', 'project': 'openclaw-config'}))
        marker.chmod(0o600)
    if marker.is_symlink() or json.loads(marker.read_text()) != {'environment': 'dev', 'project': 'openclaw-config'}:
        raise ValueError('Not a registered Dev root')
    return root


def environment(root):
    root = private_root(root)
    return {'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
            'HOME': str(root / 'home'), 'TMPDIR': str(root / 'tmp'),
            'OPENCLAW_STATE_DIR': str(root / 'state'),
            'OPENCLAW_CONFIG_PATH': str(root / 'state/openclaw.json'),
            'OPENCLAW_DISABLE_BONJOUR': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}


def prepare(root, candidate, brain_workspace=None):
    candidate = Path(candidate).resolve()
    if not (candidate/'fleet-artifact.json').is_file():
        raise ValueError('A SHA-pinned staged candidate is required')
    root = private_root(root, create=True)
    for path in ('home', 'tmp', 'state', 'workspace', 'logs'):
        (root/path).mkdir(mode=0o700)
    # Only the staged, allowlisted artifact is copied. No live state or config.
    shutil.copytree(candidate, root/'workspace/candidate')
    nonce = secrets.token_hex(12)
    (root/'workspace/DEV-NOTE.md').write_text('Synthetic Dev transport marker: '+nonce+'\n')
    (root/'workspace/AGENTS.md').write_text('This is an isolated Dev fixture, not Production. Only read requested files; cite their paths. Never execute or write.\n')
    models = [{'id': ident, 'name': ident, 'reasoning': False, 'input': ['text'],
               'cost': {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0},
               'contextWindow': 32000, 'maxTokens': 1024} for ident in ('claw-fixture', 'brain-fixture')]
    agents = [{'id': 'dev-preview', 'default': True, 'workspace': str(root/'workspace'), 'model': 'dev-fixture/claw-fixture'}]
    if brain_workspace:
        brain = Path(brain_workspace).resolve()
        if not (brain/'.fleet-brain-dev.json').is_file():
            raise ValueError('An isolated synthetic SecondBrain workspace is required')
        agents.append({'id': 'brain-dev', 'workspace': str(brain), 'model': 'dev-fixture/brain-fixture'})
    config = {
        'gateway': {'mode': 'local', 'bind': 'loopback', 'port': PORT,
                    'auth': {'mode': 'token', 'token': secrets.token_urlsafe(32)},
                    'controlUi': {'allowedOrigins': [f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}']}},
        'models': {'mode': 'replace', 'providers': {'dev-fixture': {
            'baseUrl': f'http://127.0.0.1:{PROVIDER_PORT}/v1', 'api': 'openai-completions',
            'apiKey': 'fixture-local-only', 'models': models}}},
        'agents': {'defaults': {'workspace': str(root/'workspace'), 'skipBootstrap': True,
                               'model': {'primary': 'dev-fixture/claw-fixture'}}, 'list': agents},
        'tools': {'profile': 'coding', 'allow': ['read'],
                  'deny': ['exec', 'process', 'write', 'edit', 'apply_patch', 'gateway', 'cron',
                           'sessions_spawn', 'sessions_send', 'message', 'browser', 'web_search', 'web_fetch'],
                  'fs': {'workspaceOnly': True}, 'exec': {'security': 'deny'},
                  'elevated': {'enabled': False}, 'agentToAgent': {'enabled': False}},
        'channels': {}, 'bindings': [], 'plugins': {'enabled': False},
    }
    config_path = root/'state/openclaw.json'
    config_path.write_text(json.dumps(config, indent=2)); config_path.chmod(0o600)
    (root/'expected.json').write_text(json.dumps({'openclaw_nonce': nonce, 'model_quality_tested': False}))
    return {'root': str(root), 'url': f'http://127.0.0.1:{PORT}', 'started': False,
            'provider': 'deterministic-fixture-no-paid-model', 'telegram_accounts': 0}


def text_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(part.get('text', '') for part in content if isinstance(part, dict))
    return ''


def completion(payload):
    """Always read first; answer is derived only from the returned tool text."""
    messages = payload.get('messages', [])
    tool_results = [m for m in messages if m.get('role') == 'tool']
    if tool_results:
        body = text_content(tool_results[-1].get('content'))
        return {'role': 'assistant', 'content': 'DEV fixture result (not model-quality evaluation):\n'+body[:6000]}
    tools = payload.get('tools', [])
    read = next((t['function'] for t in tools if t.get('function', {}).get('name') == 'read'), None)
    if not read:
        raise ValueError('Gateway did not expose the required read tool')
    path = 'wiki/index.md' if payload.get('model') == 'brain-fixture' else 'DEV-NOTE.md'
    last = text_content(next((m.get('content') for m in reversed(messages) if m.get('role') == 'user'), ''))
    if 'OUTSIDE_WORKSPACE_TEST' in last:
        path = '/etc/hosts'
    properties = read.get('parameters', {}).get('properties', {})
    key = 'path' if 'path' in properties else 'file_path'
    return {'role': 'assistant', 'content': None, 'tool_calls': [{
        'id': 'call_dev_read', 'type': 'function', 'function': {'name': 'read', 'arguments': json.dumps({key: path})}}]}


def serve(root):
    root = private_root(root)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            if self.path != '/health':
                self.send_error(404); return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"fixture":true}')

        def do_POST(self):
            if self.path != '/v1/chat/completions':
                self.send_error(404); return
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2_000_000:
                self.send_error(413); return
            try:
                payload = json.loads(self.rfile.read(length))
                message = completion(payload)
            except (ValueError, KeyError) as exc:
                self.send_error(400, str(exc)); return
            with (root/'logs/provider.jsonl').open('a') as handle:
                handle.write(json.dumps({'model': payload.get('model'), 'messages': payload.get('messages'), 'reply': message})+'\n')
            result = {'id': 'chatcmpl-dev-fixture', 'object': 'chat.completion', 'created': 1,
                      'model': payload.get('model'), 'choices': [{'index': 0, 'message': message,
                      'finish_reason': 'tool_calls' if message.get('tool_calls') else 'stop'}],
                      'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}}
            self.send_response(200)
            if payload.get('stream'):
                self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                delta = dict(message)
                if delta.get('tool_calls'):
                    delta['tool_calls'] = [dict(call, index=i) for i, call in enumerate(delta['tool_calls'])]
                chunk = {'id': result['id'], 'object': 'chat.completion.chunk', 'created': 1,
                         'model': result['model'], 'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]}
                final = {**chunk, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': result['choices'][0]['finish_reason']}]}
                for item in (chunk, final): self.wfile.write(('data: '+json.dumps(item)+'\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
            else:
                self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(result).encode())
    ThreadingHTTPServer(('127.0.0.1', PROVIDER_PORT), Handler).serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'provider', 'validate', 'gateway', 'call'])
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--brain-workspace', type=Path)
    parser.add_argument('--openclaw', default='/opt/homebrew/bin/openclaw')
    parser.add_argument('arguments', nargs='*')
    args = parser.parse_args()
    if args.action == 'prepare':
        print(json.dumps(prepare(args.root, args.candidate, args.brain_workspace))); return
    if args.action == 'provider': serve(args.root); return
    argv = {'validate': ['config', 'validate', '--json'],
            'gateway': ['gateway', 'run', '--port', str(PORT)],
            'call': ['gateway', 'call', '--expect-url', f'ws://127.0.0.1:{PORT}', '--json']}[args.action]
    os.execve(args.openclaw, [args.openclaw, *argv, *args.arguments], environment(args.root))


if __name__ == '__main__':
    main()
