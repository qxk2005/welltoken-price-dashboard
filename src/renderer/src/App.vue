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
        <span>{{ versionInfo.productName }} {{ versionInfo.fullVersion }}</span>
        <span>•</span>
        <button
          @click="showBackendDiag = true; fetchBackendDiag()"
          class="flex items-center space-x-1.5 hover:bg-[#F5F5F7] px-1.5 py-0.5 rounded transition-all cursor-pointer"
          :title="store.isConnected ? '后端服务运行正常，点击查看状态与日志' : '点击查看后端未就绪原因与日志'"
        >
          <span class="w-1.5 h-1.5 rounded-full" :class="store.isConnected ? 'bg-[#34C759]' : 'bg-[#FF3B30] animate-pulse'"></span>
          <span :class="store.isConnected ? 'text-[#86868B]' : 'text-[#FF3B30] font-bold'">{{ store.isConnected ? '全网实时连线' : '后端未就绪 (重连中...)' }}</span>
        </button>
      </div>
    </footer>

    <!-- 后端运行状态与诊断弹窗 -->
    <div
      v-if="showBackendDiag"
      class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
      @click.self="showBackendDiag = false"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-[#E5E5EA] max-w-md w-full p-5 space-y-4 font-sans animate-in fade-in zoom-in-95 duration-150">
        <div class="flex items-center justify-between pb-3 border-b border-[#E5E5EA]">
          <div class="flex items-center space-x-2">
            <span class="w-2.5 h-2.5 rounded-full" :class="store.isConnected ? 'bg-[#34C759]' : 'bg-[#FF3B30]'"></span>
            <h3 class="text-sm font-bold text-[#1D1D1F]">本地后端服务诊断</h3>
          </div>
          <button @click="showBackendDiag = false" class="text-[#86868B] hover:text-[#1D1D1F] text-lg leading-none cursor-pointer">&times;</button>
        </div>

        <div class="space-y-3 text-xs">
          <div class="bg-[#F5F5F7] p-3 rounded-xl space-y-1.5 font-mono text-[11px]">
            <div class="flex justify-between">
              <span class="text-[#86868B]">连接目标:</span>
              <span class="font-bold text-[#1D1D1F]">http://127.0.0.1:8765</span>
            </div>
            <div class="flex justify-between">
              <span class="text-[#86868B]">连接状态:</span>
              <span :class="store.isConnected ? 'text-[#34C759] font-bold' : 'text-[#FF3B30] font-bold'">
                {{ store.isConnected ? '● 正常连线 (WebSocket 活跃)' : '○ 未连接 (重连轮询中)' }}
              </span>
            </div>
            <div v-if="backendDiagInfo?.lastError" class="text-[#FF3B30] break-all pt-1 border-t border-[#E5E5EA]">
              最新报错: {{ backendDiagInfo.lastError }}
            </div>
          </div>

          <div class="text-[#86868B] leading-relaxed text-[11px]">
            提示: 本系统所有大模型价格比对与数据爬虫均在本地 Python 独立后台服务中运行。新版本已内置<strong>系统代理自动绕过</strong>与<strong>macOS 隔离属性自动脱敏</strong>机制。
          </div>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-2 border-t border-[#E5E5EA]">
          <button
            @click="handleOpenLog"
            class="px-3 py-1.5 rounded-xl border border-[#E5E5EA] text-[#1D1D1F] font-bold text-xs hover:bg-[#F5F5F7] active:bg-[#E5E5EA] transition-all flex items-center space-x-1 cursor-pointer"
          >
            <svg class="w-3.5 h-3.5 text-[#86868B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span>打开运行日志 (backend.log)</span>
          </button>
          <button
            @click="handleRestartBackend"
            :disabled="restartingBackend"
            class="px-3 py-1.5 rounded-xl bg-[#0071E3] text-white font-bold text-xs hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-50 transition-all flex items-center space-x-1 cursor-pointer"
          >
            <span>{{ restartingBackend ? '重启中...' : '重启后端服务' }}</span>
          </button>
        </div>
      </div>
    </div>

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
import OfficialPricingView from './views/OfficialPricingView.vue'
import ChannelManagementView from './views/ChannelManagementView.vue'
import ModelCatalogView from './views/ModelCatalogView.vue'
import SpeedTesterView from './views/SpeedTesterView.vue'
import SyncSettingsView from './views/SyncSettingsView.vue'
import AboutAppView from './views/AboutAppView.vue'
import { versionInfo } from './generated/version_info'
import { useDashboardStore } from './stores/dashboardStore'
import { useOfficialPricingStore } from './stores/officialPricingStore'

const store = useDashboardStore()
const officialStore = useOfficialPricingStore()
const showInitialWizardModal = ref(false)
const showBackendDiag = ref(false)
const backendDiagInfo = ref<any>(null)
const restartingBackend = ref(false)

async function fetchBackendDiag() {
  if (window.api?.getBackendStatus) {
    try {
      backendDiagInfo.value = await window.api.getBackendStatus()
    } catch {
      // ignore
    }
  }
}

async function handleOpenLog() {
  if (window.api?.openBackendLog) {
    await window.api.openBackendLog()
  }
}

async function handleRestartBackend() {
  if (window.api?.restartBackend) {
    restartingBackend.value = true
    try {
      await window.api.restartBackend()
      await new Promise((r) => setTimeout(r, 1500))
      await store.init()
      await fetchBackendDiag()
    } finally {
      restartingBackend.value = false
    }
  }
}

const currentView = computed(() => {
  switch (store.activeTab) {
    case 'price-matrix':
      return PriceMatrixView
    case 'official-pricing':
      return OfficialPricingView
    case 'channels':
      return ChannelManagementView
    case 'models':
      return ModelCatalogView
    case 'speed-tester':
      return SpeedTesterView
    case 'settings':
      return SyncSettingsView
    case 'about':
      return AboutAppView
    default:
      return OfficialPricingView
  }
})

onMounted(async () => {
  await store.init()
  await officialStore.fetchOfficialPrices()
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
