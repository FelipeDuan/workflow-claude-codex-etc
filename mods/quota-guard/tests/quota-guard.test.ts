import type { On, SessionRateLimit } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'

const HOME = '/home/tester'
const FILE = `${HOME}/.local/state/ai-os/quota/claude.json`
const RESET = '2026-10-22T17:20:00.000Z'
const NOW = Date.parse('2026-10-22T13:00:00.000Z')

// Monta o "engine" de mentira por baixo do mod e devolve o que ele registrou.
function world(on: On) {
  const writes: { path: string; text: string }[] = []
  const toasts: string[] = []
  const statuses: (string | undefined)[] = []
  mock.env(on, { HOME })
  mock.store(on)
  mock.clock(on, { now: NOW })
  on('fs.write', (_, e) => (writes.push(e), { value: undefined }))
  on('ui.toast', (_, e) => (toasts.push(e.text), { value: undefined }))
  on('ui.status', (_, e) => (statuses.push(e.text), { value: undefined }))
  on('session.measure', (_, e) => ({ changed: e.changed }))
  return { writes, toasts, statuses }
}

const five = (percentUsed: number, resetsAt = RESET): SessionRateLimit => ({
  kind: 'five_hour',
  percentUsed,
  resetsAt,
})

const measure = (rateLimits: SessionRateLimit[]) => ({
  context: { window: 200000 },
  rateLimits,
  changed: ['rateLimits' as const],
})

const lastJson = (writes: { path: string; text: string }[]) => JSON.parse(writes.at(-1)!.text)

const localHHMM = (iso: string) => {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

test('abaixo de 85%: grava o arquivo, mostra status, sem toast', async ($, on) => {
  const w = world(on)
  await $.session.measure(
    measure([five(40), { kind: 'seven_day', percentUsed: 12.5, resetsAt: '2026-10-27T00:00:00.000Z' }]),
  )

  expect(w.writes.length).toBe(1)
  expect(w.writes[0]!.path).toBe(FILE)
  expect(lastJson(w.writes)).toEqual({
    provider: 'claude',
    source: 'claude-code-mod',
    fetched_at: new Date(NOW).toISOString(),
    status: 'ok',
    windows: [
      { kind: 'five_hour', used_percent: 40, resets_at: RESET, window_minutes: 300 },
      { kind: 'seven_day', used_percent: 12.5, resets_at: '2026-10-27T00:00:00.000Z', window_minutes: 10080 },
    ],
    note: 'session.measure',
  })
  expect(w.statuses.at(-1)).toBe(`Claude 5h 40% · reset ${localHHMM(RESET)}`)
  expect(w.toasts.length).toBe(0)
})

test('cruzar 85% dá um toast; repetir na mesma janela não duplica; 95% dá o segundo', async ($, on) => {
  const w = world(on)
  await $.session.measure(measure([five(80)]))
  expect(w.toasts.length).toBe(0)

  await $.session.measure(measure([five(86)]))
  expect(w.toasts.length).toBe(1)
  expect(w.toasts[0]).toContain('85% da janela de 5h')
  expect(w.toasts[0]).toContain('Codex/OpenCode')

  await $.session.measure(measure([five(87)]))
  await $.session.measure(measure([five(90)]))
  expect(w.toasts.length).toBe(1)

  await $.session.measure(measure([five(95)]))
  expect(w.toasts.length).toBe(2)
  expect(w.toasts[1]).toContain('nota de estado')

  await $.session.measure(measure([five(97)]))
  expect(w.toasts.length).toBe(2)
  expect(w.writes.length).toBe(6)
})

test('janela nova (outro resetsAt) avisa de novo', async ($, on) => {
  const w = world(on)
  await $.session.measure(measure([five(88)]))
  await $.session.measure(measure([five(88, '2026-10-22T22:20:00.000Z')]))
  expect(w.toasts.length).toBe(2)
})

test('rateLimits vazio: status unknown, windows [], sem status line nem toast', async ($, on) => {
  const w = world(on)
  await $.session.measure(measure([]))

  const json = lastJson(w.writes)
  expect(json.status).toBe('unknown')
  expect(json.windows).toEqual([])
  expect(json.provider).toBe('claude')
  expect(w.statuses.at(-1)).toBe(undefined)
  expect(w.toasts.length).toBe(0)
})

test('session.start lê $.session.usage() e grava quando já há janelas', async ($, on) => {
  const w = world(on)
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.usage', () => ({
    value: { startedAt: NOW, context: { window: 200000 }, rateLimits: [five(50)] },
  }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  expect(lastJson(w.writes).note).toBe('session.start via $.session.usage()')
  expect(w.statuses.at(-1)).toBe(`Claude 5h 50% · reset ${localHHMM(RESET)}`)
})

test('session.start sem leitura ainda não sobrescreve o arquivo', async ($, on) => {
  const w = world(on)
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.usage', () => ({ value: { startedAt: NOW, context: { window: 200000 }, rateLimits: [] } }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(w.writes.length).toBe(0)
})
