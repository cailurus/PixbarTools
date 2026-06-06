<script setup lang="ts">
import type { Status, OptSpec, Attachment } from '../types'
import { api } from '../api'
import ToggleSwitch from './ToggleSwitch.vue'
import OptionField from './OptionField.vue'
const props = defineProps<{
  host: string; status: Status
  intended: Record<string, boolean>
  toggleAttach: (id: string, on: boolean) => void
}>()
const emit = defineEmits<{ (e: 'changed'): void; (e: 'open-search', a: { id: string; spec: OptSpec; kind: 'attach' }): void }>()
function listFor(): Attachment[] {
  return Object.values(props.status.attachments).filter((a) => a.host === props.host)
}
async function add(type: string) { await api.attachAdd(props.host, type); emit('changed') }
async function remove(id: string) { await api.attachRemove(id); emit('changed') }
async function setOpt(id: string, key: string, v: string) { await api.attachOption(id, key, v); emit('changed') }
function running(a: Attachment): boolean { return a.id in props.intended ? props.intended[a.id] : a.running }
</script>

<template>
  <div class="attach">
    <div class="head">
      <span>附属推送</span>
      <span class="add" v-if="status.attachTypes.length">
        <select ref="typeSel">
          <option v-for="t in status.attachTypes" :key="t.type" :value="t.type">{{ t.name }}</option>
        </select>
        <button @click="add(($refs.typeSel as HTMLSelectElement).value)">+ 添加</button>
      </span>
    </div>
    <div v-if="!listFor().length" class="muted">还没有附属推送。开启后会定时插播到本插件画面上。</div>
    <div v-for="a in listFor()" :key="a.id" class="card" :class="{ on: running(a) }">
      <div class="ch">
        <span class="nm">{{ a.typeName }}</span><span style="flex:1"></span>
        <ToggleSwitch :small="true" :model-value="running(a)" @update:model-value="(v) => toggleAttach(a.id, v)" />
        <button class="x" title="移除" @click="remove(a.id)">&times;</button>
      </div>
      <OptionField v-for="o in a.optspec" :key="o.key" :spec="o" :value="a.options[o.key]"
        @change="(v) => setOpt(a.id, o.key, v)" @open-search="(s) => emit('open-search', { id: a.id, spec: s, kind: 'attach' })" />
      <pre class="log">{{ (a.log || []).join('\n') || '—' }}</pre>
    </div>
  </div>
</template>

<style scoped>
.attach{margin-top:18px;border-top:1px solid var(--line);padding-top:14px}
.head{display:flex;align-items:center;gap:10px}
.head>span:first-child{font-family:var(--mono);font-size:var(--fs-micro);letter-spacing:.2em;text-transform:uppercase;color:var(--ink-3)}
.add{margin-left:auto;display:flex;gap:6px}
.add select,.add button,.x{background:var(--bg-2);color:var(--ink);border:1px solid var(--line-2);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:var(--fs-body)}
.card{background:var(--bg-2);border:1px solid var(--line);border-radius:11px;padding:12px;margin-top:10px;display:flex;flex-direction:column;gap:9px}
.card.on{border-color:var(--signal-dim)}
.ch{display:flex;align-items:center;gap:9px}
.nm{font-weight:600}
.x{border:0;background:none;color:var(--ink-3);font-size:18px;padding:0 5px}
.x:hover{color:var(--danger)}
.log{font-family:var(--mono);font-size:11px;line-height:1.6;color:var(--ink-2);background:var(--logbg);border:1px solid var(--line);border-radius:9px;padding:9px 11px;height:64px;overflow:auto;white-space:pre;margin:0}
.muted{color:var(--ink-3);font-size:var(--fs-small);margin-top:8px}
</style>
