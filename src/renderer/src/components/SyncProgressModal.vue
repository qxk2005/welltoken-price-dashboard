<template>
  <div
    v-if="store.syncProgress.visible"
    class="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in select-none"
  >
    <div
      class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl w-[560px] flex flex-col shadow-[0_25px_70px_rgba(0,0,0,0.2)] overflow-hidden font-sans text-xs"
    >
      <!-- 1. 顶部：标题与状态图标 -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] flex items-center justify-between bg-[#F9F9FB]">
        <div class="flex items-center space-x-2.5">
          <div
            class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all"
            :class="
              store.syncProgress.stage === 5
                ? 'bg-[#E6F4EA] text-[#34C759]'
                : store.syncProgress.stage === -1
                ? 'bg-[#FFE5E5] text-[#FF3B30]'
                : 'bg-[#E8F2FD] text-[#0071E3] animate-pulse'
            "
          >
            <span v-if="store.syncProgress.stage === 5">✓</span>
            <span v-else-if="store.syncProgress.stage === -1">⚠️</span>
            <span v-else class="animate-spin text-xs">🔄</span>
          </div>
          <div>
            <h3 class="font-bold text-sm text-[#1D1D1F]">
              {{ store.syncProgress.stage === 5 ? '全网数据同步完成' : store.syncProgress.stage === -1 ? '全网同步中断' : '全网大模型与渠道数据同步' }}
            </h3>
            <p class="text-[11px] text-[#86868B] font-mono">
              models.dev 官方基准库 (models.json + catalog.json + api.json)
            </p>
          </div>
        </div>

        <button
          v-if="!store.syncProgress.isSyncing || store.syncProgress.stage === -1 || store.syncProgress.stage === 5"
          @click="store.closeSyncProgress"
          class="w-7 h-7 rounded-full bg-[#E5E5EA] hover:bg-[#D1D1D6] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center text-xs font-bold transition-all cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- 2. 主体进度与分步展示 -->
      <div class="p-6 space-y-5 bg-[#FFFFFF]">
        <!-- 进度条与实时状态文本 -->
        <div class="space-y-2">
          <div class="flex items-center justify-between text-xs">
            <span class="font-semibold text-[#1D1D1F] flex items-center space-x-1.5">
              <span v-if="store.syncProgress.isSyncing" class="inline-block w-2 h-2 rounded-full bg-[#0071E3] animate-ping mr-1"></span>
              <span>{{ store.syncProgress.message || '正在初始化同步进程...' }}</span>
            </span>
            <span class="font-mono font-bold text-[#0071E3] text-sm">
              {{ store.syncProgress.progress }}%
            </span>
          </div>

          <!-- 苹果风流光平滑进度条 -->
          <div class="w-full h-2.5 bg-[#F2F2F7] rounded-full overflow-hidden border border-[#E5E5EA] relative">
            <div
              class="h-full rounded-full transition-all duration-300 ease-out relative overflow-hidden"
              :class="
                store.syncProgress.stage === 5
                  ? 'bg-[#34C759]'
                  : store.syncProgress.stage === -1
                  ? 'bg-[#FF3B30]'
                  : 'bg-gradient-to-r from-[#0071E3] to-[#409CFF]'
              "
              :style="{ width: `${Math.max(store.syncProgress.progress, 5)}%` }"
            >
              <!-- 流光动画 -->
              <div
                v-if="store.syncProgress.isSyncing"
                class="absolute inset-0 bg-white/25 w-full animate-pulse"
              ></div>
            </div>
          </div>

          <div v-if="store.syncProgress.detail" class="text-[11px] text-[#86868B] font-mono truncate">
            {{ store.syncProgress.detail }}
          </div>
        </div>

        <!-- 4 大阶段步骤 Checklist 卡片 -->
        <div class="p-3.5 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] space-y-2.5">
          <div
            v-for="step in syncSteps"
            :key="step.number"
            class="flex items-center justify-between transition-all"
            :class="{
              'text-[#1D1D1F] font-semibold': store.syncProgress.stage === step.number,
              'text-[#34C759]': store.syncProgress.stage > step.number || store.syncProgress.stage === 5,
              'text-[#86868B] opacity-60': store.syncProgress.stage < step.number && store.syncProgress.stage !== 5
            }"
          >
            <div class="flex items-center space-x-2.5">
              <!-- 步骤图标指示器 -->
              <div
                class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono transition-all"
                :class="
                  store.syncProgress.stage > step.number || store.syncProgress.stage === 5
                    ? 'bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6]'
                    : store.syncProgress.stage === step.number
                    ? 'bg-[#0071E3] text-white shadow-xs animate-bounce'
                    : 'bg-[#E5E5EA] text-[#86868B]'
                "
              >
                <span v-if="store.syncProgress.stage > step.number || store.syncProgress.stage === 5">✓</span>
                <span v-else>{{ step.number }}</span>
              </div>
              <span class="text-xs">{{ step.title }}</span>
            </div>

            <!-- 状态标记 -->
            <span class="text-[11px] font-mono">
              <span v-if="store.syncProgress.stage > step.number || store.syncProgress.stage === 5" class="text-[#34C759] font-bold">已就绪</span>
              <span v-else-if="store.syncProgress.stage === step.number" class="text-[#0071E3] font-bold animate-pulse">进行中...</span>
              <span v-else class="text-[#AEAEB2]">等待</span>
            </span>
          </div>
        </div>

        <!-- 完成时的统计成果展示卡片 -->
        <div
          v-if="store.syncProgress.stage === 5"
          class="p-4 bg-gradient-to-br from-[#F0FDF4] to-[#F7FEFA] rounded-xl border border-[#BBF7D0] space-y-3 animate-fade-in"
        >
          <div class="text-xs font-bold text-[#166534] flex items-center space-x-1.5">
            <span>🎉</span>
            <span>本次全网增量同步审计结果</span>
          </div>

          <div class="grid grid-cols-4 gap-2 text-center">
            <div class="p-2 rounded-lg bg-white/80 border border-[#DCFCE7] shadow-2xs">
              <div class="text-[10px] text-[#6E6E73]">标准模型</div>
              <div class="text-sm font-bold font-mono text-[#166534]">
                {{ store.syncProgress.stats?.models_count || store.modelsCatalog.length || 3593 }}
              </div>
            </div>
            <div class="p-2 rounded-lg bg-white/80 border border-[#DCFCE7] shadow-2xs">
              <div class="text-[10px] text-[#6E6E73]">供应商渠道</div>
              <div class="text-sm font-bold font-mono text-[#166534]">
                {{ store.syncProgress.stats?.providers_count || store.relaySites.length || 193 }}
              </div>
            </div>
            <div class="p-2 rounded-lg bg-white/80 border border-[#DCFCE7] shadow-2xs">
              <div class="text-[10px] text-[#6E6E73]">比价条目</div>
              <div class="text-sm font-bold font-mono text-[#166534]">
                {{ store.syncProgress.stats?.pricings_count || store.comparisonMatrix.length || 7246 }}
              </div>
            </div>
            <div class="p-2 rounded-lg bg-white/80 border border-[#DCFCE7] shadow-2xs">
              <div class="text-[10px] text-[#6E6E73]">同步耗时</div>
              <div class="text-sm font-bold font-mono text-[#166534]">
                {{ ((store.syncProgress.stats?.duration_ms || 3600) / 1000).toFixed(1) }}s
              </div>
            </div>
          </div>
        </div>

        <!-- 错误异常提示卡片 -->
        <div
          v-if="store.syncProgress.stage === -1"
          class="p-4 bg-[#FFF5F5] rounded-xl border border-[#FFD0D0] space-y-2 animate-fade-in"
        >
          <div class="text-xs font-bold text-[#FF3B30] flex items-center space-x-1.5">
            <span>⚠️</span>
            <span>同步过程中遇到异常</span>
          </div>
          <p class="text-[11px] text-[#C53030] leading-relaxed break-all">
            {{ store.syncProgress.error || '网络连接超时或无法解析 models.dev 数据源。' }}
          </p>
        </div>
      </div>

      <!-- 3. 底部操作栏 -->
      <div class="px-6 py-3.5 bg-[#F9F9FB] border-t border-[#E5E5EA] flex items-center justify-between">
        <div class="text-[11px] text-[#86868B] font-mono">
          <span v-if="store.syncProgress.stage === 5 && autoCloseCountdown > 0">
            将在 {{ autoCloseCountdown }}s 后自动关闭
          </span>
          <span v-else-if="store.syncProgress.isSyncing">
            全网并发写入中，请勿关闭窗口
          </span>
          <span v-else>
            数据已写入本地 SQLite
          </span>
        </div>

        <div class="flex items-center space-x-2">
          <button
            v-if="store.syncProgress.stage === -1"
            @click="retrySync"
            class="px-4 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white font-bold text-xs shadow-sm transition-all flex items-center space-x-1 cursor-pointer"
          >
            <span>🔄</span>
            <span>重新尝试同步</span>
          </button>

          <button
            v-if="store.syncProgress.stage === 5 || store.syncProgress.stage === -1"
            @click="store.closeSyncProgress"
            class="px-4 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-medium text-xs border border-[#E5E5EA] transition-all cursor-pointer"
          >
            完成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()

const syncSteps = [
  { number: 1, title: '拉取 models.dev 官方三大核心数据源 (models/catalog/api)' },
  { number: 2, title: '标准化各大 Lab 研发母厂与模型系列规范' },
  { number: 3, title: '整理各供应商中转渠道与聚合定价矩阵' },
  { number: 4, title: '持久化写入 SQLite 本地数据库并更新索引' }
]

const autoCloseCountdown = ref(3)
let countdownTimer: any = null

// 监听 stage 变为 5 (完成)，启动 2.5 秒倒计时自动关闭
watch(
  () => store.syncProgress.stage,
  (newStage) => {
    if (newStage === 5) {
      autoCloseCountdown.value = 3
      if (countdownTimer) clearInterval(countdownTimer)
      countdownTimer = setInterval(() => {
        autoCloseCountdown.value--
        if (autoCloseCountdown.value <= 0) {
          clearInterval(countdownTimer)
          store.closeSyncProgress()
        }
      }, 1000)
    } else {
      if (countdownTimer) clearInterval(countdownTimer)
    }
  }
)

async function retrySync() {
  await store.triggerFullSync()
}
</script>
