<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in p-4"
    @click.self="handleClose"
  >
    <div
      class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl w-full max-w-[480px] shadow-[0_20px_50px_rgba(0,0,0,0.18)] overflow-hidden transition-all flex flex-col font-sans"
    >
      <!-- 弹窗 Header -->
      <div class="px-5 py-4 border-b border-[#E5E5EA] bg-[#F9F9FB] flex items-center justify-between">
        <div class="flex items-center space-x-2.5">
          <div class="w-7 h-7 rounded-lg bg-[#E8F2FD] text-[#0071E3] flex items-center justify-center text-sm font-bold shadow-2xs">
            🎛️
          </div>
          <div>
            <h3 class="font-bold text-sm text-[#1D1D1F]">
              自定义表格显示列
            </h3>
            <p class="text-[11px] text-[#86868B] mt-0.5">
              自由勾选显示字段与点击按钮调整列展示顺序
            </p>
          </div>
        </div>
        <button
          @click="handleClose"
          class="w-6 h-6 rounded-full bg-[#E5E5EA]/80 hover:bg-[#D1D1D6] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center text-xs transition-colors cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- 弹窗列表主体 -->
      <div class="p-4 overflow-y-auto max-h-[60vh] space-y-2">
        <div class="text-[11px] text-[#86868B] px-1 flex items-center justify-between pb-1 border-b border-[#E5E5EA]">
          <span>字段名称</span>
          <span>顺序调整</span>
        </div>

        <!-- 固定首列提示 -->
        <div class="flex items-center justify-between px-3 py-2 rounded-xl bg-[#F2F2F7]/70 text-xs text-[#86868B] select-none">
          <div class="flex items-center space-x-2">
            <span class="text-xs">🔒</span>
            <span class="font-medium text-[#1D1D1F]">{{ fixedStartLabel || '模型名称 / 标准标识' }}</span>
          </div>
          <span class="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-[#E5E5EA]">固定首列</span>
        </div>

        <!-- 可配置列列表 -->
        <div
          v-for="(col, index) in localColumns"
          :key="col.key"
          class="flex items-center justify-between px-3 py-2 rounded-xl border transition-all select-none"
          :class="col.visible ? 'bg-white border-[#E5E5EA] shadow-2xs' : 'bg-[#F9F9FB] border-[#E5E5EA]/60 opacity-60'"
        >
          <!-- 勾选与名称 -->
          <label class="flex items-center space-x-2.5 cursor-pointer flex-1 py-0.5">
            <input
              type="checkbox"
              v-model="col.visible"
              class="w-4 h-4 rounded text-[#0071E3] focus:ring-0 cursor-pointer border-[#D1D1D6]"
            />
            <span class="text-xs font-medium text-[#1D1D1F]" :class="{ 'line-through text-[#86868B]': !col.visible }">
              {{ col.label }}
            </span>
          </label>

          <!-- 顺序调整按钮 -->
          <div class="flex items-center space-x-1">
            <button
              @click="moveColumn(index, -1)"
              :disabled="index === 0"
              class="w-6 h-6 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-20 text-xs text-[#1D1D1F] flex items-center justify-center transition-colors cursor-pointer font-bold"
              title="上移"
            >
              ▲
            </button>
            <button
              @click="moveColumn(index, 1)"
              :disabled="index === localColumns.length - 1"
              class="w-6 h-6 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-20 text-xs text-[#1D1D1F] flex items-center justify-center transition-colors cursor-pointer font-bold"
              title="下移"
            >
              ▼
            </button>
          </div>
        </div>

        <!-- 固定尾列提示 -->
        <div v-if="fixedEndLabel" class="flex items-center justify-between px-3 py-2 rounded-xl bg-[#F2F2F7]/70 text-xs text-[#86868B] select-none">
          <div class="flex items-center space-x-2">
            <span class="text-xs">🔒</span>
            <span class="font-medium text-[#1D1D1F]">{{ fixedEndLabel }}</span>
          </div>
          <span class="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-[#E5E5EA]">固定操作列</span>
        </div>
      </div>

      <!-- 底部 Footer -->
      <div class="px-5 py-3 border-t border-[#E5E5EA] bg-[#F9F9FB] flex items-center justify-between">
        <button
          @click="resetToDefault"
          class="text-xs text-[#6E6E73] hover:text-[#0071E3] hover:underline cursor-pointer flex items-center space-x-1 font-medium"
        >
          <span>🔄</span>
          <span>恢复默认列配置</span>
        </button>

        <div class="flex items-center space-x-2">
          <button
            @click="handleClose"
            class="px-3.5 py-1.5 rounded-xl border border-[#E5E5EA] bg-white hover:bg-[#F2F2F7] text-[#1D1D1F] text-xs font-medium cursor-pointer transition-all"
          >
            取消
          </button>
          <button
            @click="handleSave"
            class="px-4 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#005BB5] text-white text-xs font-bold cursor-pointer transition-all shadow-xs"
          >
            保存并应用
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

export interface TableColumnDef {
  key: string
  label: string
  visible: boolean
}

const props = defineProps<{
  show: boolean
  storageKey: string
  defaultColumns: TableColumnDef[]
  fixedStartLabel?: string
  fixedEndLabel?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update:columns', columns: TableColumnDef[]): void
  (e: 'reset-widths'): void
}>()

const localColumns = ref<TableColumnDef[]>([])

const loadFromStorage = () => {
  try {
    const saved = localStorage.getItem(props.storageKey)
    if (saved) {
      const parsed: TableColumnDef[] = JSON.parse(saved)
      const merged: TableColumnDef[] = []
      for (const p of parsed) {
        const d = props.defaultColumns.find(col => col.key === p.key)
        if (d) {
          merged.push({ key: p.key, label: d.label, visible: p.visible !== false })
        }
      }
      for (const d of props.defaultColumns) {
        if (!merged.some(m => m.key === d.key)) {
          merged.push({ ...d })
        }
      }
      localColumns.value = merged
      return
    }
  } catch (e) {
    console.warn('加载列配置失败:', e)
  }
  localColumns.value = props.defaultColumns.map(c => ({ ...c }))
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadFromStorage()
  }
}, { immediate: true })

const moveColumn = (index: number, direction: number) => {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= localColumns.value.length) return
  const item = localColumns.value.splice(index, 1)[0]
  localColumns.value.splice(targetIndex, 0, item)
}

const resetToDefault = () => {
  localColumns.value = props.defaultColumns.map(c => ({ ...c }))
  emit('reset-widths')
}

const handleClose = () => {
  emit('close')
}

const handleSave = () => {
  try {
    localStorage.setItem(props.storageKey, JSON.stringify(localColumns.value))
  } catch (e) {
    console.error('[TableColumnConfigModal] 写入 localStorage 失败:', e)
  }
  emit('update:columns', [...localColumns.value])
  emit('close')
}
</script>
