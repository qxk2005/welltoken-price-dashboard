<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs select-none p-4"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl border border-[#E5E5EA] w-full max-w-md overflow-hidden animate-scale-up"
    >
      <!-- 模态框标题栏 -->
      <div class="px-5 py-4 border-b border-[#E5E5EA] flex items-center justify-between bg-[#FBFBFD]">
        <div class="flex items-center space-x-2">
          <div class="w-6 h-6 rounded-lg bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center font-bold">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7m0-18H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7m0-18v18" />
            </svg>
          </div>
          <h3 class="text-sm font-bold text-[#1D1D1F]">自定义表格显示列</h3>
        </div>
        <button
          @click="$emit('close')"
          class="w-6 h-6 rounded-lg hover:bg-[#F2F2F7] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center transition-all cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- 列选项勾选列表 -->
      <div class="p-5 max-h-[60vh] overflow-y-auto space-y-2.5">
        <div class="text-xs text-[#86868B] mb-2">
          勾选您需要在「官方定价表」中显示的列，设置将自动持久化保存在本地。
        </div>

        <div
          v-for="(col, key) in DEFAULT_COLUMNS"
          :key="key"
          @click="store.toggleColumn(key)"
          class="flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer"
          :class="store.visibleColumns[key] ? 'bg-[#F2F7FF] border-[#0071E3]/30 text-[#0071E3]' : 'bg-[#FAFAFA] border-[#E5E5EA] text-[#6E6E73] hover:bg-[#F2F2F7]'"
        >
          <span class="text-xs font-medium">{{ col.label }}</span>
          <div
            class="w-4 h-4 rounded-md border flex items-center justify-center transition-colors"
            :class="store.visibleColumns[key] ? 'bg-[#0071E3] border-[#0071E3] text-white' : 'border-[#C7C7CC] bg-white'"
          >
            <svg v-if="store.visibleColumns[key]" class="w-2.5 h-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="px-5 py-3 border-t border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between">
        <button
          @click="store.resetColumns"
          class="text-xs text-[#86868B] hover:text-[#FF3B30] transition-colors cursor-pointer"
        >
          恢复默认配置
        </button>
        <button
          @click="$emit('close')"
          class="px-4 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-bold transition-all shadow-sm cursor-pointer"
        >
          完成
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useOfficialPricingStore, DEFAULT_COLUMNS } from '../stores/officialPricingStore'

defineProps<{
  visible: boolean
}>()

defineEmits<{
  (e: 'close'): void
}>()

const store = useOfficialPricingStore()
</script>

<style scoped>
@keyframes scaleUp {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
.animate-scale-up {
  animation: scaleUp 0.15s ease-out forwards;
}
</style>
