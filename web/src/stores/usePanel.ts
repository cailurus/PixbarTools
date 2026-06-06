import { ref, reactive, computed } from 'vue'
import type { Status } from '../types'
import { api } from '../api'

const GROUP_ORDER = ['信息', '工具', '游戏', '视觉', '其它']

export function groupsOf(st: Status): { map: Record<string, string[]>; names: string[] } {
  const map: Record<string, string[]> = {}
  for (const id of st.order) {
    const g = st.runners[id]?.group || '其它'
    ;(map[g] ||= []).push(id)
  }
  const names = GROUP_ORDER.filter((n) => map[n])
  for (const n of Object.keys(map)) if (!names.includes(n)) names.push(n)
  return { map, names }
}

const status = ref<Status | null>(null)
const offline = ref(false)
const selGroup = ref('')
const selId = ref('')
const intended = reactive<Record<string, boolean>>({})
const pendingInterval = reactive<Record<string, number>>({})

let pollTimer: ReturnType<typeof setInterval> | undefined
let fetching = false

export function usePanel() {
  const groups = computed(() => (status.value ? groupsOf(status.value) : { map: {}, names: [] }))
  const sel = computed(() => (status.value && selId.value ? status.value.runners[selId.value] : null))

  async function refresh() {
    if (fetching) return // 防止设备离线(3s 超时)时轮询重叠导致状态回灌闪烁
    fetching = true
    try {
      const st = await api.getStatus()
      status.value = st
      offline.value = false
      const { map, names } = groupsOf(st)
      if (!selGroup.value || !names.includes(selGroup.value)) selGroup.value = names[0] || ''
      const ids = map[selGroup.value] || []
      if (!selId.value || !ids.includes(selId.value)) selId.value = ids[0] || ''
      for (const id of Object.keys(intended)) {
        if (st.runners[id]?.running === intended[id]) delete intended[id]
      }
      for (const id in st.attachments) {
        if (id in intended && st.attachments[id].running === intended[id]) delete intended[id]
      }
    } catch {
      offline.value = true
    } finally {
      fetching = false
    }
  }

  function pickGroup(g: string) {
    selGroup.value = g
    const ids = groups.value.map[g] || []
    if (!ids.includes(selId.value)) selId.value = ids[0] || ''
  }
  function pickPlugin(id: string) { selId.value = id }

  async function toggle(id: string, on: boolean) {
    intended[id] = on
    const iv = pendingInterval[id] ?? status.value?.runners[id]?.interval ?? 5
    await api.toggle(id, on, iv).catch(() => {})
    refresh()
  }
  async function toggleAttach(id: string, on: boolean) {
    intended[id] = on
    await api.attachToggle(id, on).catch(() => {})
    refresh()
  }
  // 间隔: 暂存用户输入; 若正在运行则立即重发 toggle 应用, 否则下次开启时生效
  function setIntervalPref(id: string, iv: number) {
    if (!Number.isFinite(iv) || iv < 1) return
    pendingInterval[id] = iv
    if (status.value?.runners[id]?.running) {
      api.toggle(id, true, iv).catch(() => {})
      refresh()
    }
  }

  function start() {
    if (pollTimer) return // 幂等: 避免 HMR/重复挂载叠加多个轮询循环
    refresh()
    pollTimer = setInterval(refresh, 2500)
  }
  function stop() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = undefined }
  }

  return {
    status, offline, groups, sel, selGroup, selId, intended,
    refresh, start, stop, pickGroup, pickPlugin, toggle, toggleAttach, setIntervalPref,
  }
}
