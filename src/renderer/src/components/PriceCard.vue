<template>
  <div
    @click="handleClick"
    class="p-4 rounded-xl cursor-pointer transition-all duration-200 border select-none relative overflow-hidden"
    :class="[
      isSelected
        ? 'bg-[#181F2E] border-blue-500/50 shadow-lg shadow-blue-500/10'
        : 'bg-[#151922] border-[#232936] hover:border-[#353E52] hover:bg-[#1A202C]',
      directionClass
    ]"
  >
    <!-- 卡片顶部：Symbol、名称与自选星标 -->
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center space-x-2">
        <div class="w-6 h-6 rounded-full bg-[#232936] flex items-center justify-center text-[10px] font-bold text-gray-300">
          {{ token.symbol.slice(0, 3) }}
        </div>
        <div>
          <span class="font-bold text-sm text-white font-mono">{{ token.symbol }}</span>
          <span class="text-[11px] text-gray-400 ml-1.5 font-sans">{{ token.name }}</span>
        </div>
      </div>
      <button
        @click.stop="store.toggleFavorite(token.symbol)"
        class="text-gray-500 hover:text-amber-400 transition-colors text-sm"
      >
        {{ isFavorite ? '★' : '☆' }}
      </button>
    </div>

    <!-- 价格与 24h 涨跌 -->
    <div class="flex items-baseline justify-between mt-1">
      <div class="font-mono text-xl font-bold tracking-tight text-white">
        ${{ formatPrice(token.price) }}
      </div>
      <div
        class="text-xs font-semibold px-2 py-0.5 rounded flex items-center space-x-0.5 font-mono"
        :class="token.change_24h >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'"
      >
        <span>{{ token.change_24h >= 0 ? '+' : '' }}{{ token.change_24h }}%</span>
      </div>
    </div>

    <!-- 24h 高低与成交额 -->
    <div class="grid grid-cols-2 gap-2 mt-3 pt-2.5 border-t border-[#232936]/60 text-[11px] text-[#8E9AA8]">
      <div>
        <span class="text-gray-500">24h 高: </span>
        <span class="font-mono text-gray-300">${{ formatPrice(token.high_24h) }}</span>
      </div>
      <div class="text-right">
        <span class="text-gray-500">24h 额: </span>
        <span class="font-mono text-gray-300">${{ formatCompact(token.volume_24h) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePriceStore } from '../stores/priceStore'
import type { TokenPriceSummary } from '../types'

const props = defineProps<{
  token: TokenPriceSummary
}>()

const store = usePriceStore()

const isSelected = computed(() => store.selectedSymbol === props.token.symbol)
const isFavorite = computed(() => store.favorites.includes(props.token.symbol))

const directionClass = computed(() => {
  const dir = store.priceDirections[props.token.symbol]
  if (dir === 'up') return 'flash-up'
  if (dir === 'down') return 'flash-down'
  return ''
})

const handleClick = () => {
  store.selectToken(props.token.symbol)
}

const formatPrice = (val: number) => {
  if (val >= 1000) return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (val >= 1) return val.toFixed(2)
  return val.toFixed(4)
}

const formatCompact = (val: number) => {
  if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(2) + 'B'
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(2) + 'M'
  if (val >= 1_000) return (val / 1_000).toFixed(1) + 'K'
  return val.toFixed(0)
}
</script>
