<template>
  <aside
    class="bg-[#FFFFFF] border-r border-[#E5E5EA] flex flex-col justify-between py-3 select-none transition-all duration-300 ease-in-out relative flex-shrink-0 z-30"
    :class="store.isSidebarCollapsed ? 'w-16 px-2' : 'w-56 px-3'"
  >
    <!-- 顶部工作台导航项 -->
    <div class="space-y-1">
      <!-- 顶部工作台导航标题栏 + 人体工学折叠按钮 -->
      <div
        class="flex items-center transition-all pb-1 min-h-[28px]"
        :class="store.isSidebarCollapsed ? 'justify-center' : 'justify-between px-2'"
      >
        <span v-if="!store.isSidebarCollapsed" class="text-[10px] font-bold text-[#86868B] uppercase tracking-wider">
          工作台导航
        </span>

        <!-- 折叠 / 展开图标按钮 -->
        <button
          @click="store.toggleSidebar"
          class="w-6 h-6 rounded-lg text-[#86868B] hover:text-[#1D1D1F] hover:bg-[#F2F2F7] active:bg-[#E5E5EA] flex items-center justify-center transition-all cursor-pointer group relative"
          :title="store.isSidebarCollapsed ? '展开左侧功能栏' : '收起左侧功能栏以释放空间'"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="3" x2="9" y2="21"></line>
            <path v-if="store.isSidebarCollapsed" d="M14 9l3 3-3 3"></path>
            <path v-else d="M16 15l-3-3 3-3"></path>
          </svg>

          <!-- 收起状态下的 Tooltip -->
          <div
            v-if="store.isSidebarCollapsed"
            class="absolute left-full ml-3 px-2.5 py-1.5 bg-[#1D1D1F] text-white text-xs rounded-xl shadow-xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-150 z-50 border border-white/10"
          >
            展开左侧功能栏
            <div class="absolute right-full top-1/2 -translate-y-1/2 border-[5px] border-transparent border-r-[#1D1D1F]"></div>
          </div>
        </button>
      </div>

      <div class="space-y-1">
        <button
          v-for="item in navItems"
          :key="item.id"
          @click="store.activeTab = item.id"
          class="w-full flex items-center rounded-xl text-xs font-medium transition-all group relative cursor-pointer"
          :class="[
            store.isSidebarCollapsed
              ? 'justify-center py-2.5 px-0'
              : 'justify-between px-3 py-2',
            store.activeTab === item.id
              ? 'bg-[#0071E3] text-white shadow-sm font-bold'
              : 'text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F2F2F7]'
          ]"
        >
          <!-- 展开态内容 -->
          <div v-if="!store.isSidebarCollapsed" class="flex items-center space-x-2.5">
            <span class="text-sm">{{ item.icon }}</span>
            <span class="truncate">{{ item.label }}</span>
          </div>

          <!-- 收拢态内容 (仅图标) -->
          <div v-else class="flex items-center justify-center relative">
            <span class="text-base">{{ item.icon }}</span>
            <!-- 收拢态小圆点徽标 -->
            <span
              v-if="item.badge !== undefined && item.badge !== '' && item.badge !== '0'"
              class="absolute -top-1 -right-1.5 w-2 h-2 rounded-full border border-white"
              :class="store.activeTab === item.id ? 'bg-white' : 'bg-[#0071E3]'"
            ></span>
          </div>

          <!-- 展开态数字徽标 -->
          <span
            v-if="!store.isSidebarCollapsed && item.badge !== undefined && item.badge !== ''"
            class="px-2 py-0.5 rounded-full text-[10px] font-mono transition-colors ml-1"
            :class="
              store.activeTab === item.id
                ? 'bg-white/20 text-white'
                : 'bg-[#E5E5EA] text-[#6E6E73] group-hover:text-[#1D1D1F]'
            "
          >
            {{ item.badge }}
          </span>

          <!-- 收拢时的悬停气泡 Tooltip (带微小阴影与箭头) -->
          <div
            v-if="store.isSidebarCollapsed"
            class="absolute left-full ml-3 px-3 py-2 bg-[#1D1D1F] text-white text-xs rounded-xl shadow-[0_10px_25px_rgba(0,0,0,0.25)] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-150 z-50 flex items-center space-x-2 border border-white/10"
          >
            <span class="font-bold">{{ item.label }}</span>
            <span
              v-if="item.badge !== undefined && item.badge !== ''"
              class="px-1.5 py-0.5 rounded-full text-[10px] font-mono bg-white/20 text-white"
            >
              {{ item.badge }}
            </span>
            <!-- Tooltip 左箭头 -->
            <div class="absolute right-full top-1/2 -translate-y-1/2 border-[5px] border-transparent border-r-[#1D1D1F]"></div>
          </div>
        </button>
      </div>
    </div>

    <!-- 底部：状态看板 -->
    <div class="space-y-2 pt-3 border-t border-[#E5E5EA] text-xs">
      <!-- 展开态：完整看板 -->
      <div
        v-if="!store.isSidebarCollapsed"
        class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1 font-mono text-[11px] animate-fade-in"
      >
        <div class="flex items-center justify-between text-[#86868B]">
          <span>models.dev 基准</span>
          <span class="text-[#34C759] font-bold">100% 实时</span>
        </div>
        <div class="flex items-center justify-between text-[#86868B]">
          <span>当前换算汇率</span>
          <span class="text-[#0071E3] font-bold">{{ store.syncStatus?.usd_to_cny_rate || 7.25 }}</span>
        </div>
        <div class="text-[10px] text-[#86868B] pt-0.5 truncate">
          SQLite 本地大数据库就绪
        </div>
      </div>

      <!-- 收拢态：紧凑微型胶囊 -->
      <div
        v-else
        class="p-1.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] flex flex-col items-center justify-center font-mono text-[10px] space-y-0.5 text-center animate-fade-in group relative"
      >
        <span class="text-[#86868B]">汇率</span>
        <span class="text-[#0071E3] font-bold text-[11px]">{{ store.syncStatus?.usd_to_cny_rate || 7.25 }}</span>

        <!-- 悬停气泡提示 -->
        <div
          class="absolute left-full ml-3 px-3 py-2 bg-[#1D1D1F] text-white text-xs rounded-xl shadow-xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-150 z-50 flex flex-col space-y-1 border border-white/10"
        >
          <div class="flex items-center space-x-2">
            <span class="text-[#86868B]">实时汇率:</span>
            <strong class="text-[#0071E3]">{{ store.syncStatus?.usd_to_cny_rate || 7.25 }} CNY/USD</strong>
          </div>
          <div class="text-[10px] text-[#86868B]">
            数据源: models.dev (100% 实时)
          </div>
          <div class="absolute right-full top-1/2 -translate-y-1/2 border-[5px] border-transparent border-r-[#1D1D1F]"></div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()

function formatBadgeCount(count: number): string {
  if (!count) return '0'
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`
  }
  return `${count}`
}

const navItems = computed<Array<{
  id: 'price-matrix' | 'channels' | 'models' | 'speed-tester' | 'settings'
  label: string
  icon: string
  badge?: string | number
}>>(() => [
  { id: 'price-matrix', label: '全网聚合比价', icon: '📊', badge: formatBadgeCount(store.syncStatus?.total_pricings_cached || store.comparisonMatrix.length) },
  { id: 'channels', label: '供应商与渠道', icon: '🌐', badge: formatBadgeCount(store.syncStatus?.total_active_sites || store.relaySites.length) },
  { id: 'models', label: '厂商与模型系列', icon: '🤖', badge: formatBadgeCount(store.syncStatus?.models_dev_total_models || store.modelsCatalog.length) },
  { id: 'speed-tester', label: '渠道性能实测', icon: '⏱️', badge: store.isSpeedTesting ? '测速中' : '' },
  { id: 'settings', label: '数据同步与设置', icon: '⚙️' }
])
</script>
