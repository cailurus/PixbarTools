<script setup lang="ts">
import type { OptSpec } from '../types'
import OptionField from './OptionField.vue'
defineProps<{ name: string; optspec: OptSpec[]; options: Record<string, string | number> }>()
const emit = defineEmits<{
  (e: 'change', payload: { key: string; value: string }): void
  (e: 'open-search', spec: OptSpec): void
  (e: 'close'): void
}>()
function isWide(o: OptSpec) { return o.type === 'text' || o.type === 'search' }
</script>

<template>
  <div class="backdrop" @click.self="emit('close')">
    <div class="modal">
      <div class="head"><h3>{{ name }} · 参数</h3><button class="x" @click="emit('close')">&times;</button></div>
      <div class="grid">
        <div v-for="o in optspec" :key="o.key" class="cell" :class="{ wide: isWide(o) }">
          <OptionField :spec="o" :value="options[o.key]" compact
            @change="(v) => emit('change', { key: o.key, value: v })" @open-search="(s) => emit('open-search', s)" />
        </div>
      </div>
      <div class="foot">
        <span class="hint">改动即时生效并保存</span>
        <button class="primary" @click="emit('close')">完成</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.backdrop{position:fixed;inset:0;background:rgba(4,6,9,.55);display:flex;align-items:center;justify-content:center;z-index:46;padding:16px}
.modal{width:380px;max-width:calc(100vw - 32px);background:var(--bg-1);border:1px solid var(--line-2);border-radius:14px;padding:18px}
.head{display:flex;align-items:center;justify-content:space-between;margin-bottom:15px}
.head h3{font-family:var(--display);font-weight:700;font-size:var(--fs-h2);margin:0}
.x{background:none;border:0;color:var(--ink-3);font-size:22px;cursor:pointer;line-height:1}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px 14px}
.cell.wide{grid-column:1/-1}
.foot{display:flex;align-items:center;justify-content:space-between;margin-top:18px}
.hint{font-size:var(--fs-small);color:var(--ink-3)}
.primary{cursor:pointer;border-radius:8px;border:1px solid var(--btn-accent);background:var(--btn-accent);color:var(--on-accent);padding:7px 16px;font-weight:600}
.primary:hover{background:var(--btn-accent-h)}
</style>
