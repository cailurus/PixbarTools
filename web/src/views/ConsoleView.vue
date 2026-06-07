<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { usePanel } from '../stores/usePanel'
import { api } from '../api'
import type { OptSpec } from '../types'
import DeviceBar from '../components/DeviceBar.vue'
import CategoryNav from '../components/CategoryNav.vue'
import PluginList from '../components/PluginList.vue'
import PluginDetail from '../components/PluginDetail.vue'
import SearchModal from '../components/SearchModal.vue'

const p = usePanel()
onMounted(() => p.start())
onUnmounted(() => p.stop())

const search = ref<{ spec: OptSpec; target: { kind: 'plugin' | 'attach'; id: string } } | null>(null)
function openSearchPlugin(payload: { id: string; spec: OptSpec; kind: 'plugin' | 'attach' }) {
  search.value = { spec: payload.spec, target: { kind: payload.kind, id: payload.id } }
}
async function pick(value: string) {
  const t = search.value!.target
  if (t.kind === 'plugin') await api.setOption(t.id, search.value!.spec.key, value)
  else await api.attachOption(t.id, search.value!.spec.key, value)
  search.value = null
  p.refresh()
}
function counts(): Record<string, number> {
  const c: Record<string, number> = {}
  for (const n of p.groups.value.names) c[n] = p.groups.value.map[n].length
  return c
}
</script>

<template>
  <div class="wrap">
    <DeviceBar :status="p.status.value" :offline="p.offline.value" @changed="p.refresh" />
    <div class="console" v-if="p.status.value">
      <CategoryNav :names="p.groups.value.names" :counts="counts()" :selected="p.selGroup.value" @pick="p.pickGroup" />
      <aside>
        <PluginList :ids="p.groups.value.map[p.selGroup.value] || []" :status="p.status.value" :selected="p.selId.value" @pick="p.pickPlugin" />
      </aside>
      <PluginDetail v-if="p.selId.value" :id="p.selId.value" :status="p.status.value" :intended="p.intended"
        :toggle="p.toggle" :toggle-attach="p.toggleAttach" :set-interval="p.setIntervalPref" @changed="p.refresh"
        @open-search="openSearchPlugin" />
    </div>
    <SearchModal v-if="search" :spec="search.spec" @pick="pick" @close="search = null" />
  </div>
</template>

<style scoped>
.wrap{max-width:1180px;margin:0 auto;display:flex;flex-direction:column;gap:16px;padding:22px 28px}
.console{display:grid;grid-template-columns:168px 248px 1fr;gap:16px;align-items:start}
@media(max-width:780px){.wrap{padding:16px 12px}.console{grid-template-columns:1fr;gap:12px}}
</style>
