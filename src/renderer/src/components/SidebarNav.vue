<template>
  <aside class="w-52 h-full bg-[#0F121A] border-r border-[#1F2430] flex flex-col justify-between p-3 select-none">
    <!-- 上部导航菜单 -->
    <div class="space-y-1">
      <div class="px-3 py-2 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
        工作台导航
      </div>

      <button
        v-for="item in navItems"
        :key="item.id"
        @click="store.activeTab = item.id as any"
        class="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all"
        :class="
          store.activeTab === item.id
            ? 'bg-[#1E293B] text-[#38BDF8] border border-blue-500/30 shadow-sm shadow-blue-500/10 font-bold'
            : 'text-gray-400 hover:text-gray-200 hover:bg-[#151922]'
        "
      >
        <div class="flex items-center space-x-2.5">
          <span class="text-sm">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </div>
        <span
          v-if="item.badge"
          class="text-[10px] px-1.5 py-0.2 rounded-full font-mono font-normal"
          :class="store.activeTab === item.id ? 'bg-blue-500/20 text-blue-300' : 'bg-[#232936] text-gray-400'"
        >
          {{ item.badge }}
        </span>
      </button>
    </div>

    <!-- 底部状态小卡片 -->
    <div class="p-3 rounded-lg bg-[#151922] border border-[#232936] text-[11px] space-y-1.5">
      <div class="flex items-center justify-between text-gray-400">
        <span>models.dev 基准</span>
        <span class="text-emerald-400 font-mono">100%</span>
      </div>
      <div class="flex items-center justify-between text-gray-400">
        <span>当前换算汇率</span>
        <span class="text-blue-400 font-mono font-bold">{{ store.syncStatus?.usd_to_cny_rate || 7.30 }}</span>
      </div>
      <div class="pt-1.5 border-t border-[#232936] text-[10px] text-gray-500">
        SQLite 本地大数据库就绪
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()

const navItems = computed(() => [
  { id: 'price-matrix', label: '全网聚合比价', icon: '📊', badge: store.comparisonMatrix.length },
  { id: 'channels', label: 'Token 渠道大全', icon: '🌐', badge: store.relaySites.length },
  { id: 'models', label: '厂商与模型标准库', icon: '🤖', badge: store.modelsCatalog.length },
  { id: 'speed-tester', label: '渠道性能实测', icon: '⏱️', badge: store.isSpeedTesting ? '测速中' : '' },
  { id: 'settings', label: '数据同步与设置', icon: '⚙️' }
])
</script>
