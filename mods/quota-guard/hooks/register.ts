import type { EngineInterface, Register, SessionRateLimit } from 'claude-code'

// Contrato compartilhado com o leitor do Codex: não mudar campos sem combinar.
const QUOTA_FILE = '.local/state/ai-os/quota/claude.json'
const TOAST_KEY = 'toasted' // { window: resetsAt da janela de 5h, level: 0 | 85 | 95 }

const WINDOW_MINUTES: Record<string, number> = { five_hour: 300, seven_day: 10080 }

type Toasted = { window: string; level: number }

const hhmm = (iso: string | undefined): string | undefined => {
  if (iso === undefined) return undefined
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return undefined
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
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

async function showAndWarn($: EngineInterface, rateLimits: readonly SessionRateLimit[]) {
  const five = rateLimits.find(w => w.kind === 'five_hour')
  if (five === undefined) {
    $.ui.status(undefined)
    return
  }
  const reset = hhmm(five.resetsAt)
  const pct = Math.round(five.percentUsed)
  $.ui.status(`Claude 5h ${pct}%${reset ? ` · reset ${reset}` : ''}`)

  const target = five.percentUsed >= 95 ? 95 : five.percentUsed >= 85 ? 85 : 0
  if (target === 0) return
  const window = five.resetsAt ?? 'sem-reset'
  const prev = (await $.store.get(TOAST_KEY)) as Toasted | undefined
  const level = prev?.window === window ? prev.level : 0
  if (target <= level) return

  const when = reset ? ` (reset ${reset})` : ''
  // ponytail: pular direto de <85 para >=95 mostra só o aviso de 95 (o mais útil); o de 85 não sai depois.
  $.ui.toast(
    target === 95
      ? `Claude em 95% da janela de 5h${when}. Finalize com uma nota de estado (feito, decisões, próximo passo).`
      : `Claude em 85% da janela de 5h${when}. Considere delegar tarefas simples ao Codex/OpenCode.`,
    { timeoutMs: 10000 },
  )
  await $.store.set(TOAST_KEY, { window, level: target } satisfies Toasted)
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
