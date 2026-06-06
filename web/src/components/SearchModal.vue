<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { api } from '../api'
import type { GeoResult, OptSpec } from '../types'
const props = defineProps<{ spec: OptSpec | null }>()
const emit = defineEmits<{ (e: 'pick', value: string): void; (e: 'close'): void }>()
const q = ref('')
const results = ref<GeoResult[]>([])
const hint = ref('输入后选择匹配的城市（含省份/国家）。')
let timer: number | undefined
watch(q, () => {
  clearTimeout(timer)
  timer = window.setTimeout(run, 300)
})
onUnmounted(() => clearTimeout(timer))
async function run() {
  const s = q.value.trim()
  if (!s) { results.value = []; hint.value = '输入后选择匹配的城市（含省份/国家）。'; return }
  hint.value = '搜索中…'
  try {
    const d = await api.geocode(s)
    results.value = d.results || []
    hint.value = results.value.length ? '' : '没找到，换个写法试试。'
  } catch { hint.value = '搜索失败。' }
}
void props
</script>

<template>
  <div class="backdrop" @click.self="emit('close')">
    <div class="modal">
      <div class="head"><h3>{{ spec?.label }} · 搜索</h3><button class="x" @click="emit('close')">&times;</button></div>
      <input v-model="q" type="text" placeholder="输入城市名搜索…" autocomplete="off" autofocus />
      <div class="results">
        <div v-if="hint" class="muted">{{ hint }}</div>
        <div v-for="r in results" :key="r.value" class="item" @click="emit('pick', r.value)">{{ r.label }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.backdrop{position:fixed;inset:0;background:rgba(4,6,9,.55);display:flex;align-items:center;justify-content:center;z-index:50}
.modal{width:360px;max-width:calc(100vw - 32px);background:var(--bg-1);border:1px solid var(--line-2);border-radius:14px;padding:18px;box-shadow:0 24px 60px -20px rgba(0,0,0,.5)}
.head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.head h3{font-family:var(--display);font-weight:700;font-size:var(--fs-h2);margin:0}
.x{background:none;border:0;color:var(--ink-3);font-size:22px;cursor:pointer}
input{width:100%;background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:8px 10px;margin-bottom:10px;font-family:var(--mono)}
.results{max-height:240px;overflow-y:auto;display:flex;flex-direction:column;gap:3px}
.item{padding:9px 11px;border-radius:8px;cursor:pointer;color:var(--ink-2);border:1px solid transparent}
.item:hover{background:var(--bg-2);color:var(--ink);border-color:var(--line-2)}
.muted{color:var(--ink-3);font-size:var(--fs-small);padding:8px 2px}
</style>
