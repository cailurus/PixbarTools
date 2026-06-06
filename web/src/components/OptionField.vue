<script setup lang="ts">
import type { OptSpec } from '../types'
const props = defineProps<{ spec: OptSpec; value: string | number }>()
const emit = defineEmits<{
  (e: 'change', v: string): void
  (e: 'open-search', spec: OptSpec): void
}>()
function display(v: string | number): string {
  return typeof v === 'string' && v.includes('|') ? v.split('|').slice(2).join('|') : String(v)
}
function onText(e: Event) { emit('change', (e.target as HTMLInputElement).value) }
function onSelect(e: Event) { emit('change', (e.target as HTMLSelectElement).value) }
void props
</script>

<template>
  <div class="opt">
    <label>{{ spec.label }}</label>
    <template v-if="spec.type === 'search'">
      <button class="opt-search" @click="emit('open-search', spec)">
        <span class="os-val">{{ display(value) || '—' }}</span><span class="os-act">更改</span>
      </button>
    </template>
    <template v-else-if="spec.type === 'text'">
      <input type="text" :value="value" @change="onText" />
    </template>
    <template v-else-if="spec.type === 'number'">
      <input type="number" :min="spec.min" :max="spec.max" :value="value" @change="onText" style="width:84px" />
    </template>
    <template v-else>
      <select :value="value" @change="onSelect">
        <option v-for="c in spec.choices || []" :key="c[0]" :value="c[0]">{{ c[1] }}</option>
      </select>
    </template>
  </div>
</template>

<style scoped>
.opt{display:flex;align-items:center;gap:9px;font-size:var(--fs-body);color:var(--ink-2);margin-top:11px}
.opt label{flex:none}
input,select{background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:7px 9px;font-family:var(--mono);font-size:var(--fs-body)}
input[type=text]{flex:1;min-width:140px}
select{appearance:none;padding-right:28px;cursor:pointer}
input:focus-visible,select:focus-visible{outline:none;border-color:var(--signal);box-shadow:0 0 0 3px var(--signal-glow)}
.opt-search{flex:1;min-width:160px;display:inline-flex;align-items:center;justify-content:space-between;gap:10px;text-align:left;cursor:pointer;background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:7px 11px}
.opt-search .os-act{font-size:var(--fs-micro);color:var(--ink-3);font-family:var(--mono);letter-spacing:.1em}
</style>
