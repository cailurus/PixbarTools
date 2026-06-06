import { describe, it, expect } from 'vitest'
import { pixelize, type PixelView } from '../canvas/pixelize'
import { SOURCES } from '../canvas/logoSources'

function solid(w: number, h: number, rgba: [number, number, number, number]): PixelView {
  const data = new Uint8ClampedArray(w * h * 4)
  for (let i = 0; i < w * h; i++) {
    data[i * 4] = rgba[0]; data[i * 4 + 1] = rgba[1]; data[i * 4 + 2] = rgba[2]; data[i * 4 + 3] = rgba[3]
  }
  return { width: w, height: h, data }
}

describe('pixelize', () => {
  it('纯红方块 → 同色块', () => {
    const b = pixelize(solid(4, 4, [255, 0, 0, 255]), { size: 4, method: 'nearest', snap: false, invert: false, palette: [] })!
    expect(b.w).toBe(4)
    expect(b.h).toBe(4)
    expect(b.cells[0][0]).toEqual([255, 0, 0])
  })
  it('全透明(背景)→ null', () => {
    expect(pixelize(solid(4, 4, [0, 0, 0, 0]), { size: 4, method: 'nearest', snap: false, invert: false, palette: [] })).toBeNull()
  })
  it('snap 吸附到调色板最近色', () => {
    // 接近红的不纯色 (250,8,4) 应吸附到调色板里的纯红 [255,0,0]
    const b = pixelize(solid(4, 4, [250, 8, 4, 255]), { size: 4, method: 'nearest', snap: true, invert: false, palette: [[255, 0, 0], [0, 0, 255]] })!
    expect(b.cells[0][0]).toEqual([255, 0, 0])
  })
})

describe('logoSources', () => {
  it('含 4 个内置 Logo, 均为 data URL', () => {
    for (const k of ['AAPL', 'MSFT', 'NVDA', 'GOOGL']) {
      expect(typeof SOURCES[k]).toBe('string')
      expect(SOURCES[k].startsWith('data:image/')).toBe(true)
    }
  })
})
