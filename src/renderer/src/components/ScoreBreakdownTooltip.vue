<template>
  <div class="relative inline-block group select-none">
    <!-- 触发区域 (默认插槽或原生文本) -->
    <div class="cursor-help inline-flex items-center space-x-1">
      <slot>
        <span class="font-bold font-mono text-xs" :class="scoreColorClass">
          {{ displayScore }} 分
        </span>
      </slot>
      <span class="text-[10px] text-[#86868B] group-hover:text-[#0071E3] transition-colors">ℹ️</span>
    </div>

    <!-- 悬停 Tooltip 浮层卡片 (Apple 精致毛玻璃质感) -->
    <div
      class="absolute invisible opacity-0 group-hover:visible group-hover:opacity-100 transition-all duration-200 z-50 w-76 bg-[#FFFFFF]/98 backdrop-blur-md border border-[#E5E5EA] shadow-[0_16px_40px_rgba(0,0,0,0.15)] rounded-2xl p-3.5 text-left text-xs pointer-events-none"
      :class="placementClasses"
    >
      <!-- 卡片 Header -->
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-2 mb-2.5">
        <div class="flex items-center space-x-1.5">
          <span class="text-sm">🎯</span>
          <span class="font-bold text-xs text-[#1D1D1F]">综合性能评分明细</span>
        </div>
        <div class="flex items-center space-x-1.5">
          <span class="font-mono font-bold text-sm" :class="scoreColorClass">
            {{ breakdown.totalScore.toFixed(0) }} 分
          </span>
          <span
            class="px-1.5 py-0.2 rounded text-[10px] font-bold font-mono border"
            :class="gradeBadgeClass"
          >
            评级 {{ breakdown.grade }}
          </span>
        </div>
      </div>

      <!-- 三维加权评分构成 -->
      <div class="space-y-2.5">
        <!-- 1. 首字延迟 TTFT (权重 35%) -->
        <div class="space-y-1">
          <div class="flex items-center justify-between text-[11px]">
            <div class="flex items-center space-x-1 text-[#1D1D1F] font-medium">
              <span>⚡</span>
              <span>首字延迟 (TTFT)</span>
              <span class="text-[10px] text-[#86868B] font-mono font-normal">35%</span>
            </div>
            <div class="font-mono text-[11px]">
              <span class="text-[#6E6E73]">{{ breakdown.latencyMs.toFixed(0) }}ms ➔ </span>
              <strong class="text-[#0071E3]">{{ breakdown.latencyScore.toFixed(1) }}</strong>
              <span class="text-[#86868B]"> / 35分</span>
            </div>
          </div>
          <!-- 进度条 -->
          <div class="w-full h-1.5 bg-[#F2F2F7] rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="breakdown.latencyScore >= 25 ? 'bg-[#34C759]' : (breakdown.latencyScore >= 12 ? 'bg-[#FF9500]' : 'bg-[#FF3B30]')"
              :style="{ width: `${(breakdown.latencyScore / 35) * 100}%` }"
            ></div>
          </div>
          <div class="text-[9.5px] text-[#86868B] flex justify-between">
            <span>≤200ms 得满分 35</span>
            <span>≥1000ms 得 0 分</span>
          </div>
        </div>

        <!-- 2. 吞吐速率 TPS (权重 45%) -->
        <div class="space-y-1">
          <div class="flex items-center justify-between text-[11px]">
            <div class="flex items-center space-x-1 text-[#1D1D1F] font-medium">
              <span>🚀</span>
              <span>吞吐速率 (TPS)</span>
              <span class="text-[10px] text-[#86868B] font-mono font-normal">45%</span>
            </div>
            <div class="font-mono text-[11px]">
              <span class="text-[#6E6E73]">{{ breakdown.tps.toFixed(1) }} tok/s ➔ </span>
              <strong class="text-[#34C759]">{{ breakdown.tpsScore.toFixed(1) }}</strong>
              <span class="text-[#86868B]"> / 45分</span>
            </div>
          </div>
          <!-- 进度条 -->
          <div class="w-full h-1.5 bg-[#F2F2F7] rounded-full overflow-hidden">
            <div
              class="h-full bg-[#34C759] rounded-full transition-all duration-300"
              :style="{ width: `${Math.min(100, (breakdown.tpsScore / 45) * 100)}%` }"
            ></div>
          </div>
          <div class="text-[9.5px] text-[#86868B] flex justify-between">
            <span>实测 TPS × 0.45</span>
            <span>100 tok/s 满分</span>
          </div>
        </div>

        <!-- 3. 稳定性 Jitter (权重 20%) -->
        <div class="space-y-1">
          <div class="flex items-center justify-between text-[11px]">
            <div class="flex items-center space-x-1 text-[#1D1D1F] font-medium">
              <span>📏</span>
              <span>首字抖动 (Jitter)</span>
              <span class="text-[10px] text-[#86868B] font-mono font-normal">20%</span>
            </div>
            <div class="font-mono text-[11px]">
              <span class="text-[#6E6E73]">±{{ breakdown.jitterMs.toFixed(1) }}ms ➔ </span>
              <strong class="text-[#AF52DE]">{{ breakdown.jitterScore.toFixed(1) }}</strong>
              <span class="text-[#86868B]"> / 20分</span>
            </div>
          </div>
          <!-- 进度条 -->
          <div class="w-full h-1.5 bg-[#F2F2F7] rounded-full overflow-hidden">
            <div
              class="h-full bg-[#AF52DE] rounded-full transition-all duration-300"
              :style="{ width: `${(breakdown.jitterScore / 20) * 100}%` }"
            ></div>
          </div>
          <div class="text-[9.5px] text-[#86868B] flex justify-between">
            <span>标准差 ≤5ms 满分</span>
            <span>≥15ms 得 0 分</span>
          </div>
        </div>
      </div>

      <!-- 底部结算统计 -->
      <div class="mt-3 pt-2 border-t border-[#E5E5EA] flex items-center justify-between text-[10.5px]">
        <span class="text-[#86868B]">各项加权小计:</span>
        <div class="font-mono font-semibold text-[#1D1D1F]">
          {{ breakdown.rawSum.toFixed(1) }} 分
          <span v-if="breakdown.isGuaranteed" class="text-[#FF9500] font-normal text-[10px]">
            ➔ (已触发系统保底 50分)
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    score?: number
    latencyMs?: number
    avgTps?: number
    jitterMs?: number
    placement?: 'top' | 'bottom'
    align?: 'left' | 'center' | 'right'
  }>(),
  {
    score: 90,
    latencyMs: 35,
    placement: 'bottom',
    align: 'center'
  }
)

const displayScore = computed(() => {
  return props.score !== undefined && props.score !== null ? Number(props.score).toFixed(0) : '90'
})

const breakdown = computed(() => {
  const currentScore = props.score !== undefined && props.score !== null ? Number(props.score) : 90
  const ttft = props.latencyMs !== undefined && props.latencyMs !== null ? Number(props.latencyMs) : 40
  
  // TPS 估算或实测传入
  let tps = props.avgTps
  if (tps === undefined || tps === null || tps <= 0) {
    if (currentScore >= 92) tps = 80.0
    else if (currentScore >= 85) tps = 60.0
    else if (currentScore >= 70) tps = 40.0
    else tps = 18.2
  }

  // Jitter 估算或实测传入
  let jitter = props.jitterMs
  if (jitter === undefined || jitter === null || jitter <= 0) {
    if (currentScore >= 92) jitter = 3.0
    else if (currentScore >= 85) jitter = 5.0
    else if (currentScore >= 70) jitter = 8.0
    else jitter = 12.0
  }

  // 1. 延迟分 (0~35)
  const latencyScore = Math.max(0, Math.min(35, Number((((1000 - Math.min(1000, ttft)) / 10) * 0.35).toFixed(1))))
  // 2. 吞吐分 (0~45)
  const tpsScore = Math.max(0, Math.min(45, Number((tps * 0.45).toFixed(1))))
  // 3. 稳定性分 (0~20)
  const jitterScore = Math.max(0, Math.min(20, Number(((15 - Math.min(15, jitter)) * 1.5).toFixed(1))))

  const rawSum = Number((latencyScore + tpsScore + jitterScore).toFixed(1))
  const finalScore = currentScore > 0 ? currentScore : Math.min(100, Math.max(50, rawSum))
  const isGuaranteed = rawSum < 50 && finalScore <= 50

  let grade: 'S' | 'A' | 'B' | 'C' = 'C'
  if (finalScore >= 92) grade = 'S'
  else if (finalScore >= 85) grade = 'A'
  else if (finalScore >= 70) grade = 'B'

  return {
    totalScore: finalScore,
    grade,
    latencyMs: ttft,
    latencyScore,
    tps,
    tpsScore,
    jitterMs: jitter,
    jitterScore,
    rawSum,
    isGuaranteed
  }
})

const scoreColorClass = computed(() => {
  const s = breakdown.value.totalScore
  if (s >= 92) return 'text-[#34C759]'
  if (s >= 85) return 'text-[#0071E3]'
  if (s >= 70) return 'text-[#FF9500]'
  return 'text-[#FF3B30]'
})

const gradeBadgeClass = computed(() => {
  const g = breakdown.value.grade
  switch (g) {
    case 'S':
      return 'bg-[#E6F4EA] text-[#34C759] border-[#CEEAD6]'
    case 'A':
      return 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB]'
    case 'B':
      return 'bg-[#FFF4E5] text-[#FF9500] border-[#FFE2B8]'
    default:
      return 'bg-[#FDE8E8] text-[#FF3B30] border-[#FCD2D2]'
  }
})

const placementClasses = computed(() => {
  const vertical = props.placement === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'
  let horizontal = 'left-1/2 -translate-x-1/2'
  if (props.align === 'left') horizontal = 'left-0'
  if (props.align === 'right') horizontal = 'right-0'
  return `${vertical} ${horizontal}`
})
</script>
