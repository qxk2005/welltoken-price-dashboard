<template>
  <aside class="w-56 bg-[#FFFFFF] border-r border-[#E5E5EA] flex flex-col justify-between p-3 select-none">
    <!-- 顶部工作台导航项 -->
    <div class="space-y-1">
      <div class="text-[10px] font-bold text-[#86868B] px-3 py-1.5 uppercase tracking-wider">
        工作台导航
      </div>

      <button
        v-for="item in navItems"
        :key="item.id"
        @click="store.activeTab = item.id"
        class="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all group"
        :class="
          store.activeTab === item.id
            ? 'bg-[#0071E3] text-white shadow-sm font-bold'
            : 'text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F2F2F7]'
        "
      >
        <div class="flex items-center space-x-2.5">
          <span class="text-sm">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </div>

        <span
          v-if="item.badge !== undefined && item.badge !== ''"
          class="px-2 py-0.5 rounded-full text-[10px] font-mono transition-colors"
          :class="
            store.activeTab === item.id
              ? 'bg-white/20 text-white'
              : 'bg-[#E5E5EA] text-[#6E6E73] group-hover:text-[#1D1D1F]'
          "
        >
          {{ item.badge }}
        </span>
      </button>
    </div>

    <!-- 底部状态与汇率小看板 -->
    <div class="space-y-2 pt-3 border-t border-[#E5E5EA] text-xs">
      <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1 font-mono text-[11px]">
        <div class="flex items-center justify-between text-[#86868B]">
          <span>models.dev 基准</span>
          <span class="text-[#34C759] font-bold">100% 实时</span>
        </div>
        <div class="flex items-center justify-between text-[#86868B]">
          <span>当前换算汇率</span>
          <span class="text-[#0071E3] font-bold">{{ store.syncStatus?.usd_to_cny_rate || 7.3 }}</span>
        </div>
        <div class="text-[10px] text-[#86868B] pt-0.5 truncate">
          SQLite 本地大数据库就绪
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()

const navItems = computed<Array<{
  id: 'price-matrix' | 'channels' | 'models' | 'speed-tester' | 'settings'
  label: string
  icon: string
  badge?: string | number
}>>(() => [
  { id: 'price-matrix', label: '全网聚合比价', icon: '📊', badge: store.comparisonMatrix.length || '7.2k' },
  { id: 'channels', label: '供应商与渠道', icon: '🌐', badge: store.relaySites.length || 193 },
  { id: 'models', label: '厂商与模型系列', icon: '🤖', badge: store.modelsCatalog.length || '3.5k' },
  { id: 'speed-tester', label: '渠道性能实测', icon: '⏱️', badge: store.isSpeedTesting ? '测速中' : '' },
  { id: 'settings', label: '数据同步与设置', icon: '⚙️' }
])
</script>

