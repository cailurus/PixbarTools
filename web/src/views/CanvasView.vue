<script setup lang="ts">
import { useCanvas } from '../canvas/useCanvas'
import CanvasStage from '../components/CanvasStage.vue'
import CanvasControls from '../components/CanvasControls.vue'
import ImagePanel from '../components/ImagePanel.vue'
const c = useCanvas()
</script>

<template>
  <div class="wrap">
    <CanvasStage />
    <CanvasControls />
    <ImagePanel v-if="c.tool.value === 'image'" />
  </div>
</template>

<style scoped>
.wrap{max-width:1000px;margin:0 auto;display:flex;flex-direction:column;gap:14px;padding:22px 28px}
</style>
