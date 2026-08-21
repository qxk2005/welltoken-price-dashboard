<template>
  <header class="h-14 border-b border-[#232936] bg-[#11151F]/90 backdrop-blur px-4 flex items-center justify-between select-none drag-region">
    <!-- 左侧：应用标识与状态 -->
    <div class="flex items-center space-x-3 no-drag">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
        <span class="text-white font-bold text-lg font-mono">W</span>
      </div>
      <div>
        <div class="flex items-center space-x-2">
          <span class="font-bold text-sm tracking-wide text-white font-sans">WellToken</span>
          <span class="text-xs px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono font-medium border border-blue-500/20">Pro</span>
        </div>
        <div class="flex items-center space-x-1.5 text-[11px] text-[#8E9AA8]">
          <span
            class="w-1.5 h-1.5 rounded-full"
            :class="store.isConnected ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50 animate-pulse' : 'bg-rose-500'"
          ></span>
          <span>{{ store.isConnected ? '实时行情已同步' : '连接中断重试中' }}</span>
          <span class="text-[#4B5563]">•</span>
          <span>SQLite 引擎: {{ store.backendHealthy ? '正常' : '异常' }}</span>
        </div>
      </div>
    </div>

    <!-- 中间：快速搜索框 -->
    <div class="w-72 no-drag">
      <div class="relative">
        <input
          v-model="store.searchQuery"
          type="text"
          placeholder="搜索代币名称或 Symbol (如 WELL, BTC)..."
          class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-sans"
        />
        <span class="absolute right-2.5 top-2 text-[10px] text-gray-500 font-mono">⌘K</span>
      </div>
    </div>

    <!-- 右侧：快捷操作与窗口按钮 -->
    <div class="flex items-center space-x-3 no-drag">
      <button
        @click="store.fetchSummaries()"
        class="text-xs px-2.5 py-1 rounded bg-[#1A202C] hover:bg-[#252D3D] text-gray-300 border border-[#2D3748] transition-colors flex items-center space-x-1"
        title="刷新行情"
      >
        <span>刷新</span>
      </button>

      <!-- 窗口控制按钮 (非 Mac 或自定义平台) -->
      <div class="flex items-center space-x-1 pl-2 border-l border-[#232936]">
        <button
          @click="minimize"
          class="w-7 h-7 rounded hover:bg-[#232936] text-gray-400 hover:text-white flex items-center justify-center text-xs transition-colors"
        >
          ─
        </button>
        <button
          @click="maximize"
          class="w-7 h-7 rounded hover:bg-[#232936] text-gray-400 hover:text-white flex items-center justify-center text-xs transition-colors"
        >
          □
        </button>
        <button
          @click="close"
          class="w-7 h-7 rounded hover:bg-rose-600/80 text-gray-400 hover:text-white flex items-center justify-center text-xs transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { usePriceStore } from '../stores/priceStore'

const store = usePriceStore()

const minimize = () => window.api?.minimizeWindow?.()
const maximize = () => window.api?.maximizeWindow?.()
const close = () => window.api?.closeWindow?.()
</script>

<style scoped>
.drag-region {
  -webkit-app-region: drag;
}
.no-drag {
  -webkit-app-region: no-drag;
}
</style>
