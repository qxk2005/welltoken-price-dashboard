<template>
  <div class="relative inline-block text-left select-none" ref="dropdownRef">
    <!-- 触发胶囊按钮 -->
    <button
      type="button"
      @click="isOpen = !isOpen"
      class="h-8 px-2.5 rounded-lg border text-xs font-medium flex items-center space-x-1.5 transition-all shadow-sm"
      :class="
        selectedValues.length > 0
          ? 'bg-blue-600/15 border-blue-500/50 text-blue-300 font-bold'
          : 'bg-[#1A202C] border-[#2D3748] text-gray-300 hover:border-gray-500 hover:text-white'
      "
    >
      <span class="text-xs">{{ icon }}</span>
      <span>{{ label }}:</span>
      <span v-if="selectedValues.length === 0" class="text-gray-500 font-normal">全部</span>
      <span
        v-else
        class="px-1.5 py-0.2 rounded bg-blue-500 text-white text-[10px] font-mono font-bold"
      >
        {{ selectedValues.length === options.length && options.length > 1 ? '全部' : `${selectedValues.length} 项` }}
      </span>
      <span class="text-[10px] text-gray-400">▼</span>
      <button
        v-if="selectedValues.length > 0"
        @click.stop="clearAll"
        class="ml-1 text-gray-400 hover:text-rose-400 text-xs px-0.5 rounded"
        title="清空此维度筛选"
      >
        ✕
      </button>
    </button>

    <!-- 下拉面板 -->
    <div
      v-if="isOpen"
      class="absolute left-0 top-9 w-64 rounded-xl bg-[#151922] border border-[#2D3748] shadow-2xl z-50 p-2.5 space-y-2 animate-in fade-in zoom-in-95 duration-100"
    >
      <!-- 搜索输入框 -->
      <div class="relative">
        <input
          v-model="searchTerm"
          type="text"
          :placeholder="`搜索 ${label}...`"
          class="w-full bg-[#0B0E14] border border-[#2D3748] rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-sans"
        />
        <span v-if="searchTerm" @click="searchTerm = ''" class="absolute right-2 top-1.5 text-gray-500 hover:text-white cursor-pointer text-xs">✕</span>
      </div>

      <!-- 快捷操作栏 -->
      <div class="flex items-center justify-between text-[11px] px-1 text-gray-400 border-b border-[#232936] pb-1.5">
        <div class="space-x-2">
          <button @click="selectAll" class="text-blue-400 hover:underline">全选</button>
          <span>•</span>
          <button @click="clearAll" class="hover:text-white">清空</button>
          <span>•</span>
          <button @click="invertSelection" class="text-gray-400 hover:text-white">反选</button>
        </div>
        <span class="font-mono text-[10px] text-gray-500">共 {{ filteredOptions.length }} 项</span>
      </div>

      <!-- 选项列表 -->
      <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1 divide-y divide-[#232936]/30">
        <label
          v-for="opt in filteredOptions"
          :key="opt.value"
          class="flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-[#1A202C] cursor-pointer text-xs group transition-colors"
          :class="isSelected(opt.value) ? 'text-blue-300 font-medium' : 'text-gray-300'"
        >
          <div class="flex items-center space-x-2 truncate">
            <input
              type="checkbox"
              :checked="isSelected(opt.value)"
              @change="toggleOption(opt.value)"
              class="rounded bg-[#0B0E14] border-gray-600 text-blue-600 focus:ring-0 focus:ring-offset-0"
            />
            <span class="truncate">{{ opt.label }}</span>
          </div>
          <span
            v-if="opt.count !== undefined"
            class="text-[10px] font-mono px-1.5 py-0.2 rounded"
            :class="isSelected(opt.value) ? 'bg-blue-500/20 text-blue-300' : 'bg-[#232936] text-gray-500 group-hover:text-gray-400'"
          >
            {{ opt.count }}
          </span>
        </label>

        <div v-if="filteredOptions.length === 0" class="py-4 text-center text-xs text-gray-500">
          无匹配的{{ label }}
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
  (e: 'update:modelValue', value: string[]): void
}>()

const isOpen = ref(false)
const searchTerm = ref('')
const dropdownRef = ref<HTMLElement | null>(null)

const selectedValues = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isSelected = (val: string) => selectedValues.value.includes(val)

const toggleOption = (val: string) => {
  const cur = [...selectedValues.value]
  const idx = cur.indexOf(val)
  if (idx >= 0) {
    cur.splice(idx, 1)
  } else {
    cur.push(val)
  }
  selectedValues.value = cur
}

const selectAll = () => {
  selectedValues.value = props.options.map((o) => o.value)
}

const clearAll = () => {
  selectedValues.value = []
}

const invertSelection = () => {
  const allVals = props.options.map((o) => o.value)
  selectedValues.value = allVals.filter((v) => !selectedValues.value.includes(v))
}

const filteredOptions = computed(() => {
  if (!searchTerm.value.trim()) return props.options
  const q = searchTerm.value.toLowerCase().trim()
  return props.options.filter(
    (o) => o.label.toLowerCase().includes(q) || o.value.toLowerCase().includes(q)
  )
})

// 点击外部关闭
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
