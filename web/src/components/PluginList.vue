<script setup lang="ts">
import type { Status } from '../types'
defineProps<{ ids: string[]; status: Status; selected: string }>()
const emit = defineEmits<{ (e: 'pick', id: string): void }>()
</script>

<template>
  <ul class="plist">
    <li v-for="id in ids" :key="id" class="li" :class="{ sel: id === selected }" tabindex="0"
        @click="emit('pick', id)" @keydown.enter="emit('pick', id)">
      <span class="lidot" :class="{ run: status.runners[id]?.running }"></span>
      <span class="nm">{{ status.runners[id]?.name || id }}</span>
    </li>
  </ul>
</template>

<style scoped>
.plist{list-style:none;margin:0;padding:6px;background:var(--bg-1);border:1px solid var(--line);border-radius:14px;display:flex;flex-direction:column;gap:2px}
.li{display:flex;align-items:center;gap:9px;padding:9px 11px;border-radius:9px;cursor:pointer;font-size:var(--fs-body);color:var(--ink-2);transition:.14s}
.li:hover{background:var(--bg-2);color:var(--ink)}
.li.sel{background:var(--bg-3);color:var(--ink);box-shadow:inset 2px 0 0 var(--signal)}
.lidot{width:7px;height:7px;border-radius:50%;background:var(--ink-3);flex:none}
.lidot.run{background:var(--signal);box-shadow:0 0 6px var(--signal)}
.nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
</style>
