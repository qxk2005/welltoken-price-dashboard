<template>
  <div class="h-screen w-screen flex flex-col bg-[#0B0E14] text-[#F3F4F6] overflow-hidden select-none">
    <!-- 顶部状态与导航栏 -->
    <HeaderBar />

    <!-- 主工作区内容 -->
    <main class="flex-1 flex flex-col p-3 space-y-3 overflow-hidden">
      <!-- 顶部核心资产卡片矩阵 -->
      <div class="grid grid-cols-5 gap-3">
        <PriceCard
          v-for="token in store.tokens"
          :key="token.symbol"
          :token="token"
        />
      </div>

      <!-- 下方主体：左侧专业图表 + 右侧行情列表 -->
      <div class="flex-1 grid grid-cols-12 gap-3 min-h-0">
        <!-- 左侧 K线/深度图表区 (8列) -->
        <div class="col-span-8 h-full">
          <ChartView />
        </div>

        <!-- 右侧资产监控列表 (4列) -->
        <div class="col-span-4 h-full">
          <TokenTable />
        </div>
      </div>
    </main>

    <!-- 底部状态微栏 -->
    <footer class="h-6 px-4 bg-[#080A0F] border-t border-[#232936]/60 flex items-center justify-between text-[10px] text-gray-500 font-mono">
      <div class="flex items-center space-x-3">
        <span>服务地址: {{ store.apiUrl }}</span>
        <span>•</span>
        <span>环境: Python 3.14 (pyenv WPD) + SQLite</span>
      </div>
      <div class="flex items-center space-x-3">
        <span>跨平台客户端 v1.0.0</span>
        <span>•</span>
        <span class="text-emerald-500">WebSocket 实时已连接</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { usePriceStore } from './stores/priceStore'
import HeaderBar from './components/HeaderBar.vue'
import PriceCard from './components/PriceCard.vue'
import ChartView from './components/ChartView.vue'
import TokenTable from './components/TokenTable.vue'

const store = usePriceStore()

onMounted(async () => {
  await store.initConfig()
  await store.checkHealth()
  await store.fetchSummaries()
  await store.fetchKline(store.selectedSymbol, store.currentTimeframe)
  await store.fetchDepth(store.selectedSymbol)
  store.connectWebSocket()
})
</script>
