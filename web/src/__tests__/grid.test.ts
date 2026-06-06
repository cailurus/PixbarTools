import { describe, it, expect } from 'vitest'
import { emptyGrid, cloneGrid, packColor, flatten, setPx, COLS, ROWS } from '../canvas/grid'

describe('grid', () => {
  it('emptyGrid 是 ROWS×COLS 的 null', () => {
    const g = emptyGrid()
    expect(g.length).toBe(ROWS)
    expect(g[0].length).toBe(COLS)
    expect(g[0][0]).toBeNull()
  })
  it('packColor 打成 0x00RRGGBB', () => {
    expect(packColor([255, 0, 102])).toBe(0xff0066)
    expect(packColor([0, 0, 0])).toBe(0)
  })
  it('flatten 行优先长度 832, null→0', () => {
    const g = emptyGrid()
    setPx(g, 1, 0, [255, 0, 0])
    const f = flatten(g)
    expect(f.length).toBe(832)
    expect(f[0]).toBe(0)
    expect(f[1]).toBe(0xff0000)
  })
  it('cloneGrid 深拷贝', () => {
    const g = emptyGrid()
    setPx(g, 0, 0, [1, 2, 3])
    const c = cloneGrid(g)
    setPx(g, 0, 0, [9, 9, 9])
    expect(c[0][0]).toEqual([1, 2, 3])
  })
})
