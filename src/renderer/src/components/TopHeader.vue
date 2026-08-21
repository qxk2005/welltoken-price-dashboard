<template>
  <header class="h-14 border-b border-[#232936] bg-[#11151F]/90 backdrop-blur px-4 flex items-center justify-between select-none drag-region">
    <!-- 左侧：应用标识与状态 -->
    <div class="flex items-center space-x-3 no-drag">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
        <span class="text-white font-bold text-lg font-mono">W</span>
      </div>
      <div>
        <div class="flex items-center space-x-2">
          <span class="font-bold text-sm tracking-wide text-white">WellToken</span>
          <span class="text-xs px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono font-medium border border-blue-500/20">比价与测评 Pro</span>
        </div>
        <div class="flex items-center space-x-2 text-[11px] text-[#8E9AA8]">
          <span
            class="w-1.5 h-1.5 rounded-full"
            :class="store.isConnected ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50 animate-pulse' : 'bg-rose-500'"
          ></span>
          <span>{{ store.isConnected ? '全网行情已同步' : '连接重试中' }}</span>
          <span class="text-[#4B5563]">•</span>
          <span>已收录渠道: {{ store.relaySites.length }} 家</span>
          <span class="text-[#4B5563]">•</span>
          <span>标准模型: {{ store.modelsCatalog.length }} 款</span>
        </div>
      </div>
    </div>

    <!-- 中间：全局搜索框 -->
    <div class="w-80 no-drag">
      <div class="relative">
        <input
          v-model="store.searchQuery"
          type="text"
          placeholder="搜索模型 (如 deepseek-r1, gpt-4o) 或中转站..."
          class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
        />
        <span class="absolute right-2.5 top-2 text-[10px] text-gray-500 font-mono">⌘K</span>
      </div>
    </div>

    <!-- 右侧：货币切换与全网同步 -->
    <div class="flex items-center space-x-3 no-drag">
      <!-- 货币切换按钮 -->
      <button
        @click="store.toggleCurrency"
        class="text-xs px-3 py-1.5 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-200 border border-[#374151] transition-all font-mono font-semibold flex items-center space-x-1.5"
        title="点击切换 USD / CNY 计价换算"
      >
        <span>{{ store.currency === 'USD' ? '💵 USD ($)' : '💴 CNY (￥)' }}</span>
      </button>

      <!-- 一键全网刷新 -->
      <button
        @click="store.triggerFullSync"
        class="text-xs px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-md shadow-blue-600/20 transition-all flex items-center space-x-1.5"
      >
        <span>⚡ 一键全网同步</span>
      </button>

      <!-- 窗口控制按钮 -->
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
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()

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
