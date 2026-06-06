import { ref } from 'vue'
import type { Grid, RGB, Cell } from './grid'
import { emptyGrid, cloneGrid, flatten, setPx, exportPngDataUrl } from './grid'
import { renderText } from './font'
import { api } from '../api'

export type Tool = 'pen' | 'eraser' | 'select' | 'text' | 'image'
export interface Sel { x: number; y: number; w: number; h: number }

// 调色板(并入两个工具的预设:sketch + logo 去重)
export const PRESET: RGB[] = [
  [255, 255, 255], [0, 255, 102], [255, 48, 48], [255, 208, 0], [66, 133, 244], [242, 80, 34],
  [52, 168, 83], [0, 164, 239], [154, 160, 166], [234, 67, 53], [255, 185, 0], [0, 0, 0],
]

// ---- 模块级单例响应式状态 ----
const grid = ref<Grid>(emptyGrid())
const version = ref(0) // 网格变更计数, 供组件重绘
const tool = ref<Tool>('pen')
const color = ref<RGB>([0, 255, 102])
const showGrid = ref(true)
const status = ref('左键画、右键擦;先选颜色或用自定义取色。')
const sel = ref<Sel | null>(null)
const textValue = ref('CPU 45%')
const fontHeight = ref(10)
const undoStack: Grid[] = []
const redoStack: Grid[] = []

function bump() { version.value++ }
function snapshot() {
  undoStack.push(cloneGrid(grid.value))
  redoStack.length = 0
  if (undoStack.length > 50) undoStack.shift()
}
function undo() {
  if (!undoStack.length) return
  redoStack.push(cloneGrid(grid.value))
  grid.value = undoStack.pop()!
  sel.value = null
  bump()
  status.value = '已撤销'
}
function redo() {
  if (!redoStack.length) return
  undoStack.push(cloneGrid(grid.value))
  grid.value = redoStack.pop()!
  sel.value = null
  bump()
  status.value = '已重做'
}
function setColor(c: RGB) {
  color.value = c
  if (tool.value !== 'select') tool.value = 'pen'
}
function setTool(t: Tool) { tool.value = t; sel.value = null; bump() }
function clear() { snapshot(); grid.value = emptyGrid(); sel.value = null; bump(); status.value = '已清空' }
function paintPx(x: number, y: number, erase: boolean) {
  setPx(grid.value, x, y, erase ? null : ([color.value[0], color.value[1], color.value[2]] as RGB))
  bump()
}
function placeText(x: number, y: number) {
  const t = textValue.value
  if (!t) { status.value = '先输入文字'; return }
  const b = renderText(t, fontHeight.value)
  if (!b.on.some((v) => v)) { status.value = '无可显示字符(设备字体仅支持 ASCII)'; return }
  snapshot()
  for (let j = 0; j < b.h; j++) for (let i = 0; i < b.w; i++) {
    if (b.on[j * b.w + i]) setPx(grid.value, x + i, y + j, [color.value[0], color.value[1], color.value[2]])
  }
  bump()
  status.value = `已落字 "${t}" @ (${x},${y}),可用画笔继续修改`
}
function placeBlock(cells: Cell[][], x: number, y: number) {
  snapshot()
  for (let j = 0; j < cells.length; j++) for (let i = 0; i < cells[j].length; i++) {
    const c = cells[j][i]
    if (c) setPx(grid.value, x + i, y + j, [c[0], c[1], c[2]])
  }
  sel.value = { x, y, w: cells[0]?.length || 0, h: cells.length }
  tool.value = 'select'
  bump()
  status.value = '已落图,切到「选择」可拖动整体搬移'
}
async function pushDevice() {
  status.value = '推送中…'
  try {
    const r = await api.pushCanvas(flatten(grid.value))
    const j = await r.json()
    status.value = j.ok ? '已推送到设备(DIY 组件 canvas)' : '推送失败:' + (j.error || '设备无响应')
  } catch {
    status.value = '推送失败:控制服务器无响应'
  }
}
function exportPng(scale: number) {
  const a = document.createElement('a')
  a.download = 'pixbar_canvas.png'
  a.href = exportPngDataUrl(grid.value, scale)
  a.click()
  status.value = '已导出 pixbar_canvas.png'
}

export function useCanvas() {
  return {
    grid, version, tool, color, showGrid, status, sel, textValue, fontHeight,
    snapshot, bump, undo, redo, setColor, setTool, clear, paintPx, placeText, placeBlock, pushDevice, exportPng,
  }
}
