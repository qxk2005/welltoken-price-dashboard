<template>
  <header class="h-12 bg-[#FFFFFF] border-b border-[#E5E5EA] px-4 flex items-center justify-between z-20 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
    <!-- 左侧 Logo 与健康状态 -->
    <div class="flex items-center space-x-3">
      <div class="flex items-center space-x-2">
        <div class="w-7 h-7 rounded-lg bg-[#0071E3] flex items-center justify-center font-black text-white text-sm shadow-sm">
          W
        </div>
        <div>
          <span class="font-bold text-sm text-[#1D1D1F] tracking-tight">WellToken</span>
          <span class="ml-1.5 px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]">
            比价与测评
          </span>
        </div>
      </div>

      <div class="h-4 w-px bg-[#E5E5EA]"></div>

      <!-- 后端健康状态指示 -->
      <div class="flex items-center space-x-1.5 text-xs">
        <span
          class="w-2 h-2 rounded-full transition-colors"
          :class="store.backendHealthy ? 'bg-[#34C759]' : 'bg-[#FF3B30] animate-pulse'"
        ></span>
        <span class="text-[#86868B] text-xs font-mono">
          {{ store.backendHealthy ? '服务在线' : '连接重试中' }}
        </span>
        <span class="text-[#D1D1D6]">•</span>
        <span class="text-[#6E6E73] text-xs">
          已收录渠道: <strong class="text-[#1D1D1F] font-mono">{{ store.relaySites.length }}</strong> 家
        </span>
        <span class="text-[#D1D1D6]">•</span>
        <span class="text-[#6E6E73] text-xs">
          标准模型: <strong class="text-[#1D1D1F] font-mono">{{ store.modelsCatalog.length }}</strong> 款
        </span>
      </div>
    </div>

    <!-- 中间全局搜索框 -->
    <div class="w-80 relative">
      <input
        v-model="store.searchQuery"
        type="text"
        placeholder="搜索模型 (如 deepseek-r1, gpt-4o) 或渠道商..."
        class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-3 py-1.5 text-xs text-[#1D1D1F] placeholder-[#86868B] transition-all focus:outline-none focus:ring-2 focus:ring-[#0071E3]/15 font-sans"
      />
      <span v-if="store.searchQuery" @click="store.searchQuery = ''" class="absolute right-2.5 top-2 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
    </div>

    <!-- 右侧功能区：实时汇率、货币切换、全量同步、环境标记 -->
    <div class="flex items-center space-x-2.5 text-xs">
      <!-- 汇率切换胶囊 -->
      <button
        @click="store.toggleCurrency"
        class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] border border-[#E5E5EA] text-[#1D1D1F] font-mono font-medium transition-all flex items-center space-x-1.5"
        title="切换 USD 刀 / CNY 人民币定价展示"
      >
        <span class="text-xs">{{ store.currency === 'USD' ? '💵 USD ($)' : '💴 CNY (￥)' }}</span>
      </button>

      <!-- 全网同步按钮 -->
      <button
        @click="store.triggerFullSync"
        :disabled="store.syncProgress.isSyncing"
        class="px-3 py-1 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-60 text-white font-medium shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer"
        :title="store.syncProgress.isSyncing ? '正在全量同步中...' : '从 models.dev 同步全网最新大模型与渠道定价数据'"
      >
        <span v-if="store.syncProgress.isSyncing" class="animate-spin text-xs">🔄</span>
        <span v-else>⚡</span>
        <span>{{ store.syncProgress.isSyncing ? `同步中 (${store.syncProgress.progress}%)` : '一键全网同步' }}</span>
      </button>

      <!-- 模式标记 -->
      <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-[#F2F2F7] text-[#6E6E73] border border-[#E5E5EA]">
        Web 实时调试模式
      </span>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()
</script>
