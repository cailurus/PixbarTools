<script setup lang="ts">
import { ref } from 'vue'
import { useTheme } from './stores/useTheme'
import ConsoleView from './views/ConsoleView.vue'
import CanvasView from './views/CanvasView.vue'
const tab = ref<'console' | 'canvas'>('console')
const { theme, toggle } = useTheme()
</script>

<template>
  <header class="topbar">
    <div class="brand"><span class="wordmark">PIXBAR<small>控制中心</small></span></div>
    <nav class="tabs">
      <button class="tab" :class="{ active: tab === 'console' }" @click="tab = 'console'">控制台</button>
      <button class="tab" :class="{ active: tab === 'canvas' }" @click="tab = 'canvas'">画板</button>
    </nav>
    <span class="spacer"></span>
    <button class="theme-btn" title="深浅模式" @click="toggle">{{ theme === 'dark' ? '☀' : '☾' }}</button>
  </header>
  <main class="body">
    <ConsoleView v-show="tab === 'console'" />
    <CanvasView v-show="tab === 'canvas'" />
  </main>
</template>

<style scoped>
.topbar{display:flex;align-items:center;gap:28px;height:58px;padding:0 22px;background:var(--bg-1);border-bottom:1px solid var(--line)}
.wordmark{font-family:var(--display);font-weight:800;font-size:17px}
.wordmark small{display:block;font-family:var(--mono);font-weight:400;font-size:9.5px;letter-spacing:.32em;color:var(--ink-3);margin-top:3px;text-transform:uppercase}
.tabs{display:flex;gap:4px;background:var(--bg-2);padding:4px;border-radius:11px;border:1px solid var(--line)}
.tab{background:none;border:0;cursor:pointer;font-size:13.5px;font-weight:500;color:var(--ink-2);padding:7px 15px;border-radius:8px}
.tab:hover{color:var(--ink)}
.tab.active{background:var(--bg-1);color:var(--ink);box-shadow:0 0 0 1px var(--line-2)}
.spacer{flex:1}
.theme-btn{width:38px;height:38px;border-radius:10px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink-2);cursor:pointer;font-size:16px}
.theme-btn:hover{color:var(--signal);background:var(--bg-3)}
</style>
