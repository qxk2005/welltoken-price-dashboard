<template>
  <div class="relative inline-block text-left" ref="dropdownRef">
    <!-- 下拉触发胶囊按钮 (苹果风格) -->
    <button
      @click="isOpen = !isOpen"
      type="button"
      class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all shadow-xs"
      :class="
        modelValue.length > 0
          ? 'bg-[#E8F2FD] border-[#CCE4FB] text-[#0071E3] font-bold'
          : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#1D1D1F]'
      "
    >
      <span>{{ icon }}</span>
      <span>{{ label }}:</span>
      <span class="font-bold">
        {{ selectedLabelSummary }}
      </span>
      <span class="text-[10px] text-[#86868B]">▼</span>
    </button>

    <!-- 下拉浮层面板 (苹果毛玻璃/纯白阴影质感) -->
    <div
      v-if="isOpen"
      class="absolute left-0 mt-1.5 w-64 rounded-xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_12px_36px_rgba(0,0,0,0.1)] z-50 p-2.5 space-y-2 select-none"
    >
      <!-- 搜索过滤框 -->
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="`搜索${label}...`"
          class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
        />
        <span v-if="searchQuery" @click="searchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
      </div>

      <!-- 快速全选 / 清空 -->
      <div class="flex items-center justify-between text-[11px] px-1 text-[#0071E3]">
        <button @click="selectAll" class="hover:underline font-medium">全选 ({{ filteredOptions.length }})</button>
        <button @click="clearAll" class="hover:underline text-[#FF3B30]">清空</button>
      </div>

      <!-- 选项列表 -->
      <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1">
        <label
          v-for="opt in filteredOptions"
          :key="opt.value"
          class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-[#F2F2F7] cursor-pointer text-xs text-[#1D1D1F] transition-colors"
        >
          <div class="flex items-center space-x-2 truncate">
            <input
              type="checkbox"
              :value="opt.value"
              :checked="modelValue.includes(opt.value)"
              @change="toggleOption(opt.value)"
              class="w-3.5 h-3.5 rounded border-[#D1D1D6] text-[#0071E3] focus:ring-[#0071E3]"
            />
            <span class="truncate" :title="opt.label">{{ opt.label }}</span>
          </div>

          <span v-if="opt.count !== undefined" class="text-[10px] text-[#86868B] font-mono ml-2">
            {{ opt.count }}
          </span>
        </label>

        <div v-if="filteredOptions.length === 0" class="py-4 text-center text-xs text-[#86868B]">
          无匹配选项
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

export interface FilterOption {
  value: string
  label: string
  count?: number
}

const props = defineProps<{
  label: string
  icon: string
  options: FilterOption[]
  modelValue: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string[]): void
}>()

const isOpen = ref(false)
const searchQuery = ref('')
const dropdownRef = ref<HTMLElement | null>(null)

const filteredOptions = computed(() => {
  if (!searchQuery.value.trim()) return props.options
  const q = searchQuery.value.toLowerCase().trim()
  return props.options.filter(
    (opt) => opt.label.toLowerCase().includes(q) || opt.value.toLowerCase().includes(q)
  )
})

const selectedLabelSummary = computed(() => {
  if (props.modelValue.length === 0) return '全部'
  if (props.modelValue.length === 1) {
    const matched = props.options.find((o) => o.value === props.modelValue[0])
    return matched ? matched.label : props.modelValue[0]
  }
  return `已选 (${props.modelValue.length})`
})

const toggleOption = (val: string) => {
  const current = [...props.modelValue]
  const idx = current.indexOf(val)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(val)
  }
  emit('update:modelValue', current)
}

const selectAll = () => {
  const allVals = filteredOptions.value.map((o) => o.value)
  const merged = Array.from(new Set([...props.modelValue, ...allVals]))
  emit('update:modelValue', merged)
}

const clearAll = () => {
  emit('update:modelValue', [])
}

const handleClickOutside = (e: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
