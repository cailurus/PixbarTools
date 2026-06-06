import { describe, it, expect } from 'vitest'
import { useCanvas } from '../canvas/useCanvas'
import { flatten, packColor } from '../canvas/grid'

describe('useCanvas 撤销/重做', () => {
  it('快照→落像素→撤销回退→重做重放', () => {
    const c = useCanvas()
    c.clear() // 重置网格(单例)
    c.setColor([10, 20, 30])
    c.snapshot()
    c.paintPx(2, 0, false)
    expect(flatten(c.grid.value)[2]).toBe(packColor([10, 20, 30]))
    c.undo()
    expect(flatten(c.grid.value)[2]).toBe(0)
    c.redo()
    expect(flatten(c.grid.value)[2]).toBe(packColor([10, 20, 30]))
  })
  it('落图块后选区尺寸正确', () => {
    const c = useCanvas()
    c.clear()
    c.placeBlock([[[1, 2, 3], null], [[4, 5, 6], [7, 8, 9]]], 0, 0)
    expect(c.sel.value).toEqual({ x: 0, y: 0, w: 2, h: 2 })
    expect(flatten(c.grid.value)[0]).toBe(packColor([1, 2, 3]))
  })
  it('落不可显示的文字不产生幽灵撤销', () => {
    const c = useCanvas()
    c.clear()
    c.setColor([10, 20, 30])
    c.snapshot() // 保存空白基线 S0
    c.paintPx(5, 0, false) // 画标记 → S1
    expect(flatten(c.grid.value)[5]).toBe(packColor([10, 20, 30]))
    c.textValue.value = '你好' // CJK → 设备字体无字形, 全空
    c.placeText(0, 0) // 修复后: 不快照; 误快照则会把 S1 压栈
    c.undo() // 应弹回 S0(标记消失); 若 placeText 误快照则弹回 S1(标记仍在)
    expect(flatten(c.grid.value)[5]).toBe(0)
  })
})
