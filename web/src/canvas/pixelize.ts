import type { RGB, Cell } from './grid'

export interface PixelView { width: number; height: number; data: Uint8ClampedArray }
export type PixelizeMethod = 'mode' | 'nearest' | 'smooth'
export interface PixelizeOptions {
  size: number // 8–16, 输出高度
  method: PixelizeMethod
  snap: boolean
  invert: boolean
  palette: RGB[]
}
export interface PixelBlock { w: number; h: number; cells: Cell[][] }

function isBg(p: number[]): boolean {
  return p[3] < 100 || Math.min(p[0], p[1], p[2]) > 200
}
function nearest(p: number[], pal: RGB[]): RGB {
  let bd = 1e9
  let bc = pal[0]
  for (const c of pal) {
    const d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
    if (d < bd) { bd = d; bc = c }
  }
  return bc
}

// 求非背景包围盒 → 按 size 缩放(宽≤16,保持比例)→ 按 method 量化 → 返回小像素块; 全背景返回 null。
export function pixelize(img: PixelView, opts: PixelizeOptions): PixelBlock | null {
  const { width: W, height: H, data } = img
  const px = (x: number, y: number): number[] => {
    const i = (y * W + x) * 4
    return [data[i], data[i + 1], data[i + 2], data[i + 3]]
  }
  let minx = 1e9, miny = 1e9, maxx = -1, maxy = -1
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const p = px(x, y)
    const ct = opts.invert ? p[3] >= 100 && (p[0] + p[1] + p[2]) / 3 < 128 : !isBg(p)
    if (ct) { if (x < minx) minx = x; if (x > maxx) maxx = x; if (y < miny) miny = y; if (y > maxy) maxy = y }
  }
  if (maxx < 0) return null
  const bw = maxx - minx + 1
  const bh = maxy - miny + 1
  const oh = opts.size
  const ow = Math.min(16, Math.round((bw * opts.size) / bh))
  if (ow < 1) return null // 极端窄高比 → 无可用像素块
  const PAL = opts.snap ? opts.palette : null
  const cells: Cell[][] = Array.from({ length: oh }, () => Array<Cell>(ow).fill(null))
  for (let iy = 0; iy < oh; iy++) for (let ix = 0; ix < ow; ix++) {
    const sx0 = minx + Math.floor((ix * bw) / ow)
    const sx1 = Math.max(sx0 + 1, minx + Math.floor(((ix + 1) * bw) / ow))
    const sy0 = miny + Math.floor((iy * bh) / oh)
    const sy1 = Math.max(sy0 + 1, miny + Math.floor(((iy + 1) * bh) / oh))
    let col: RGB | null = null
    if (opts.invert) {
      let dark = 0, bg = 0
      for (let sy = sy0; sy < sy1; sy++) for (let sx = sx0; sx < sx1; sx++) {
        const p = px(sx, sy)
        if (p[3] >= 100 && (p[0] + p[1] + p[2]) / 3 < 128) dark++; else bg++
      }
      if (dark >= bg && dark > 0) col = [255, 255, 255]
    } else if (opts.method === 'mode') {
      let bg = 0
      const votes: Record<string, number> = {}
      for (let sy = sy0; sy < sy1; sy++) for (let sx = sx0; sx < sx1; sx++) {
        const p = px(sx, sy)
        if (isBg(p)) { bg++; continue }
        const c = PAL ? nearest(p, PAL) : ([p[0], p[1], p[2]] as RGB)
        const kk = c.join(',')
        votes[kk] = (votes[kk] || 0) + 1
      }
      let best: string | null = null, bc = 0, tot = 0
      for (const kk in votes) { tot += votes[kk]; if (votes[kk] > bc) { bc = votes[kk]; best = kk } }
      if (tot > bg && best) col = best.split(',').map(Number) as RGB
    } else {
      const cx = (sx0 + sx1) >> 1
      const cy = (sy0 + sy1) >> 1
      const p = px(cx, cy)
      if (!isBg(p)) col = PAL ? nearest(p, PAL) : ([p[0], p[1], p[2]] as RGB)
    }
    if (col) cells[iy][ix] = col
  }
  return { w: ow, h: oh, cells }
}

// 品牌色板(随内置 Logo 预设),数值移植自 logo.html palForCurrent()。
export const BRAND_PALETTES: Record<string, RGB[]> = {
  MSFT: [[242, 80, 34], [127, 186, 0], [0, 164, 239], [255, 185, 0]],
  GOOGL: [[234, 67, 53], [251, 188, 5], [52, 168, 83], [66, 133, 244]],
  NVDA: [[118, 185, 0]],
  AAPL: [[255, 255, 255]],
}
