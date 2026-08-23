<template>
  <div class="flex flex-col h-screen w-screen bg-[#F5F5F7] text-[#1D1D1F] overflow-hidden select-none font-sans">
    <!-- 顶部状态栏 -->
    <TopHeader />

    <!-- 主体内容区：左侧导航 + 右侧主工作台 -->
    <div class="flex flex-1 overflow-hidden">
      <SidebarNav />

      <main class="flex-1 p-3 overflow-hidden bg-[#F5F5F7]">
        <component :is="currentView" />
      </main>
    </div>

    <!-- 底部极简状态栏 -->
    <footer class="h-6 bg-[#FFFFFF] border-t border-[#E5E5EA] px-3 flex items-center justify-between text-[11px] text-[#86868B] font-mono">
      <div class="flex items-center space-x-3">
        <span>后端服务: <strong class="text-[#1D1D1F]">http://127.0.0.1:8765</strong></span>
        <span>•</span>
        <span>引擎: <strong class="text-[#0071E3]">SQLite 3 (WAL 异步引擎)</strong></span>
        <span>•</span>
        <span>数据规范: models.dev + relaywatch + speed-tester</span>
      </div>
      <div class="flex items-center space-x-3">
        <span>WellToken 价格与测评看板 v1.2.0</span>
        <span>•</span>
        <span class="flex items-center space-x-1">
          <span class="w-1.5 h-1.5 rounded-full" :class="store.isConnected ? 'bg-[#34C759]' : 'bg-[#FF3B30]'"></span>
          <span>{{ store.isConnected ? '全网实时连线' : '重连中...' }}</span>
        </span>
      </div>
    </footer>

    <!-- 首次启动/数据库为空时自动弹出的引导向导 -->
    <AddChannelWizardModal
      v-if="showInitialWizardModal"
      @close="showInitialWizardModal = false"
      @saved="handleInitialWizardSaved"
    />

    <!-- 全局全网数据同步实时进度浮窗 -->
    <SyncProgressModal />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import TopHeader from './components/TopHeader.vue'
import SidebarNav from './components/SidebarNav.vue'
import AddChannelWizardModal from './components/AddChannelWizardModal.vue'
import SyncProgressModal from './components/SyncProgressModal.vue'
import PriceMatrixView from './views/PriceMatrixView.vue'
import ChannelManagementView from './views/ChannelManagementView.vue'
import ModelCatalogView from './views/ModelCatalogView.vue'
import SpeedTesterView from './views/SpeedTesterView.vue'
import SyncSettingsView from './views/SyncSettingsView.vue'
import { useDashboardStore } from './stores/dashboardStore'

const store = useDashboardStore()
const showInitialWizardModal = ref(false)

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
  // 检测数据库是否完全为空，若是则友好弹出初始化向导
  if (store.backendHealthy && store.relaySites.length === 0 && store.modelsCatalog.length === 0) {
    showInitialWizardModal.value = true
  }
})

async function handleInitialWizardSaved() {
  showInitialWizardModal.value = false
  await store.fetchRelaySites()
  await store.fetchModelsCatalog()
  await store.fetchComparisonMatrix()
  await store.fetchSyncStatus()
}
</script>
