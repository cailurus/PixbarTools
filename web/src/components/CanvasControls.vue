<script setup lang="ts">
import { useCanvas, PRESET, type Tool } from '../canvas/useCanvas'
import type { RGB } from '../canvas/grid'

const c = useCanvas()
const TOOLS: { k: Tool; label: string }[] = [
  { k: 'pen', label: '画笔' }, { k: 'eraser', label: '橡皮' }, { k: 'select', label: '选择' },
  { k: 'text', label: '文字' }, { k: 'image', label: '图片' },
]
const SCALES = [8, 12, 16, 20]
const exportScale = { value: 12 }

function rgbCss(c2: RGB) { return `rgb(${c2[0]},${c2[1]},${c2[2]})` }
function onCustom(e: Event) {
  const h = (e.target as HTMLInputElement).value
  c.setColor([parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)])
}
function onScale(e: Event) { exportScale.value = parseInt((e.target as HTMLSelectElement).value, 10) }
function isActiveColor(p: RGB) { return c.color.value[0] === p[0] && c.color.value[1] === p[1] && c.color.value[2] === p[2] }
</script>

<template>
  <div class="controls">
    <div class="grouprow">
      <div class="tools">
        <button v-for="t in TOOLS" :key="t.k" class="tool" :class="{ on: c.tool.value === t.k }" @click="c.setTool(t.k)">{{ t.label }}</button>
      </div>
      <div class="palette">
        <span v-for="(p, i) in PRESET" :key="i" class="sw" :class="{ act: isActiveColor(p) }" :style="{ background: rgbCss(p) }" @click="c.setColor(p)"></span>
        <input type="color" value="#00ff66" title="自定义颜色" @input="onCustom" />
      </div>
    </div>

    <div class="grouprow" v-if="c.tool.value === 'text'">
      <label class="fld">文字 <input type="text" v-model="c.textValue.value" placeholder="ASCII 文字" /></label>
      <label class="fld">字高
        <select v-model.number="c.fontHeight.value"><option :value="10">10px</option><option :value="5">5px</option></select>
      </label>
      <span class="hint">选「文字」后,在画布上点一下决定左上角落字。</span>
    </div>

    <div class="grouprow actions">
      <label class="chk"><input type="checkbox" v-model="c.showGrid.value" /> 网格</label>
      <button class="act" @click="c.undo()">撤销</button>
      <button class="act" @click="c.redo()">重做</button>
      <button class="act" @click="c.clear()">清空</button>
      <span class="sep"></span>
      <label class="fld">放大 <select @change="onScale">
        <option v-for="s in SCALES" :key="s" :value="s" :selected="s === 12">{{ s }}×</option>
      </select></label>
      <button class="act" @click="c.exportPng(exportScale.value)">导出 PNG</button>
      <button class="act push" @click="c.pushDevice()">推送设备</button>
    </div>

    <div class="status">{{ c.status.value }}</div>
  </div>
</template>

<style scoped>
.controls{display:flex;flex-direction:column;gap:12px;background:var(--bg-1);border:1px solid var(--line);border-radius:12px;padding:14px}
.grouprow{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.tools{display:flex;gap:4px;background:var(--bg-2);padding:4px;border-radius:10px;border:1px solid var(--line)}
.tool{background:none;border:0;cursor:pointer;font-size:13px;color:var(--ink-2);padding:6px 12px;border-radius:7px}
.tool:hover{color:var(--ink)}
.tool.on{background:var(--bg-1);color:var(--signal);box-shadow:0 0 0 1px var(--signal-dim)}
.palette{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.sw{width:20px;height:20px;border:2px solid var(--line-2);border-radius:4px;cursor:pointer}
.sw.act{border-color:var(--signal)}
.palette input[type=color]{width:26px;height:24px;border:1px solid var(--line-2);border-radius:5px;background:var(--bg-2);cursor:pointer;padding:0}
.fld{display:flex;align-items:center;gap:6px;color:var(--ink-2);font-size:var(--fs-body)}
.fld input[type=text]{width:150px}
input[type=text],select{background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:7px;padding:6px 8px;font-family:var(--mono);font-size:var(--fs-body)}
.actions{border-top:1px solid var(--line);padding-top:12px}
.chk{display:flex;align-items:center;gap:5px;color:var(--ink-2);font-size:var(--fs-body)}
.act{cursor:pointer;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink);padding:6px 12px;border-radius:8px;font-weight:500;font-size:var(--fs-body)}
.act:hover{background:var(--bg-3)}
.act.push{border-color:var(--signal-dim);color:var(--signal)}
.sep{flex:1}
.hint{font-size:var(--fs-small);color:var(--ink-3)}
.status{font-family:var(--mono);font-size:var(--fs-small);color:var(--signal);min-height:16px}
</style>
