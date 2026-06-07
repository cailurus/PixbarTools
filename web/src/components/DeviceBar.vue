<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Status } from '../types'
import { api } from '../api'
import SettingsModal from './SettingsModal.vue'
const props = defineProps<{ status: Status | null; offline: boolean }>()
const emit = defineEmits<{ (e: 'changed'): void }>()
const showSettings = ref(false)
const noDevice = computed(() => !props.offline && !props.status?.device)
function nameOf(id: string): string { return props.status?.runners[id]?.name || id }
async function save(ip: string) {
  if (ip) await api.setDevice(ip)
  showSettings.value = false
  emit('changed')
}
</script>

<template>
  <section class="card device">
    <div class="row">
      <div class="id">
        <span class="dot" :class="status && status.online ? 'on' : 'off'"></span>
        <h1>{{ offline ? '控制服务器无响应' : noDevice ? '未设置设备' : status && status.online ? '设备在线' : '设备离线' }}</h1>
      </div>
      <button class="gear" title="设置" @click="showSettings = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
      </button>
    </div>
    <div class="meta" v-if="status && status.online">
      <div class="kv"><span>IP</span><b>{{ status.base.ip || '-' }}</b></div>
      <div class="kv"><span>固件</span><b>{{ status.base.appVer || '-' }}</b></div>
      <div class="kv"><span>SSID</span><b>{{ status.base.ssid || '-' }}</b></div>
      <div class="kv"><span>亮度</span><b>{{ status.config.brightness ?? '-' }}</b></div>
      <div class="kv"><span>音量</span><b>{{ status.config.volume ?? '-' }}</b></div>
      <div class="kv"><span>时区</span><b>{{ status.config.timezone || '-' }}</b></div>
    </div>
    <div class="meta muted" v-else-if="noDevice">点右上角齿轮填入像素时钟的 IP（需与本机在同一局域网）</div>
    <div class="meta muted" v-else>无法连接设备（检查同一局域网 / IP）</div>
    <div class="diy">
      <span class="lbl">DIY 组件</span>
      <template v-if="status && (status.apps.apps || []).length">
        <span v-for="a in status.apps.apps" :key="a" class="chip">{{ nameOf(a) }}</span>
      </template>
      <span v-else class="muted">无</span>
    </div>
    <SettingsModal v-if="showSettings" :device="status?.device || ''" @save="save" @close="showSettings = false" />
  </section>
</template>

<style scoped>
.card{background:var(--bg-1);border:1px solid var(--line);border-radius:14px;padding:18px}
.row{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
.id{display:flex;align-items:center;gap:11px}
.dot{width:9px;height:9px;border-radius:50%;background:var(--ink-3);flex:none}
.dot.on{background:var(--signal);box-shadow:0 0 0 3px var(--signal-glow)}
.dot.off{background:var(--danger);box-shadow:0 0 0 3px rgba(255,90,82,.15)}
h1{font-family:var(--display);font-weight:700;font-size:var(--fs-h1);margin:0}
.gear{width:36px;height:36px;padding:0;border-radius:10px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink-2);cursor:pointer;display:inline-flex;align-items:center;justify-content:center}
.gear:hover{color:var(--signal);background:var(--bg-3)}
.gear svg{width:17px;height:17px;display:block}
.meta{display:flex;flex-wrap:wrap;gap:7px 9px;margin-top:15px}
.kv{display:flex;align-items:baseline;gap:7px;background:var(--bg-2);border:1px solid var(--line);border-radius:8px;padding:5px 10px}
.kv span{font-size:var(--fs-small);color:var(--ink-3)}
.kv b{font-family:var(--mono);font-weight:500;font-size:var(--fs-data)}
.diy{display:flex;align-items:center;gap:10px;margin-top:13px;flex-wrap:wrap;min-height:22px}
.diy .lbl{font-size:var(--fs-small);color:var(--ink-3)}
.chip{font-size:var(--fs-small);color:var(--ink-2);background:var(--bg-2);border:1px solid var(--line-2);border-radius:6px;padding:2px 9px}
.muted{color:var(--ink-3);font-size:var(--fs-small)}
</style>
