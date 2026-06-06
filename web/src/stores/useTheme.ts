import { ref } from 'vue'

const theme = ref<'dark' | 'light'>(
  (localStorage.getItem('pixbar-theme') as 'dark' | 'light') || 'dark',
)

function apply() {
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem('pixbar-theme', theme.value)
}

export function useTheme() {
  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    apply()
  }
  return { theme, toggle }
}
