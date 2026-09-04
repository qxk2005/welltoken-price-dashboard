<template>
  <div class="relative w-full text-xs" ref="containerRef">
    <!-- 1. 触发器按钮 (Trigger) -->
    <div
      @click="toggleDropdown"
      class="w-full flex items-center justify-between bg-[#FFFFFF] border rounded-lg px-2.5 py-1.5 cursor-pointer transition-all hover:border-[#0071E3]"
      :class="modelValue ? 'border-[#E5E5EA] text-[#1D1D1F]' : 'border-[#FF9500] text-[#FF9500] bg-[#FFFBF5]'"
    >
      <div class="flex items-center space-x-1.5 truncate flex-1 mr-1">
        <span v-if="selectedModel" class="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase font-mono" :class="getProviderBadgeClass(selectedModel.provider)">
          {{ selectedModel.provider }}
        </span>
        <span v-if="selectedModel" class="font-mono text-[11px] font-semibold text-[#1D1D1F] truncate">
          {{ selectedModel.model_id }}
        </span>
        <span v-if="selectedModel && selectedModel.name && selectedModel.name !== selectedModel.model_id" class="text-[10px] text-[#86868B] truncate">
          ({{ selectedModel.name }})
        </span>
        <span v-else-if="!modelValue" class="text-[#FF9500] flex items-center space-x-1 text-[11px]">
          <span>🔍</span>
          <span>选择或输入模型...</span>
        </span>
      </div>

      <div class="flex items-center space-x-1 text-[#86868B] shrink-0">
        <button
          v-if="modelValue"
          type="button"
          @click.stop="clearSelection"
          class="hover:text-[#FF3B30] p-0.5 rounded text-[11px]"
          title="清空关联"
        >
          ✕
        </button>
        <span class="text-[10px] text-[#86868B]">▾</span>
      </div>
    </div>

    <!-- 2. 搜索下拉浮层 (Popover Dropdown) -->
    <div
      v-if="isOpen"
      class="absolute left-0 top-full mt-1 w-[380px] max-w-[90vw] z-50 bg-[#FFFFFF] border border-[#E5E5EA] rounded-xl shadow-[0_12px_32px_rgba(0,0,0,0.18)] p-2.5 space-y-2 animate-fade-in text-xs"
    >
      <!-- 搜索输入框 -->
      <div class="relative">
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          placeholder="输入模型 ID、名称或厂商模糊搜索..."
          class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg pl-7 pr-7 py-1.5 text-xs text-[#1D1D1F] focus:outline-none transition-colors"
          @keydown.down.prevent="navigateDown"
          @keydown.up.prevent="navigateUp"
          @keydown.enter.prevent="selectHighlighted"
          @keydown.esc="closeDropdown"
        />
        <span class="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#86868B] text-[11px]">🔍</span>
        <button
          v-if="searchQuery"
          type="button"
          @click="searchQuery = ''"
          class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#86868B] hover:text-[#1D1D1F] text-[11px]"
        >
          ✕
        </button>
      </div>

      <!-- 模型列表视图 -->
      <div v-if="!isCreatingNew" class="max-h-52 overflow-y-auto space-y-0.5 custom-scrollbar pr-0.5">
        <div
          v-for="(item, idx) in filteredModels"
          :key="getModelId(item)"
          @click="selectModel(getModelId(item))"
          @mouseenter="highlightedIndex = idx"
          class="px-2.5 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors"
          :class="[
            highlightedIndex === idx ? 'bg-[#E8F2FD] text-[#0071E3]' : 'hover:bg-[#F2F2F7] text-[#1D1D1F]',
            getModelId(item) === modelValue ? 'font-bold bg-[#F2F2F7]' : ''
          ]"
        >
          <div class="flex items-center space-x-2 truncate flex-1 mr-2">
            <span class="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase font-mono shrink-0" :class="getProviderBadgeClass(item.provider)">
              {{ item.provider_name || item.provider }}
            </span>
            <div class="truncate">
              <div class="font-mono text-[11px] truncate leading-tight">{{ getModelId(item) }}</div>
              <div v-if="getModelName(item) && getModelName(item) !== getModelId(item)" class="text-[10px] text-[#86868B] truncate">
                {{ getModelName(item) }}
              </div>
            </div>
          </div>

          <div class="text-[10px] font-mono text-[#86868B] shrink-0">
            <span v-if="item.converted_input_cny !== undefined && currency !== 'USD'">¥{{ item.converted_input_cny }}</span>
            <span v-else>${{ item.converted_input_usd ?? item.official_input_price }}</span>
            / 1M
          </div>
        </div>

        <div v-if="filteredModels.length === 0" class="py-4 text-center text-[#86868B] text-[11px]">
          <div>未找到匹配的官方标准模型「{{ searchQuery }}」</div>
          <div class="text-[10px] text-[#0071E3] mt-1">可在下方点击「+ 创建新模型/别名」自动生成并入库！</div>
        </div>
      </div>

      <!-- 创建新自定义模型表单视图 -->
      <div v-else class="p-2.5 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] space-y-2 animate-fade-in">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-1.5">
          <span class="font-bold text-[#1D1D1F] text-[11px] flex items-center space-x-1">
            <span>✨</span>
            <span>新建标准模型并固化别名</span>
          </span>
          <button @click="isCreatingNew = false" type="button" class="text-[#86868B] hover:text-[#1D1D1F] text-[11px]">返回列表</button>
        </div>

        <div class="space-y-1.5 text-[11px]">
          <div>
            <label class="block text-[#6E6E73] font-medium mb-0.5">标准模型 ID *</label>
            <input
              v-model="newModelForm.model_id"
              type="text"
              class="w-full bg-[#FFFFFF] border border-[#E5E5EA] focus:border-[#0071E3] rounded-lg px-2 py-1 font-mono text-[11px] text-[#1D1D1F] focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-[#6E6E73] font-medium mb-0.5">显示名称 *</label>
              <input
                v-model="newModelForm.name"
                type="text"
                class="w-full bg-[#FFFFFF] border border-[#E5E5EA] focus:border-[#0071E3] rounded-lg px-2 py-1 text-[11px] text-[#1D1D1F] focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-0.5">研发厂商 (Provider)</label>
              <select
                v-model="newModelForm.provider"
                class="w-full bg-[#FFFFFF] border border-[#E5E5EA] focus:border-[#0071E3] rounded-lg px-2 py-1 text-[11px] text-[#1D1D1F] focus:outline-none"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="deepseek">DeepSeek</option>
                <option value="google">Google (Gemini)</option>
                <option value="alibaba">Alibaba (Qwen)</option>
                <option value="bytedance">ByteDance (Doubao)</option>
                <option value="zhipuai">Zhipu AI (GLM)</option>
                <option value="moonshotai">Moonshot AI (Kimi)</option>
                <option value="minimax">MiniMax</option>
                <option value="xai">xAI (Grok)</option>
                <option value="custom">Custom 自定义</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-[#6E6E73] font-medium mb-0.5">官方输入基准价 ($/1M)</label>
              <input
                v-model.number="newModelForm.official_input_price"
                type="number"
                step="0.01"
                class="w-full bg-[#FFFFFF] border border-[#E5E5EA] focus:border-[#0071E3] rounded-lg px-2 py-1 font-mono text-[11px] text-[#1D1D1F] focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-0.5">官方输出基准价 ($/1M)</label>
              <input
                v-model.number="newModelForm.official_output_price"
                type="number"
                step="0.01"
                class="w-full bg-[#FFFFFF] border border-[#E5E5EA] focus:border-[#0071E3] rounded-lg px-2 py-1 font-mono text-[11px] text-[#1D1D1F] focus:outline-none"
              />
            </div>
          </div>

          <div class="flex items-center space-x-1.5 pt-1 text-[10px] text-[#6E6E73]">
            <input v-model="newModelForm.auto_promote_alias" type="checkbox" id="promote_alias_cb" class="rounded text-[#0071E3]" />
            <label for="promote_alias_cb" class="cursor-pointer">同时固化「{{ rawModelName }}」为永久全局别名</label>
          </div>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-1.5">
          <button
            type="button"
            @click="isCreatingNew = false"
            class="px-2.5 py-1 rounded-lg bg-[#FFFFFF] border border-[#E5E5EA] hover:bg-[#F2F2F7] text-[#1D1D1F] text-[10px]"
          >
            取消
          </button>
          <button
            type="button"
            @click="submitNewModel"
            :disabled="isSubmittingNewModel"
            class="px-3 py-1 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] text-white text-[10px] font-bold shadow-xs disabled:opacity-50"
          >
            {{ isSubmittingNewModel ? '保存中...' : '保存并绑定' }}
          </button>
        </div>
      </div>

      <!-- 底部快捷新建按钮 -->
      <div v-if="!isCreatingNew" class="pt-1.5 border-t border-[#E5E5EA] flex items-center justify-between text-[11px]">
        <span class="text-[#86868B]">共 {{ modelsCatalog.length }} 款官方标准模型</span>
        <button
          type="button"
          @click="openCreateNewModel"
          class="text-[#0071E3] hover:text-[#0077ED] font-semibold flex items-center space-x-1 hover:underline cursor-pointer"
        >
          <span>➕</span>
          <span>创建新模型/别名</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, reactive } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import type { ModelMetadata } from '../types'

const props = defineProps<{
  modelValue?: string
  modelsCatalog: (ModelMetadata | any)[]
  rawModelName?: string
  currentPriceUsd?: number
  currentPriceCny?: number
  currency?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
  (e: 'created', newModel: any): void
}>()

const store = useDashboardStore()
const containerRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)

const isOpen = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(0)
const isCreatingNew = ref(false)
const isSubmittingNewModel = ref(false)

function getModelId(item: any): string {
  if (!item) return ''
  return item.model_id || item.raw_model_id || item.clean_name || ''
}

function getModelName(item: any): string {
  if (!item) return ''
  return item.clean_name || item.name || item.model_name || getModelId(item)
}

const newModelForm = reactive({
  model_id: '',
  name: '',
  provider: 'custom',
  official_input_price: 2.0,
  official_output_price: 2.0,
  official_cache_price: 0.2,
  auto_promote_alias: true
})

const selectedModel = computed(() => {
  if (!props.modelValue) return null
  const target = props.modelValue.toLowerCase()
  return (
    props.modelsCatalog.find((m: any) =>
      getModelId(m).toLowerCase() === target ||
      (m.clean_name && m.clean_name.toLowerCase() === target)
    ) || {
      model_id: props.modelValue,
      name: props.modelValue,
      provider: 'custom',
      official_input_price: 2.0
    }
  )
})

const filteredModels = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) {
    return props.modelsCatalog.slice(0, 100)
  }
  return props.modelsCatalog
    .filter((m: any) => {
      const id = getModelId(m).toLowerCase()
      const name = getModelName(m).toLowerCase()
      const provider = (m.provider_name || m.provider || '').toLowerCase()
      const series = (m.series || '').toLowerCase()
      return id.includes(q) || name.includes(q) || provider.includes(q) || series.includes(q)
    })
    .slice(0, 100)
})

function inferProvider(rawName: string): string {
  const m = (rawName || '').toLowerCase()
  if (m.includes('claude')) return 'anthropic'
  if (m.includes('deepseek')) return 'deepseek'
  if (m.includes('gpt') || m.includes('o1') || m.includes('o3') || m.includes('codex') || m.includes('text-embedding')) return 'openai'
  if (m.includes('gemini') || m.includes('gemma')) return 'google'
  if (m.includes('qwen')) return 'alibaba'
  if (m.includes('doubao') || m.includes('seed')) return 'bytedance'
  if (m.includes('glm') || m.includes('zhipu')) return 'zhipuai'
  if (m.includes('kimi') || m.includes('moonshot')) return 'moonshotai'
  if (m.includes('minimax') || m.includes('abab')) return 'minimax'
  if (m.includes('grok') || m.includes('xai')) return 'xai'
  return 'custom'
}

function openCreateNewModel() {
  const raw = (props.rawModelName || searchQuery.value || '').trim()
  const cleanId = raw.toLowerCase().replace(/[^a-z0-9._-]/g, '-')
  newModelForm.model_id = cleanId || 'custom-model'
  newModelForm.name = raw || cleanId
  newModelForm.provider = inferProvider(raw)
  
  const basePrice = props.currentPriceUsd && props.currentPriceUsd > 0
    ? props.currentPriceUsd
    : (props.currentPriceCny ? roundNum(props.currentPriceCny / 7.25, 3) : 2.0)
  newModelForm.official_input_price = basePrice
  newModelForm.official_output_price = basePrice
  newModelForm.official_cache_price = roundNum(basePrice * 0.1, 3)
  newModelForm.auto_promote_alias = true

  isCreatingNew.value = true
}

function roundNum(val: number, decimals: number): number {
  return Number(Math.round(Number(val + 'e' + decimals)) + 'e-' + decimals)
}

async function submitNewModel() {
  if (!newModelForm.model_id.trim() || !newModelForm.name.trim()) {
    alert('请填写模型 ID 与显示名称！')
    return
  }

  isSubmittingNewModel.value = true
  try {
    const rawAliasParam = newModelForm.auto_promote_alias && props.rawModelName ? `?raw_alias=${encodeURIComponent(props.rawModelName)}` : ''
    const res = await axios.post(`${store.apiUrl}/api/v1/models${rawAliasParam}`, {
      model_id: newModelForm.model_id.trim(),
      name: newModelForm.name.trim(),
      provider: newModelForm.provider,
      series: 'Custom',
      official_input_price: newModelForm.official_input_price,
      official_output_price: newModelForm.official_output_price,
      official_cache_price: newModelForm.official_cache_price,
      description: '用户在向导中创建的自定义模型'
    })

    const created = res.data
    await store.fetchModelsCatalog()
    emit('update:modelValue', created.model_id)
    emit('change', created.model_id)
    emit('created', created)

    isCreatingNew.value = false
    isOpen.value = false
  } catch (e: any) {
    alert(`创建模型失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isSubmittingNewModel.value = false
  }
}

function toggleDropdown() {
  if (isOpen.value) {
    closeDropdown()
  } else {
    openDropdown()
  }
}

function openDropdown() {
  isOpen.value = true
  isCreatingNew.value = false
  searchQuery.value = ''
  highlightedIndex.value = 0
  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

function closeDropdown() {
  isOpen.value = false
  isCreatingNew.value = false
}

function clearSelection() {
  emit('update:modelValue', '')
  emit('change', '')
}

function selectModel(id: string) {
  emit('update:modelValue', id)
  emit('change', id)
  closeDropdown()
}

function selectHighlighted() {
  if (filteredModels.value.length > 0 && highlightedIndex.value < filteredModels.value.length) {
    selectModel(filteredModels.value[highlightedIndex.value].model_id)
  }
}

function navigateDown() {
  if (highlightedIndex.value < filteredModels.value.length - 1) {
    highlightedIndex.value++
  }
}

function navigateUp() {
  if (highlightedIndex.value > 0) {
    highlightedIndex.value--
  }
}

function handleClickOutside(event: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

function getProviderBadgeClass(provider: string = ''): string {
  const p = provider.toLowerCase()
  if (p === 'openai') return 'bg-[#E8F2FD] text-[#0071E3]'
  if (p === 'anthropic') return 'bg-[#FDF2F8] text-[#DB2777]'
  if (p === 'deepseek') return 'bg-[#EEF2FF] text-[#4F46E5]'
  if (p === 'google') return 'bg-[#FEF3C7] text-[#D97706]'
  if (p === 'alibaba') return 'bg-[#FFF7ED] text-[#EA580C]'
  if (p === 'bytedance') return 'bg-[#F0FDF4] text-[#16A34A]'
  if (p === 'zhipuai') return 'bg-[#F5F3FF] text-[#7C3AED]'
  return 'bg-[#F2F2F7] text-[#6E6E73]'
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
