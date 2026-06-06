<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useCanvas } from '../canvas/useCanvas'
import { COLS, ROWS, drawGrid, setPx, type Cell } from '../canvas/grid'

const CELL = 14
const c = useCanvas()
const canvas = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null

// 框选/搬移本地状态(移植自 sketch.html)
let painting = false
let dragErase = false
let marq: { x0: number; y0: number; x1: number; y1: number } | null = null
let mv: { buf: Cell[]; w: number; h: number; gx: number; gy: number; curx: number; cury: number } | null = null
const coord = ref('')

function cellAt(e: MouseEvent): [number, number] {
  const r = canvas.value!.getBoundingClientRect()
  return [Math.floor((e.clientX - r.left) / CELL), Math.floor((e.clientY - r.top) / CELL)]
}
function dashRect(x: number, y: number, w: number, h: number) {
  ctx!.save(); ctx!.strokeStyle = '#0a84ff'; ctx!.lineWidth = 2; ctx!.setLineDash([6, 4])
  ctx!.strokeRect(x * CELL + 1, y * CELL + 1, w * CELL - 2, h * CELL - 2); ctx!.restore()
}
function redraw() {
  if (!ctx) return
  ctx.clearRect(0, 0, canvas.value!.width, canvas.value!.height)
  drawGrid(ctx, c.grid.value, CELL)
  if (c.showGrid.value) {
    ctx.strokeStyle = '#222'; ctx.lineWidth = 1
    for (let x = 0; x <= COLS; x++) { ctx.beginPath(); ctx.moveTo(x * CELL + 0.5, 0); ctx.lineTo(x * CELL + 0.5, ROWS * CELL); ctx.stroke() }
    for (let y = 0; y <= ROWS; y++) { ctx.beginPath(); ctx.moveTo(0, y * CELL + 0.5); ctx.lineTo(COLS * CELL, y * CELL + 0.5); ctx.stroke() }
  }
  if (mv) {
    const ox = mv.curx - mv.gx, oy = mv.cury - mv.gy
    for (let j = 0; j < mv.h; j++) for (let i = 0; i < mv.w; i++) {
      const col = mv.buf[j * mv.w + i]
      if (col) { ctx.fillStyle = `rgb(${col[0]},${col[1]},${col[2]})`; ctx.fillRect((ox + i) * CELL, (oy + j) * CELL, CELL, CELL) }
    }
    dashRect(ox, oy, mv.w, mv.h)
  } else if (c.sel.value) {
    dashRect(c.sel.value.x, c.sel.value.y, c.sel.value.w, c.sel.value.h)
  }
  if (marq) {
    const x0 = Math.min(marq.x0, marq.x1), y0 = Math.min(marq.y0, marq.y1)
    const w = Math.abs(marq.x1 - marq.x0) + 1, h = Math.abs(marq.y1 - marq.y0) + 1
    dashRect(x0, y0, w, h)
  }
}
function inSel(x: number, y: number): boolean {
  const s = c.sel.value
  return !!s && x >= s.x && y >= s.y && x < s.x + s.w && y < s.y + s.h
}

function onDown(e: MouseEvent) {
  const [x, y] = cellAt(e)
  if (c.tool.value === 'text') { c.placeText(x, y); return }
  if (c.tool.value === 'image') return // 图片落块由面板按钮触发
  if (c.tool.value === 'select') {
    if (inSel(x, y)) {
      const s = c.sel.value!
      c.snapshot() // 搬移可撤销: 在剪下源像素前快照
      const buf: Cell[] = []
      for (let j = 0; j < s.h; j++) for (let i = 0; i < s.w; i++) { buf.push(c.grid.value[s.y + j][s.x + i]); setPx(c.grid.value, s.x + i, s.y + j, null) }
      mv = { buf, w: s.w, h: s.h, gx: x - s.x, gy: y - s.y, curx: x, cury: y }
    } else {
      marq = { x0: x, y0: y, x1: x, y1: y }
    }
    redraw(); return
  }
  // pen / eraser
  c.snapshot()
  painting = true
  dragErase = e.button === 2 || c.tool.value === 'eraser'
  c.paintPx(x, y, dragErase)
}
function onMove(e: MouseEvent) {
  const [x, y] = cellAt(e)
  coord.value = x >= 0 && y >= 0 && x < COLS && y < ROWS ? `(${x}, ${y})` : ''
  if (c.tool.value === 'select') {
    if (mv) { mv.curx = x; mv.cury = y; redraw() } else if (marq) { marq.x1 = x; marq.y1 = y; redraw() }
    return
  }
  if (painting) c.paintPx(x, y, dragErase)
}
function onUp() {
  painting = false
  // mv/marq 无条件结算: 即便拖拽中途切换工具, 也要把剪下的像素贴回, 不残留搬移缓冲
  if (mv) {
    const ox = mv.curx - mv.gx, oy = mv.cury - mv.gy
    for (let j = 0; j < mv.h; j++) for (let i = 0; i < mv.w; i++) { const col = mv.buf[j * mv.w + i]; if (col) setPx(c.grid.value, ox + i, oy + j, [col[0], col[1], col[2]]) }
    c.sel.value = { x: ox, y: oy, w: mv.w, h: mv.h }
    mv = null; c.bump(); c.status.value = '已搬移选区'
  } else if (marq) {
    const x0 = Math.max(0, Math.min(marq.x0, marq.x1)), y0 = Math.max(0, Math.min(marq.y0, marq.y1))
    const x1 = Math.min(COLS - 1, Math.max(marq.x0, marq.x1)), y1 = Math.min(ROWS - 1, Math.max(marq.y0, marq.y1))
    if (x1 >= x0 && y1 >= y0) { c.sel.value = { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 }; c.status.value = `已框选 ${x1 - x0 + 1}×${y1 - y0 + 1},在选区内拖动可搬移` } else c.sel.value = null
    marq = null; redraw()
  }
}
function onContext(e: MouseEvent) {
  e.preventDefault()
  if (c.tool.value === 'pen' || c.tool.value === 'eraser') {
    const [x, y] = cellAt(e); c.snapshot(); c.paintPx(x, y, true)
  }
}

onMounted(() => {
  ctx = canvas.value!.getContext('2d')
  redraw()
  window.addEventListener('mouseup', onUp)
})
onUnmounted(() => window.removeEventListener('mouseup', onUp))
watch(() => [c.version.value, c.showGrid.value], redraw)
</script>

<template>
  <div class="stagewrap">
    <div class="bar"><span class="lbl">画布 52×16</span><span class="coord">{{ coord }}</span></div>
    <canvas ref="canvas" :width="COLS * CELL" :height="ROWS * CELL" class="stage"
      @mousedown="onDown" @mousemove="onMove" @contextmenu="onContext"></canvas>
  </div>
</template>

<style scoped>
.stagewrap{display:flex;flex-direction:column;gap:8px}
.bar{display:flex;align-items:center;gap:10px}
.lbl{font-family:var(--mono);font-size:var(--fs-micro);letter-spacing:.18em;text-transform:uppercase;color:var(--ink-3)}
.coord{font-family:var(--mono);font-size:var(--fs-micro);color:var(--ink-2)}
.stage{background:#000;border:1px solid var(--line);border-radius:6px;image-rendering:pixelated;cursor:crosshair;max-width:100%}
</style>
