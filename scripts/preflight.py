#!/usr/bin/env python3
"""Preflight consultivo do AI OS (Python >= 3.11, somente stdlib).

Não inicia agentes nem grava estado. A CLI coleta Git, franquias e agentes;
``decide`` usa apenas os argumentos recebidos. Contrato de task: provider
(provider/model), mode, thinking, base, base_exists, risk, now (ISO UTC).
restricted: {enabled: bool, allowed_models: [ID]}. running_agents=None indica
falha da coleta, nunca ausência confirmada de agentes.
"""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def validate_policy(policy):
    """Schema mínimo: chaves, tipos e domínios usados na decisão."""
    def require(obj, key, kind):
        if not isinstance(obj, dict) or key not in obj or type(obj[key]) is not kind:
            raise ValueError(f"política: campo {key} deve ser {kind.__name__}")
        return obj[key]

    def strings(obj, key):
        values = require(obj, key, list)
        if any(type(value) is not str or not value for value in values):
            raise ValueError(f"política: {key} deve conter strings não vazias")
        return values

    if require(policy, 'schema_version', int) != 3:
        raise ValueError('política: schema_version deve ser 3')
    if not require(policy, 'policy_version', str).strip():
        raise ValueError('política: policy_version vazio')
    providers = require(policy, 'providers', dict)
    if not providers:
        raise ValueError('política: providers vazio')
    strings(policy, 'forbidden_providers')
    if set(strings(policy, 'required_parameters')) != {'provider_model', 'mode'}:
        raise ValueError('política: required_parameters inválido')
    if strings(policy, 'worktree_required_parameters') != ['base']:
        raise ValueError('política: worktree requer base')
    for name, spec in providers.items():
        if type(name) is not str or not name:
            raise ValueError('política: provider inválido')
        modes = strings(spec, 'allowed_modes')
        forbidden = strings(spec, 'forbidden_modes')
        if not modes or set(modes) & set(forbidden):
            raise ValueError('política: modos ausentes ou contraditórios')
        require(spec, 'thinking_required', bool)
        require(spec, 'quota_metered', bool)
        if require(spec, 'default_mode', str) not in modes:
            raise ValueError('política: default_mode inválido')
        thinking = spec.get('default_thinking')
        if 'default_thinking' not in spec or (thinking is not None and type(thinking) is not str):
            raise ValueError('política: default_thinking inválido')
        if spec['thinking_required'] and not thinking:
            raise ValueError('política: default_thinking obrigatório')
    quota = require(policy, 'quota', dict)
    if require(quota, 'max_age_seconds', int) <= 0:
        raise ValueError('política: max_age_seconds inválido')
    thresholds = require(quota, 'thresholds', dict)
    for window in ('five_hour', 'weekly'):
        value = thresholds.get(window)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError('política: limiar inválido')
    aliases = require(quota, 'window_aliases', dict)
    if any(type(k) is not str or v not in thresholds for k, v in aliases.items()):
        raise ValueError('política: alias de janela inválido')
    if not {'five_hour', 'weekly', 'seven_day'} <= aliases.keys():
        raise ValueError('política: aliases obrigatórios ausentes')
    if not set(strings(quota, 'threshold_risks')) <= {'low', 'medium'}:
        raise ValueError('política: quota não pode rebaixar risco alto')
    for key in ('unknown_decision', 'stale_decision'):
        if require(quota, key, str) != 'ask_human':
            raise ValueError('política: quota desconhecida exige humano')
    reset = require(quota, 'reset_exception', dict)
    if require(reset, 'max_minutes_to_reset', int) <= 0 or strings(reset, 'windows') != ['five_hour']:
        raise ValueError('política: exceção por reset inválida')
    astra = require(policy, 'astra', dict)
    if require(astra, 'provider', str) not in providers:
        raise ValueError('política: provider Astra inválido')
    require(astra, 'model', str)
    if strings(astra, 'allowed_risks') != ['high']:
        raise ValueError('política: Astra exige risco alto')
    strings(astra, 'allowed_thinking')
    value = require(astra, 'five_hour_used_percent_exclusive_max', int)
    if not 0 < value <= 100:
        raise ValueError('política: limite Astra inválido')
    require(astra, 'require_no_cheaper_eligible', bool)
    if require(astra, 'unknown_decision', str) != 'deny':
        raise ValueError('política: Astra desconhecido deve bloquear')
    concurrency = require(policy, 'concurrency', dict)
    for name in providers:
        spec = require(concurrency, name, dict)
        limit = spec.get('max_heavy')
        if 'max_heavy' not in spec or (limit is not None and (type(limit) is not int or limit < 1)):
            raise ValueError('política: max_heavy inválido')
        strings(spec, 'light_models')
        require(spec, 'unknown_model_is_heavy', bool)
    eligible = require(policy, 'eligible_models', dict)
    for risk in ('low', 'medium', 'high'):
        if not strings(eligible, risk):
            raise ValueError('política: modelos elegíveis ausentes')
        for label in eligible[risk]:
            provider, model = split_model(label)
            if provider not in providers or not model or provider in policy['forbidden_providers']:
                raise ValueError('política: candidato inválido')
    access = require(policy, 'acesso_dados', dict)
    for group in ('pessoal-publico', 'pessoal-restrito', 'institucional'):
        strings(access, group)
    require(policy, 'nota_institucional', str)
    guardrails = require(policy, 'guardrails', dict)
    if require(guardrails, 'limite_fallback', int) < 0:
        raise ValueError('política: limite_fallback inválido')
    require(guardrails, 'revisor_independente_para_alto_risco', bool)
    reviewers = require(policy, 'reviewers', dict)
    require(require(reviewers, 'high', dict), 'different_model_family', bool)
    medium = require(reviewers, 'medium', dict)
    strings(medium, 'order')
    strings(medium, 'sol_thinking')
    require(medium, 'luna_only_mechanical', bool)
    strings(policy, 'documented_only')
    return policy


def split_model(label):
    """Normaliza apenas o namespace duplicado real do OpenCode."""
    provider, _, model = str(label or '').strip().partition('/')
    if provider == 'opencode' and model.startswith('opencode/'):
        model = model.removeprefix('opencode/')
    return provider, model


def model_allowed(label, allowed):
    provider, model = split_model(label)
    normalized = f'{provider}/{model}'
    return any(item == provider if item in ('claude', 'codex') else
               '/'.join(split_model(item)) == normalized for item in allowed)


def timestamp(value):
    try:
        moment = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return moment if moment.tzinfo is not None else None
    except (ValueError, TypeError, AttributeError):
        return None


def quota_status(provider, quotas, policy, now):
    snapshot = quotas.get(provider) if isinstance(quotas, dict) else None
    result = {'status': 'unknown', 'fetched_at': None, 'age_seconds': None, 'windows': {}, 'resets_at': {}}
    if provider in policy['providers'] and not policy['providers'][provider]['quota_metered']:
        result['status'] = 'unmetered'
        return result
    if not isinstance(snapshot, dict):
        return result
    result['fetched_at'] = snapshot.get('fetched_at')
    fetched = timestamp(snapshot.get('fetched_at'))
    if now is None or fetched is None:
        return result
    age = (now - fetched).total_seconds()
    result['age_seconds'] = age
    if age < 0:
        return result
    if age > policy['quota']['max_age_seconds']:
        result['status'] = 'stale'
        return result
    if snapshot.get('status') != 'ok' or snapshot.get('provider') != provider:
        return result
    windows = snapshot.get('windows')
    if not isinstance(windows, list):
        return result
    for window in windows:
        if not isinstance(window, dict):
            return result
        raw_kind = window.get('kind')
        if not isinstance(raw_kind, str):
            return result
        kind = policy['quota']['window_aliases'].get(raw_kind)
        if kind is None:
            continue
        used = window.get('used_percent')
        if type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= 100:
            return result
        result['windows'][kind] = max(used, result['windows'].get(kind, 0))
        reset = window.get('resets_at')
        if kind in result['resets_at'] and result['resets_at'][kind] != reset:
            reset = None
        result['resets_at'][kind] = reset if timestamp(reset) else None
    if set(policy['quota']['thresholds']) <= result['windows'].keys():
        result['status'] = 'fresh'
    return result


def _heavy(provider, model, policy):
    spec = policy['concurrency'][provider]
    return model not in spec['light_models'] if model else spec['unknown_model_is_heavy']


def _decision(task, policy, quotas, running_agents, restricted):
    provider, model = split_model(task.get('provider'))
    now = timestamp(task.get('now'))
    freshness = quota_status(provider, quotas, policy, now)
    result = {'decision': 'allow', 'reason_codes': [], 'hints': [],
              'alternatives': [], 'policy_version': policy['policy_version'],
              'quota_freshness': freshness}

    def finish(decision, codes, hints=()):
        result.update(decision=decision, reason_codes=codes, hints=list(hints))
        return result

    # (a) Dados, termos e permissões precedem ausência de parâmetros.
    if provider in policy['forbidden_providers']:
        return finish('deny', ['provider_forbidden'])
    if restricted.get('enabled') and not model_allowed(task.get('provider'), restricted['allowed_models']):
        return finish('deny', ['restricted_model_not_allowed'])
    if provider in policy['providers'] and task.get('mode') in policy['providers'][provider]['forbidden_modes']:
        return finish('deny', ['mode_forbidden'])

    # (b) Parâmetros explícitos: nenhuma herança implícita do pai.
    codes, hints = [], []
    if provider not in policy['providers']:
        codes.append('provider_unknown')
        hints.append('Use um provider da política com --provider provider/model.')
    if not model or any(not part for part in model.split('/')):
        codes.append('provider_model_required')
        hints.append('Informe --provider provider/model explicitamente (I-19).')
    if not task.get('mode'):
        codes.append('mode_required')
        hints.append('Informe --mode explicitamente (I-19).')
    elif provider in policy['providers'] and task['mode'] not in policy['providers'][provider]['allowed_modes']:
        codes.append('mode_invalid')
    if task.get('new_workspace') not in (None, 'worktree', 'local'):
        codes.append('new_workspace_invalid')
    planned = task.get('planned_heavy', 0)
    if type(planned) is not int or planned < 0:
        codes.append('planned_heavy_invalid')
    if task.get('new_workspace') == 'worktree' and not task.get('base'):
        codes.append('base_required')
        hints.append('Informe --base com a branch ou referência de origem (I-17).')
    elif task.get('base') and task.get('base_exists') is not True:
        codes.append('base_not_found')
        hints.append('Confirme a referência --base no Git do --cwd.')
    if provider in policy['providers'] and policy['providers'][provider]['thinking_required'] and not task.get('thinking'):
        codes.append('thinking_required')
        hints.append('Informe --thinking explicitamente para Codex.')
    risk = task.get('risk')
    if risk not in policy['eligible_models']:
        codes.append('risk_required')
    if codes:
        return finish('deny', codes, hints)
    eligible = [split_model(item) for item in policy['eligible_models'][risk]]
    is_astra = (provider, model) == (policy['astra']['provider'], policy['astra']['model'])
    if not is_astra and (provider, model) not in eligible:
        return finish('deny', ['risk_quality_floor'], ['Escolha um modelo elegível para o risco; a quota não rebaixa o piso.'])

    # (c) Astra tem regra mais estrita que a abstenção genérica de quota.
    astra = policy['astra']
    if (provider, model) == (astra['provider'], astra['model']):
        codes = []
        if risk not in astra['allowed_risks']:
            codes.append('astra_risk_forbidden')
        if task.get('thinking') not in astra['allowed_thinking']:
            codes.append('astra_thinking_forbidden')
        if astra['require_no_cheaper_eligible'] and task.get('no_cheaper_eligible') is not True:
            codes.append('astra_cheaper_eligible_not_ruled_out')
        if freshness['status'] != 'fresh':
            codes.append('astra_quota_unknown')
        elif freshness['windows']['five_hour'] >= astra['five_hour_used_percent_exclusive_max']:
            codes.append('astra_quota_limit')
        if codes:
            return finish('deny', codes, ['Astra exige verificar todas as condições em roteamento.json.'])
    if policy['providers'][provider]['quota_metered'] and freshness['status'] != 'fresh':
        return finish('ask_human', ['quota_' + freshness['status']])
    exceeded = [kind for kind, threshold in policy['quota']['thresholds'].items()
                if kind in freshness['windows'] and freshness['windows'][kind] >= threshold]
    reset_exception = False
    if risk in policy['quota']['threshold_risks'] and exceeded:
        reset_policy = policy['quota']['reset_exception']
        reset_exception = task.get('short_task') is True and all(
            kind in reset_policy['windows'] and timestamp(freshness['resets_at'].get(kind)) is not None and
            0 <= (timestamp(freshness['resets_at'][kind]) - now).total_seconds() <= reset_policy['max_minutes_to_reset'] * 60
            for kind in exceeded)
        if not reset_exception:
            return finish('ask_human', ['quota_' + kind + '_limit' for kind in exceeded],
                          ['Prefira outro provider elegível ou consulte Felipe.'])

    # (d) Snapshot ausente é desconhecido; nunca significa lista vazia.
    spec = policy['concurrency'][provider]
    if spec['max_heavy'] is not None and _heavy(provider, model, policy):
        if running_agents is None:
            return finish('ask_human', ['running_agents_unknown'])
        count = 0
        for agent in running_agents:
            ap = agent.get('Provider', agent.get('provider', ''))
            am = agent.get('Model', agent.get('model', ''))
            if '/' in ap:
                ap, embedded = split_model(ap)
                am = am or embedded
            if isinstance(am, str) and am.startswith(ap + '/'):
                _, am = split_model(am)
            status = agent.get('Status', agent.get('status', ''))
            if ap == provider and status not in ('idle', 'closed', 'error') and _heavy(ap, am, policy):
                count += 1
        if count + planned >= spec['max_heavy']:
            return finish('ask_human', ['provider_heavy_concurrency'])
    if reset_exception:
        return finish('allow', ['quota_reset_exception'])
    return result


def decide(task, policy, quotas, running_agents, restricted):
    """Decisão pura, determinística; não lê relógio, arquivos ou processos."""
    try:
        validate_policy(policy)
    except (ValueError, TypeError) as exc:
        return {'decision': 'deny', 'reason_codes': ['policy_invalid'], 'hints': [str(exc)],
                'alternatives': [], 'policy_version': None, 'quota_freshness': {'status': 'unknown'}}
    if not isinstance(task, dict) or any(task.get(key) is not None and type(task[key]) is not str for key in ('provider', 'mode', 'thinking', 'base', 'risk', 'now')) or not isinstance(restricted, dict) or type(restricted.get('enabled')) is not bool or not isinstance(restricted.get('allowed_models'), list) or any(type(item) is not str for item in restricted['allowed_models']):
        return {'decision': 'deny', 'reason_codes': ['input_invalid'], 'hints': [],
                'alternatives': [], 'policy_version': policy['policy_version'], 'quota_freshness': {'status': 'unknown'}}
    if running_agents is not None and (not isinstance(running_agents, list) or any(
            not isinstance(a, dict) or not a.get('Provider', a.get('provider')) or any(type(a.get(upper, a.get(lower, ''))) is not str
                                          for upper, lower in (('Provider', 'provider'), ('Model', 'model'), ('Status', 'status')))
            for a in running_agents)):
        running_agents = None
    result = _decision(task, policy, quotas, running_agents, restricted)
    if result['decision'] != 'allow' and task.get('risk') in policy['eligible_models']:
        current_provider = split_model(task.get('provider'))[0]
        for label in policy['eligible_models'][task['risk']]:
            provider, _ = split_model(label)
            # Uma sugestão de economia troca o provider; nunca força downgrade.
            if provider == current_provider:
                continue
            spec = policy['providers'][provider]
            candidate = dict(task, provider=label, mode=spec['default_mode'], thinking=spec['default_thinking'])
            verdict = _decision(candidate, policy, quotas, running_agents, restricted)
            if verdict['decision'] == 'allow':
                result['alternatives'].append({'provider': label, 'mode': candidate['mode'],
                                               'thinking': candidate['thinking']})
    return result


def _run(argv, cwd=None):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=10,
                          env={k: v for k, v in os.environ.items() if not k.startswith('GIT_')})


def git(cwd, *args):
    proc = _run(['git', '-c', 'core.fsmonitor=false', '--no-optional-locks', '-C', str(cwd), *args])
    return proc.stdout.strip() if proc.returncode == 0 else None


def load_restricted(cwd, path):
    with path.open('rb') as handle:
        spec = tomllib.load(handle)['restricted']
    if not isinstance(spec, dict) or not isinstance(spec.get('paths'), list) or any(type(p) is not str for p in spec['paths']) or not isinstance(spec.get('allowed_models'), list) or any(type(p) is not str for p in spec['allowed_models']):
        raise ValueError('configuração restricted inválida')
    candidates = [cwd]
    common = git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if common:
        candidates.append(Path(common).resolve().parent)
    elif any((parent / '.git').is_file() for parent in (cwd, *cwd.parents)):
        raise ValueError('origem do worktree indisponível')
    # O marcador é evidência adicional, nunca substitui a política de modelos.
    enabled = False
    for candidate in candidates:
        enabled |= any(candidate.is_relative_to(Path(root).expanduser().resolve()) for root in spec['paths'])
        for parent in (candidate, *candidate.parents):
            marker = parent / '.ai-memory.toml'
            if marker.is_file():
                with marker.open('rb') as handle:
                    enabled |= tomllib.load(handle).get('workspace') == 'restrito'
                break
    return {'enabled': enabled, 'allowed_models': spec['allowed_models']}


def read_agents(path=None):
    if path:
        payload = json.loads(Path(path).read_text())
    else:
        proc = _run(['paseo', 'ls', '--json', '-a', '-g', '--background'])
        if proc.returncode:
            return None
        payload = json.loads(proc.stdout)
    if isinstance(payload, dict):
        payload = payload.get('agents', payload.get('Agents'))
    if not isinstance(payload, list) or any(not isinstance(a, dict) for a in payload):
        return None
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('provider', 'mode', 'thinking', 'base'):
        parser.add_argument('--' + name)
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--new-workspace', choices=('worktree', 'local'))
    parser.add_argument('--risk', choices=('low', 'medium', 'high'), required=True)
    parser.add_argument('--short-task', action='store_true', help='Tarefa curta, elegível à exceção de reset da janela 5h.')
    parser.add_argument('--planned-heavy', type=int, default=0, help='Pesados adicionais planejados ainda ausentes do snapshot.')
    parser.add_argument('--no-cheaper-eligible', action='store_true', help='A decisão humana descartou executores mais baratos para Astra.')
    parser.add_argument('--policy', type=Path, default=ROOT / 'docs/ai-os/roteamento.json')
    parser.add_argument('--restricted-config', type=Path, default=ROOT / 'config/ai-os-memory.toml')
    parser.add_argument('--quota-dir', type=Path, default=Path.home() / '.local/state/ai-os/quota')
    parser.add_argument('--agents-file', type=Path, help='Snapshot JSON de paseo ls, para simulação reproduzível.')
    parser.add_argument('--now', help='Instante ISO com fuso para simulação; padrão: relógio UTC.')
    try:
        try:
            args = parser.parse_args(argv)
        except SystemExit as exc:
            if exc.code == 0:
                return 0
            raise ValueError('argumentos inválidos') from exc
        policy = validate_policy(json.loads(args.policy.read_text()))
        cwd = Path(args.cwd).expanduser().resolve(strict=True)
        restricted = load_restricted(cwd, args.restricted_config)
        task = vars(args).copy()
        task['now'] = args.now or datetime.now(timezone.utc).isoformat()
        if timestamp(task['now']) is None:
            raise ValueError('--now precisa ser um instante ISO com fuso')
        task['base_exists'] = bool(args.base and not args.base.startswith('-') and
                                   git(cwd, 'rev-parse', '--verify', '--end-of-options', args.base + '^{commit}'))
        quotas = {}
        for provider in policy['providers']:
            try:
                quotas[provider] = json.loads((args.quota_dir.expanduser() / (provider + '.json')).read_text())
            except (OSError, ValueError):
                quotas[provider] = None
        try:
            agents = read_agents(args.agents_file)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            agents = None
        result = decide(task, policy, quotas, agents, restricted)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        result = {'decision': 'deny', 'reason_codes': ['preflight_input_error'],
                  'hints': ['Confira política, --cwd, configuração restrita e --now.'],
                  'alternatives': [], 'policy_version': None, 'quota_freshness': {'status': 'unknown'}}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return {'allow': 0, 'ask_human': 2, 'deny': 1}[result['decision']]


if __name__ == '__main__':
    raise SystemExit(main())
