import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '../api'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ json: async () => ({ ok: true }) })) as unknown as typeof fetch)
})

describe('api', () => {
  it('getStatus hits /api/status', async () => {
    await api.getStatus()
    expect(fetch).toHaveBeenCalledWith('/api/status')
  })
  it('setOption encodes value', async () => {
    await api.setOption('weather', 'location', 'a|b|杭州, 浙江')
    const url = (fetch as unknown as { mock: { calls: string[][] } }).mock.calls[0][0]
    expect(url).toContain('/api/option?app=weather&key=location&value=')
    expect(url).toContain(encodeURIComponent('a|b|杭州, 浙江'))
  })
})
