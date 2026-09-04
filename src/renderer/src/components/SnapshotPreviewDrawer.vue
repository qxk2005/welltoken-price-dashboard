<template>
  <div
    v-if="store.snapshotDrawer.visible"
    class="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs transition-opacity duration-300"
    @click.self="store.closeSnapshotDrawer"
  >
    <div
      class="w-full max-w-4xl h-full bg-[#FFFFFF] shadow-2xl flex flex-col border-l border-[#E5E5EA] animate-slide-left select-none overflow-hidden"
    >
      <!-- 抽屉顶部栏 (苹果极简白 + 灰底) -->
      <div class="px-5 py-3 border-b border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between flex-shrink-0">
        <div class="flex items-center space-x-3 min-w-0">
          <div class="w-8 h-8 rounded-xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center font-bold flex-shrink-0">
            <SystemIcon name="official-pricing" custom-class="w-4 h-4" />
          </div>
          <div class="min-w-0">
            <div class="flex items-center space-x-2">
              <h3 class="text-sm font-bold text-[#1D1D1F] truncate">
                {{ store.snapshotDrawer.modelName }} 官方快照对账
              </h3>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#34C759]/10 text-[#34C759] border border-[#34C759]/20 flex-shrink-0">
                完整 HTML 凭证
              </span>
            </div>
            <p class="text-[11px] text-[#86868B] truncate mt-0.5">
              {{ store.snapshotDrawer.pageTitle }}
            </p>
          </div>
        </div>

        <div class="flex items-center space-x-2 flex-shrink-0">
          <!-- 直达官方源链接按钮 -->
          <a
            :href="store.snapshotDrawer.sourceUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="px-3 py-1.5 rounded-xl border border-[#E5E5EA] bg-white hover:bg-[#F2F2F7] text-xs font-medium text-[#0071E3] flex items-center space-x-1.5 transition-all shadow-2xs"
            title="新窗口打开官网原始在线页面"
          >
            <span>访问官网</span>
            <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>

          <!-- 关闭抽屉按钮 -->
          <button
            @click="store.closeSnapshotDrawer"
            class="w-8 h-8 rounded-xl hover:bg-[#F2F2F7] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center transition-all cursor-pointer"
            title="关闭对账抽屉 (ESC)"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- 来源 URL 与位置指示栏 -->
      <div class="px-5 py-2 bg-[#F5F5F7] border-b border-[#E5E5EA] flex items-center justify-between text-xs text-[#6E6E73] font-mono flex-shrink-0">
        <div class="flex items-center space-x-2 truncate">
          <span class="text-[#86868B]">原始地址:</span>
          <span class="text-[#1D1D1F] truncate select-all">{{ store.snapshotDrawer.sourceUrl }}</span>
        </div>
        <span class="text-[11px] text-[#0071E3] font-sans flex-shrink-0">
          本地磁盘持久化快照
        </span>
      </div>

      <!-- 抽屉主体：iframe 渲染保存的完整 HTML 快照 -->
      <div class="flex-1 bg-white relative overflow-hidden">
        <iframe
          v-if="store.snapshotDrawer.snapshotId"
          :src="`${store.apiUrl}/api/v1/official-pricing/snapshots/${store.snapshotDrawer.snapshotId}/view?highlight=${encodeURIComponent(store.snapshotDrawer.highlightTarget || '')}`"
          class="w-full h-full border-0 select-text"
        ></iframe>

        <div v-else class="flex flex-col items-center justify-center h-full text-[#86868B] space-y-3">
          <SystemIcon name="folder" custom-class="w-12 h-12 opacity-30 text-[#86868B]" />
          <div class="text-sm font-medium">当前模型暂无关联的离线快照文件</div>
          <a
            :href="store.snapshotDrawer.sourceUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="px-4 py-2 rounded-xl bg-[#0071E3] text-white text-xs font-bold hover:bg-[#0077ED] transition-all shadow-sm"
          >
            直接前往官方在线页面
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useOfficialPricingStore } from '../stores/officialPricingStore'
import SystemIcon from './SystemIcon.vue'

const store = useOfficialPricingStore()

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && store.snapshotDrawer.visible) {
    store.closeSnapshotDrawer()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
@keyframes slideLeft {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}
.animate-slide-left {
  animation: slideLeft 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
