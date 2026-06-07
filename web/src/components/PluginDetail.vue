<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Status, Runner, OptSpec } from '../types'
import { api } from '../api'
import ToggleSwitch from './ToggleSwitch.vue'
import PluginSettings from './PluginSettings.vue'
import AttachSection from './AttachSection.vue'
const showSettings = ref(false)
const props = defineProps<{
  id: string; status: Status
  intended: Record<string, boolean>
  toggle: (id: string, on: boolean) => void
  toggleAttach: (id: string, on: boolean) => void
  setInterval: (id: string, iv: number) => void
}>()
const emit = defineEmits<{ (e: 'changed'): void; (e: 'open-search', payload: { id: string; spec: OptSpec; kind: 'plugin' | 'attach' }): void }>()
const r = computed<Runner | undefined>(() => props.status.runners[props.id])
const running = computed(() => (props.id in props.intended ? props.intended[props.id] : !!r.value?.running))
// 间隔输入用本地状态: 编辑中不被 2.5s 轮询冲掉; 失焦/回车提交到后端
const ivLocal = ref('')
const ivEditing = ref(false)
watch(() => r.value?.interval, (v) => { if (!ivEditing.value) ivLocal.value = String(v ?? '') }, { immediate: true })
function ivCommit() {
  ivEditing.value = false
  const n = Number(ivLocal.value)
  if (Number.isFinite(n) && n >= 1) props.setInterval(props.id, n)
}
async function once() { await api.pushOnce(props.id); emit('changed') }
async function setOpt(key: string, v: string) { await api.setOption(props.id, key, v); emit('changed') }
</script>

<template>
  <section class="detail card" v-if="r">
    <div class="head">
      <div><h2>{{ r.name }}</h2><div class="rs" :style="{ color: running ? 'var(--signal)' : 'var(--ink-3)' }">{{ running ? '运行中' : '已停止' }}</div></div>
      <ToggleSwitch :model-value="running" @update:model-value="(v) => toggle(id, v)" />
    </div>
    <p v-if="r.desc" class="desc">{{ r.desc }}</p>
    <div class="controls">
      <div class="field"><label>间隔</label><input type="number" min="1" v-model="ivLocal" @focus="ivEditing = true" @blur="ivCommit" @keydown.enter="ivCommit" id="iv" /><span class="unit">秒</span></div>
      <button class="ghost" @click="once">推一次</button>
      <button v-if="r.optspec.length" class="ghost" @click="showSettings = true">⚙ 设置</button>
    </div>
    <pre class="log">{{ (r.log || []).join('\n') || '—' }}</pre>
    <AttachSection :host="id" :status="status" :intended="intended" :toggle-attach="toggleAttach"
      @changed="emit('changed')" @open-search="(p) => emit('open-search', p)" />
    <PluginSettings v-if="showSettings && r.optspec.length" :name="r.name" :optspec="r.optspec" :options="r.options"
      @change="(p) => setOpt(p.key, p.value)" @open-search="(s) => emit('open-search', { id, spec: s, kind: 'plugin' })"
      @close="showSettings = false" />
  </section>
</template>

<style scoped>
.card{background:var(--bg-1);border:1px solid var(--line);border-radius:14px;padding:18px;min-height:280px}
.head{display:flex;align-items:center;justify-content:space-between;gap:12px}
h2{font-family:var(--display);font-weight:700;font-size:var(--fs-h2);margin:0}
.rs{font-family:var(--mono);font-size:var(--fs-micro);letter-spacing:.12em;margin-top:4px}
.desc{color:var(--ink-2);font-size:var(--fs-body);line-height:1.65;margin:14px 0 0}
.controls{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:16px}
.field{display:flex;align-items:center;gap:7px;color:var(--ink-2)}
.field input{width:62px;background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:7px 9px;font-family:var(--mono)}
.field .unit{color:var(--ink-3);font-size:var(--fs-small)}
button{cursor:pointer;border-radius:8px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink);padding:7px 13px;font-weight:500}
.ghost{background:transparent}
.log{font-family:var(--mono);font-size:11px;line-height:1.65;color:var(--ink-2);background:var(--logbg);border:1px solid var(--line);border-radius:10px;padding:10px 12px;height:150px;overflow:auto;white-space:pre;margin-top:16px}
</style>
