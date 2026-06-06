export type RGB = [number, number, number]
export type Cell = RGB | null
export type Grid = Cell[][] // [y][x], ROWS×COLS
export const COLS = 52
export const ROWS = 16

export function emptyGrid(): Grid {
  return Array.from({ length: ROWS }, () => Array<Cell>(COLS).fill(null))
}

export function cloneGrid(g: Grid): Grid {
  return g.map((row) => row.map((c) => (c ? ([c[0], c[1], c[2]] as RGB) : null)))
}

export function packColor(c: RGB): number {
  return ((c[0] & 255) << 16) | ((c[1] & 255) << 8) | (c[2] & 255)
}

export function flatten(g: Grid): number[] {
  const out: number[] = []
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
    const c = g[y][x]
    out.push(c ? packColor(c) : 0)
  }
  return out
}

export function setPx(g: Grid, x: number, y: number, col: Cell): void {
  if (x >= 0 && y >= 0 && x < COLS && y < ROWS) g[y][x] = col
}

export function drawGrid(ctx: CanvasRenderingContext2D, g: Grid, cell: number): void {
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
    const c = g[y][x]
    ctx.fillStyle = c ? `rgb(${c[0]},${c[1]},${c[2]})` : '#000'
    ctx.fillRect(x * cell, y * cell, cell, cell)
  }
}

export function exportPngDataUrl(g: Grid, scale: number): string {
  const out = document.createElement('canvas')
  out.width = COLS * scale
  out.height = ROWS * scale
  const o = out.getContext('2d')!
  o.fillStyle = '#000'
  o.fillRect(0, 0, out.width, out.height)
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
    const c = g[y][x]
    if (c) { o.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`; o.fillRect(x * scale, y * scale, scale, scale) }
  }
  return out.toDataURL()
}
