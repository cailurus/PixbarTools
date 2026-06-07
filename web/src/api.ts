import type { Status, GeoResult } from './types'

const post = (url: string) => fetch(url, { method: 'POST' })
const enc = encodeURIComponent

export const api = {
  getStatus: (): Promise<Status> => fetch('/api/status').then((r) => r.json()),
  setDevice: (ip: string) => post(`/api/device?ip=${enc(ip)}`),
  toggle: (app: string, on: boolean, interval: number) =>
    post(`/api/toggle?app=${enc(app)}&on=${on ? 1 : 0}&interval=${interval}`),
  pushOnce: (app: string) => post(`/api/pushonce?app=${enc(app)}`),
  setInterval: (app: string, interval: number) =>
    post(`/api/interval?app=${enc(app)}&interval=${interval}`),
  setOption: (app: string, key: string, value: string | number) =>
    post(`/api/option?app=${enc(app)}&key=${enc(key)}&value=${enc(String(value))}`),
  attachAdd: (host: string, type: string) => post(`/api/attach/add?host=${enc(host)}&type=${enc(type)}`),
  attachRemove: (id: string) => post(`/api/attach/remove?id=${enc(id)}`),
  attachToggle: (id: string, on: boolean) => post(`/api/attach/toggle?id=${enc(id)}&on=${on ? 1 : 0}`),
  attachOption: (id: string, key: string, value: string | number) =>
    post(`/api/attach/option?id=${enc(id)}&key=${enc(key)}&value=${enc(String(value))}`),
  geocode: (q: string): Promise<{ results: GeoResult[] }> =>
    fetch(`/api/geocode?q=${enc(q)}`).then((r) => r.json()),
  pushCanvas: (pixels: number[], duration = 10) =>
    fetch('/api/canvas/push', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pixels, duration }),
    }),
}
