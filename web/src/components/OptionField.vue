<script setup lang="ts">
import { ref, watch } from 'vue'
import type { OptSpec } from '../types'
const props = defineProps<{ spec: OptSpec; value: string | number; compact?: boolean }>()
const emit = defineEmits<{
  (e: 'change', v: string): void
  (e: 'open-search', spec: OptSpec): void
}>()
// 文本/数字框用本地状态; 只在未编辑时同步外部值, 否则 2.5s 轮询会把正在输入的内容冲掉
const local = ref(String(props.value ?? ''))
const editing = ref(false)
watch(() => props.value, (v) => { if (!editing.value) local.value = String(v ?? '') })
function display(v: string | number): string {
  return typeof v === 'string' && v.includes('|') ? v.split('|').slice(2).join('|') : String(v)
}
function submit() { emit('change', local.value) }
function onBlur() { editing.value = false; submit() }
function onSelect(e: Event) { emit('change', (e.target as HTMLSelectElement).value) }
</script>

<template>
  <div class="opt" :class="{ compact }">
    <label>{{ spec.label }}</label>
    <template v-if="spec.type === 'search'">
      <button class="opt-search" @click="emit('open-search', spec)">
        <span class="os-val">{{ display(value) || '—' }}</span><span class="os-act">更改</span>
      </button>
    </template>
    <template v-else-if="spec.type === 'text'">
      <input type="text" v-model="local" @focus="editing = true" @blur="onBlur" @keydown.enter="submit" />
    </template>
    <template v-else-if="spec.type === 'number'">
      <input class="num" type="number" :min="spec.min" :max="spec.max" v-model="local"
        @focus="editing = true" @blur="onBlur" @keydown.enter="submit" />
    </template>
    <template v-else>
      <select :value="value" @change="onSelect">
        <option v-for="c in spec.choices || []" :key="c[0]" :value="c[0]">{{ c[1] }}</option>
      </select>
    </template>
  </div>
</template>

<style scoped>
.opt{display:flex;align-items:center;gap:9px;flex-wrap:wrap;font-size:var(--fs-body);color:var(--ink-2);margin-top:11px}
.opt label{flex:none}
input,select{background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:7px 9px;font-family:var(--mono);font-size:var(--fs-body)}
input[type=text]{flex:1;min-width:120px}
.num{width:84px}
select{appearance:none;padding-right:28px;cursor:pointer}
input:focus-visible,select:focus-visible{outline:none;border-color:var(--signal);box-shadow:0 0 0 3px var(--signal-glow)}
.opt-search{flex:1;min-width:160px;display:inline-flex;align-items:center;justify-content:space-between;gap:10px;text-align:left;cursor:pointer;background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:7px 11px}
.opt-search .os-act{font-size:var(--fs-micro);color:var(--ink-3);font-family:var(--mono);letter-spacing:.1em}
/* 紧凑模式(弹窗内): 标签在上, 控件占满单元格 */
.opt.compact{flex-direction:column;align-items:stretch;gap:5px;margin-top:0}
.opt.compact label{font-size:var(--fs-small);color:var(--ink-3)}
.opt.compact input[type=text],.opt.compact .num,.opt.compact select,.opt.compact .opt-search{width:100%;min-width:0;flex:none}
</style>
