import { describe, it, expect } from 'vitest'
import { renderText } from '../canvas/font'

describe('renderText', () => {
  it("'A' 5px: 宽3 高5, 首行 ### 点亮", () => {
    const r = renderText('A', 5)
    expect(r.w).toBe(3)
    expect(r.h).toBe(5)
    expect(Array.from(r.on.slice(0, 3))).toEqual([1, 1, 1])
    expect(Array.from(r.on.slice(3, 6))).toEqual([1, 0, 1]) // 第二行 #.#
  })
  it('字高 10 放大 2×', () => {
    const r = renderText('A', 10)
    expect(r.w).toBe(6)
    expect(r.h).toBe(10)
  })
  it('空串宽 0', () => {
    expect(renderText('', 5).w).toBe(0)
  })
  it('小写映射到大写', () => {
    const lo = renderText('a', 5)
    const up = renderText('A', 5)
    expect(Array.from(lo.on)).toEqual(Array.from(up.on))
  })
})
