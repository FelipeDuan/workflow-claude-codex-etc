#!/usr/bin/env python3
"""Consulta a franquia pelo App Server oficial; --write salva o resultado local."""

import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

TIMEOUT = 20.0


def iso(timestamp=None):
    value = datetime.now(timezone.utc) if timestamp is None else datetime.fromtimestamp(timestamp, timezone.utc)
    return value.isoformat().replace('+00:00', 'Z')


def windows_from(result):
    snapshot = result['rateLimits']
    buckets = result.get('rateLimitsByLimitId')
    if isinstance(buckets, dict) and 'codex' in buckets:
        snapshot = buckets['codex']
    if not isinstance(snapshot, dict):
        raise ValueError
    windows = []
    for name in ('primary', 'secondary'):
        window = snapshot.get(name)
        if window is None:
            continue
        used = window['usedPercent']
        minutes = window.get('windowDurationMins')
        reset = window.get('resetsAt')
        if type(used) is not int or used < 0:
            raise ValueError
        if minutes is not None and (type(minutes) is not int or minutes <= 0):
            raise ValueError
        if reset is not None and type(reset) is not int:
            raise ValueError
        windows.append({
            'kind': {300: 'five_hour', 10080: 'weekly'}.get(minutes, name),
            'used_percent': float(used),
            'resets_at': iso(reset) if reset is not None else None,
            'window_minutes': minutes,
        })
    return windows


def fetch_quota():
    deadline = time.monotonic() + TIMEOUT
    # Reserva até um segundo do mesmo prazo para encerrar e recolher o processo.
    read_deadline = deadline - min(1.0, TIMEOUT / 4)
    output = dict(provider='codex', source='app-server', fetched_at=iso(),
                  status='error', windows=[], note='Falha na consulta ao App Server.')
    process = None
    try:
        process = subprocess.Popen(['codex', 'app-server'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            pending = b''

            def send(message):
                process.stdin.write((json.dumps(message) + '\n').encode())
                process.stdin.flush()

            def response(request_id):
                nonlocal pending
                while True:
                    remaining = read_deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError
                    if b'\n' not in pending:
                        if not selector.select(remaining):
                            raise TimeoutError
                        chunk = os.read(process.stdout.fileno(), 65536)
                        if not chunk:
                            raise ValueError
                        pending += chunk
                        continue
                    line, pending = pending.split(b'\n', 1)
                    message = json.loads(line)
                    if not isinstance(message, dict):
                        raise ValueError
                    if message.get('id') != request_id:
                        continue
                    if 'error' in message:
                        raise ValueError
                    if not isinstance(message.get('result'), dict):
                        raise ValueError
                    return message['result']

            send({'id': 0, 'method': 'initialize', 'params': {
                'clientInfo': {'name': 'ai_os_quota', 'version': '1.0.0'}}})
            response(0)
            send({'method': 'initialized'})
            send({'id': 1, 'method': 'account/rateLimits/read'})
            output['windows'] = windows_from(response(1))
            output['status'] = 'ok' if output['windows'] else 'unknown'
            output['note'] = '' if output['windows'] else 'Franquia indisponível nesta conta.'
    except FileNotFoundError:
        output['note'] = 'Executável codex não encontrado.'
    except (TimeoutError, subprocess.TimeoutExpired):
        output['note'] = 'Tempo limite na consulta ao App Server.'
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        pass
    finally:
        if process is not None:
            try:
                process.terminate()
                try:
                    process.wait(timeout=max(0, min(0.3, deadline - time.monotonic())))
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=max(0, deadline - time.monotonic()))
            except (OSError, subprocess.TimeoutExpired):
                output.update(status='error', windows=[], note='Falha ao encerrar o App Server.')
            for pipe in (process.stdin, process.stdout):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        output.update(status='error', windows=[], note='Falha ao encerrar o App Server.')
    output['fetched_at'] = iso()
    return output


def write_quota(output):
    directory = Path.home() / '.local/state/ai-os/quota'
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory,
                                         prefix='.codex-', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(output, stream, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        temporary.replace(directory / 'codex.json')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    if sys.argv[1:] not in ([], ['--write']):
        output = dict(provider='codex', source='app-server', fetched_at=iso(),
                      status='error', windows=[], note='Argumentos inválidos. Use --write para salvar.')
    else:
        output = fetch_quota()
        if '--write' in sys.argv:
            try:
                write_quota(output)
            except (OSError, ValueError):
                output.update(status='error', windows=[], note='Não foi possível salvar a franquia.')
    print(json.dumps(output, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
