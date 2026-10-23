import type { EngineInterface, Register, SessionRateLimit } from 'claude-code'

// Contrato compartilhado com o leitor do Codex: não mudar campos sem combinar.
const QUOTA_FILE = '.local/state/ai-os/quota/claude.json'
const WINDOW_MINUTES: Record<string, number> = { five_hour: 300, seven_day: 10080 }
const WEEKDAYS = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']

// Um aviso por nível por janela; a janela é identificada pelo seu resetsAt.
type Toasted = { window: string; level: number }
type Rule = { storeKey: string; low: number; high: number; text: (level: number, when: string) => string }

const FIVE_HOUR: Rule = {
  storeKey: 'toasted', // { window, level: 0 | 85 | 95 }
  low: 85,
  high: 95,
  text: (level, when) =>
    level === 95
      ? `Claude em 95% da janela de 5h${when}. Finalize com uma nota de estado (feito, decisões, próximo passo).`
      : `Claude em 85% da janela de 5h${when}. Considere delegar tarefas simples ao Codex/OpenCode.`,
}

const SEVEN_DAY: Rule = {
  storeKey: 'toasted_week', // { window, level: 0 | 75 | 90 }
  low: 75,
  high: 90,
  text: (level, when) =>
    level === 90
      ? `Claude em 90% da semana${when}. Reserve o Claude para tarefas de risco alto.`
      : `Claude usou 75% da semana${when}. Prefira Codex/OpenCode para tarefas de risco baixo e médio.`,
}

// Hora local "HH:MM"; com withDay, "dom HH:MM".
const formatReset = (iso: string | undefined, withDay = false): string | undefined => {
  if (iso === undefined) return undefined
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return undefined
  const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  return withDay ? `${WEEKDAYS[d.getDay()]} ${hm}` : hm
}

async function writeQuota($: EngineInterface, rateLimits: readonly SessionRateLimit[], note: string) {
  const home = await $.env.get('HOME')
  if (home === undefined) return
  const isKnown = rateLimits.length > 0
  const payload = {
    provider: 'claude',
    source: 'claude-code-mod',
    fetched_at: new Date(await $.clock.now()).toISOString(),
    status: isKnown ? 'ok' : 'unknown',
    windows: rateLimits.map(w => ({
      kind: w.kind,
      used_percent: w.percentUsed,
      resets_at: w.resetsAt ?? null,
      window_minutes: WINDOW_MINUTES[w.kind] ?? null,
    })),
    note: isKnown ? note : 'rateLimits vazio (fora de assinatura ou sem leitura da API ainda)',
  }
  await $.fs.write(`${home}/${QUOTA_FILE}`, JSON.stringify(payload, null, 2) + '\n')
}

async function warnOnce($: EngineInterface, w: SessionRateLimit, rule: Rule, reset: string | undefined) {
  const target = w.percentUsed >= rule.high ? rule.high : w.percentUsed >= rule.low ? rule.low : 0
  if (target === 0) return
  const window = w.resetsAt ?? 'sem-reset'
  const prev = (await $.store.get(rule.storeKey)) as Toasted | undefined
  const level = prev?.window === window ? prev.level : 0
  if (target <= level) return
  // ponytail: pular direto do nível baixo para o alto mostra só o aviso alto (o mais útil); o baixo não sai depois.
  $.ui.toast(rule.text(target, reset ? ` (reset ${reset})` : ''), { timeoutMs: 10000 })
  await $.store.set(rule.storeKey, { window, level: target } satisfies Toasted)
}

async function showAndWarn($: EngineInterface, rateLimits: readonly SessionRateLimit[]) {
  const five = rateLimits.find(w => w.kind === 'five_hour')
  const week = rateLimits.find(w => w.kind === 'seven_day')
  if (five === undefined && week === undefined) {
    $.ui.status(undefined)
    return
  }
  const fiveReset = formatReset(five?.resetsAt)
  const weekReset = formatReset(week?.resetsAt, true)
  // O reset mostrado é o da janela de 5h; só com a semanal, o dela (com dia).
  const reset = five ? fiveReset : weekReset
  const parts = [
    five && `5h ${Math.round(five.percentUsed)}%`,
    week && `sem ${Math.round(week.percentUsed)}%`,
    reset && `reset ${reset}`,
  ].filter(Boolean)
  $.ui.status(`Claude ${parts.join(' · ')}`)

  if (five) await warnOnce($, five, FIVE_HOUR, fiveReset)
  if (week) await warnOnce($, week, SEVEN_DAY, weekReset)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    const { rateLimits } = await $.session.usage()
    // Na largada a lista costuma vir vazia (nenhuma resposta da API ainda). Não grava
    // "unknown" aqui para não sobrescrever um arquivo bom escrito por outra sessão;
    // o primeiro session.measure grava o estado real.
    if (rateLimits.length > 0) {
      await showAndWarn($, rateLimits)
      await writeQuota($, rateLimits, 'session.start via $.session.usage()')
    }
    return result
  })

  on('session.measure', async ($, e, next) => {
    await showAndWarn($, e.rateLimits)
    await writeQuota($, e.rateLimits, 'session.measure')
    return next(e)
  })
}
