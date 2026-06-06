<script setup lang="ts">
defineProps<{ modelValue: boolean; small?: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()
</script>

<template>
  <label class="switch" :class="{ sm: small }">
    <input type="checkbox" :checked="modelValue" @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)" />
    <span class="track"></span>
  </label>
</template>

<style scoped>
.switch{position:relative;display:inline-flex;width:46px;height:26px;flex:none;cursor:pointer}
.switch.sm{transform:scale(.82);transform-origin:right center}
.switch input{position:absolute;opacity:0;width:100%;height:100%;margin:0;cursor:pointer}
.track{position:absolute;inset:0;background:var(--bg-3);border:1px solid var(--line-2);border-radius:26px;transition:.22s cubic-bezier(.4,0,.2,1)}
.track::after{content:"";position:absolute;width:18px;height:18px;left:3px;top:3px;border-radius:50%;background:var(--ink-2);transition:.22s cubic-bezier(.4,0,.2,1)}
.switch input:checked+.track{background:var(--signal-dim);border-color:var(--signal)}
.switch input:checked+.track::after{transform:translateX(20px);background:var(--signal);box-shadow:0 0 8px var(--signal)}
.switch input:focus-visible+.track{box-shadow:0 0 0 3px var(--signal-glow)}
</style>
