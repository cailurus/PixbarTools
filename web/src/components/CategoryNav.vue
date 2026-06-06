<script setup lang="ts">
defineProps<{ names: string[]; counts: Record<string, number>; selected: string }>()
const emit = defineEmits<{ (e: 'pick', g: string): void }>()
</script>

<template>
  <nav class="ptabs">
    <button v-for="n in names" :key="n" class="ptab" :class="{ active: n === selected }" @click="emit('pick', n)">
      <span>{{ n }}</span><span class="cnt">{{ counts[n] }}</span>
    </button>
  </nav>
</template>

<style scoped>
.ptabs{display:flex;flex-direction:column;gap:3px;background:var(--bg-1);border:1px solid var(--line);border-radius:12px;padding:6px;height:fit-content;position:sticky;top:22px}
.ptab{background:none;border:0;cursor:pointer;font-size:var(--fs-body);font-weight:500;color:var(--ink-2);padding:9px 12px;border-radius:8px;display:flex;align-items:center;justify-content:space-between;gap:7px;width:100%;text-align:left;transition:.16s}
.ptab:hover{color:var(--ink);background:var(--bg-2)}
.ptab.active{background:var(--bg-3);color:var(--ink);box-shadow:inset 2px 0 0 var(--signal)}
.cnt{font-family:var(--mono);font-size:var(--fs-micro);color:var(--ink-3)}
</style>
