<template>
  <div class="h-screen w-screen flex flex-col bg-[#0B0E14] text-[#F3F4F6] overflow-hidden select-none">
    <!-- 顶部状态栏 -->
    <TopHeader />

    <!-- 中部主容器：左侧导航 + 右侧各工作台 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 侧边栏导航 -->
      <SidebarNav />

      <!-- 主工作区内容 -->
      <main class="flex-1 p-3 overflow-hidden">
        <component :is="currentView" />
      </main>
    </div>

    <!-- 底部状态微条 -->
    <footer class="h-6 px-4 bg-[#080A0F] border-t border-[#232936]/60 flex items-center justify-between text-[10px] text-gray-500 font-mono">
      <div class="flex items-center space-x-3">
        <span>后端服务: {{ store.apiUrl }}</span>
        <span>•</span>
        <span>存储引擎: SQLite 3 (SQLAlchemy 2.0 异步驱动)</span>
        <span>•</span>
        <span>参考规范: models.dev + relaywatch + token-speed-tester</span>
      </div>
      <div class="flex items-center space-x-3">
        <span>WellToken 价格与测评看板 v1.0.0</span>
        <span>•</span>
        <span :class="store.isConnected ? 'text-emerald-500' : 'text-rose-500'">
          ● {{ store.isConnected ? 'WebSocket 行情与测速流已就绪' : '连接中断' }}
        </span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useDashboardStore } from './stores/dashboardStore'
import TopHeader from './components/TopHeader.vue'
import SidebarNav from './components/SidebarNav.vue'
import PriceMatrixView from './views/PriceMatrixView.vue'
import ChannelManagementView from './views/ChannelManagementView.vue'
import ModelCatalogView from './views/ModelCatalogView.vue'
import SpeedTesterView from './views/SpeedTesterView.vue'
import SyncSettingsView from './views/SyncSettingsView.vue'

const store = useDashboardStore()

const currentView = computed(() => {
  switch (store.activeTab) {
    case 'price-matrix':
      return PriceMatrixView
    case 'channels':
      return ChannelManagementView
    case 'models':
      return ModelCatalogView
    case 'speed-tester':
      return SpeedTesterView
    case 'settings':
      return SyncSettingsView
    default:
      return PriceMatrixView
  }
})

onMounted(async () => {
  await store.init()
})
</script>
