#!/usr/bin/env python3
"""Consulta a franquia do Antigravity CLI via agy -p /usage; --write salva o resultado local."""

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile

TIMEOUT = 30.0


def iso(timestamp=None):
    value = datetime.now(timezone.utc) if timestamp is None else datetime.fromtimestamp(timestamp, timezone.utc)
    return value.isoformat().replace('+00:00', 'Z')


def parse_usage(text):
    """Interpreta as linhas em TSV retornadas por agy -p /usage."""
    if not text or not text.strip():
        raise ValueError('Saída do agy vazia.')

    windows = []
    ignored_notes = []

    for line in text.splitlines():
        trimmed = line.strip('\r\n')
        if not trimmed:
            continue
        cols = trimmed.split('\t')
        if len(cols) != 4:
            raise ValueError(f'Linha com formato inválido (esperado 4 colunas separadas por TAB): {trimmed}')

        pool = cols[0].strip()
        window_raw = cols[1].strip()
        pct_raw = cols[2].strip()
        reset_raw = cols[3].strip()

        if not pool or not window_raw or not pct_raw or not reset_raw:
            raise ValueError(f'Coluna vazia na linha: {trimmed}')

        if not pct_raw.endswith('%'):
            raise ValueError(f'Formato de porcentagem inválido: {pct_raw}')

        try:
            remaining = float(pct_raw[:-1].strip())
        except ValueError:
            raise ValueError(f'Porcentagem não numérica: {pct_raw}')

        if not (0.0 <= remaining <= 100.0):
            raise ValueError(f'Porcentagem fora do intervalo 0-100%: {pct_raw}')

        used_percent = float(round(100.0 - remaining, 2))

        try:
            dt = datetime.fromisoformat(reset_raw.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            raise ValueError(f'Data de reset inválida: {reset_raw}')

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        resets_at = dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

        w_lower = window_raw.lower()
        if 'five hour' in w_lower or '5 hour' in w_lower or '5h' in w_lower:
            kind = 'five_hour'
            window_minutes = 300
        elif 'weekly' in w_lower or 'week' in w_lower or 'semanal' in w_lower:
            kind = 'weekly'
            window_minutes = 10080
        else:
            ignored_notes.append(f'Linha desconhecida ignorada: {window_raw}')
            continue

        windows.append({
            'kind': kind,
            'pool': pool,
            'used_percent': used_percent,
            'resets_at': resets_at,
            'window_minutes': window_minutes,
        })

    if not windows:
        if ignored_notes:
            raise ValueError('; '.join(ignored_notes))
        raise ValueError('Nenhuma franquia encontrada na saída do agy.')

    return windows, ignored_notes


def fetch_quota():
    output = dict(
        provider='antigravity',
        source='agy-usage',
        fetched_at=iso(),
        status='error',
        windows=[],
        note='Falha na consulta ao agy.',
    )
    try:
        result = subprocess.run(
            ['agy', '-p', '/usage'],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        if result.returncode != 0:
            output['note'] = f'Comando agy retornou código {result.returncode}.'
            return output

        windows, notes = parse_usage(result.stdout)
        output['windows'] = windows
        output['status'] = 'ok'
        output['note'] = '; '.join(notes) if notes else ''
    except FileNotFoundError:
        output['note'] = 'Executável agy não encontrado.'
    except subprocess.TimeoutExpired:
        output['note'] = 'Tempo limite na consulta ao agy.'
    except ValueError as exc:
        output['note'] = str(exc)
    except OSError:
        output['note'] = 'Falha na execução do agy.'
    finally:
        output['fetched_at'] = iso()
    return output


def write_quota(output):
    directory = Path.home() / '.local/state/ai-os/quota'
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory,
                                         prefix='.antigravity-', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(output, stream, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        temporary.replace(directory / 'antigravity.json')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    if sys.argv[1:] not in ([], ['--write']):
        output = dict(
            provider='antigravity',
            source='agy-usage',
            fetched_at=iso(),
            status='error',
            windows=[],
            note='Argumentos inválidos. Use --write para salvar.',
        )
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
