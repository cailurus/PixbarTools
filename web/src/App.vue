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
    <div class="brand">
      <span class="wordmark">PixDeck</span>
      <svg class="brandmark" viewBox="0 0 52 16" role="img" aria-label="像素星空">
        <rect x="0.5" y="0.5" width="51" height="15" rx="3" fill="#0b0e12" stroke="rgba(255,255,255,.10)" />
        <g stroke="#e9ebee" stroke-width="1" stroke-linecap="round" opacity="0.5">
          <line x1="40" y1="5" x2="47" y2="3" /><line x1="12" y1="11" x2="5" y2="13" />
        </g>
        <g fill="#f0f2f5">
          <circle cx="47" cy="3" r="1.4" /><circle cx="5" cy="13" r="1.4" /><circle cx="43" cy="12" r="1.3" /><circle cx="9" cy="4" r="1.3" />
        </g>
        <g fill="#c8ccd4">
          <circle cx="30" cy="3" r="1" /><circle cx="20" cy="12" r="1" /><circle cx="37" cy="8" r="1" /><circle cx="16" cy="7" r="1" />
        </g>
        <g fill="#e9ebee" opacity="0.4">
          <circle cx="26" cy="8" r="0.9" /><circle cx="23" cy="6" r="0.8" /><circle cx="31" cy="10" r="0.8" /><circle cx="34" cy="5" r="0.8" />
        </g>
      </svg>
    </div>
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
.brand{display:flex;flex-direction:column;align-items:flex-start;gap:5px}
.brandmark{width:54px;height:16px;flex:none;display:block}
.wordmark{font-family:var(--display);font-weight:800;font-size:17px;line-height:1}
.tabs{display:flex;gap:4px;background:var(--bg-2);padding:4px;border-radius:11px;border:1px solid var(--line)}
.tab{background:none;border:0;cursor:pointer;font-size:13.5px;font-weight:500;color:var(--ink-2);padding:7px 15px;border-radius:8px}
.tab:hover{color:var(--ink)}
.tab.active{background:var(--bg-1);color:var(--ink);box-shadow:0 0 0 1px var(--line-2)}
.spacer{flex:1}
.theme-btn{width:38px;height:38px;border-radius:10px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink-2);cursor:pointer;font-size:16px}
.theme-btn:hover{color:var(--signal);background:var(--bg-3)}
</style>
