<script setup lang="ts">
import { computed } from 'vue'
import type { Status, Runner, OptSpec } from '../types'
import { api } from '../api'
import ToggleSwitch from './ToggleSwitch.vue'
import OptionField from './OptionField.vue'
import AttachSection from './AttachSection.vue'
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
function setIv(e: Event) { props.setInterval(props.id, Number((e.target as HTMLInputElement).value)) }
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
      <div class="field"><label>间隔</label><input type="number" min="1" :value="r.interval" @change="setIv" id="iv" /><span class="unit">秒</span></div>
      <button class="ghost" @click="once">推一次</button>
    </div>
    <OptionField v-for="o in r.optspec" :key="o.key" :spec="o" :value="r.options[o.key]"
      @change="(v) => setOpt(o.key, v)" @open-search="(s) => emit('open-search', { id, spec: s, kind: 'plugin' })" />
    <pre class="log">{{ (r.log || []).join('\n') || '—' }}</pre>
    <AttachSection :host="id" :status="status" :intended="intended" :toggle-attach="toggleAttach"
      @changed="emit('changed')" @open-search="(p) => emit('open-search', p)" />
  </section>
</template>

<style scoped>
.card{background:var(--bg-1);border:1px solid var(--line);border-radius:14px;padding:18px;min-height:280px}
.head{display:flex;align-items:center;justify-content:space-between;gap:12px}
h2{font-family:var(--display);font-weight:700;font-size:var(--fs-h2);margin:0}
.rs{font-family:var(--mono);font-size:var(--fs-micro);letter-spacing:.12em;margin-top:4px}
.desc{color:var(--ink-2);font-size:var(--fs-body);line-height:1.65;margin:14px 0 0;max-width:60ch}
.controls{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:16px}
.field{display:flex;align-items:center;gap:7px;color:var(--ink-2)}
.field input{width:62px;background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:7px 9px;font-family:var(--mono)}
.field .unit{color:var(--ink-3);font-size:var(--fs-small)}
button{cursor:pointer;border-radius:8px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink);padding:7px 13px;font-weight:500}
.ghost{background:transparent}
.log{font-family:var(--mono);font-size:11px;line-height:1.65;color:var(--ink-2);background:var(--logbg);border:1px solid var(--line);border-radius:10px;padding:10px 12px;height:150px;overflow:auto;white-space:pre;margin-top:16px}
</style>
