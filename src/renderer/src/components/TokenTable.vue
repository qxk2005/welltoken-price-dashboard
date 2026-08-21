<template>
  <div class="h-full flex flex-col bg-[#151922] rounded-xl border border-[#232936] p-3 overflow-hidden">
    <!-- 列表标题与自选过滤 Tab -->
    <div class="flex items-center justify-between pb-2 border-b border-[#232936]">
      <div class="flex items-center space-x-1 bg-[#0B0E14] p-0.5 rounded-lg border border-[#232936]">
        <button
          @click="activeTab = 'all'"
          class="px-2.5 py-1 text-xs rounded font-medium transition-all"
          :class="activeTab === 'all' ? 'bg-[#232936] text-white' : 'text-gray-400 hover:text-gray-200'"
        >
          全部行情 ({{ store.filteredTokens.length }})
        </button>
        <button
          @click="activeTab = 'favorites'"
          class="px-2.5 py-1 text-xs rounded font-medium transition-all flex items-center space-x-1"
          :class="activeTab === 'favorites' ? 'bg-[#232936] text-amber-400' : 'text-gray-400 hover:text-gray-200'"
        >
          <span>自选</span>
          <span>({{ store.favoriteTokens.length }})</span>
        </button>
      </div>
    </div>

    <!-- 表头 -->
    <div class="grid grid-cols-12 gap-2 text-[11px] text-gray-400 font-medium px-2 py-2 border-b border-[#232936]/60">
      <div class="col-span-4">资产</div>
      <div class="col-span-4 text-right">最新价</div>
      <div class="col-span-4 text-right">24h 涨跌</div>
    </div>

    <!-- 行情数据行列表 -->
    <div class="flex-1 overflow-y-auto divide-y divide-[#232936]/40 pr-1 mt-1">
      <div
        v-for="item in displayTokens"
        :key="item.symbol"
        @click="store.selectToken(item.symbol)"
        class="grid grid-cols-12 gap-2 items-center px-2 py-2.5 rounded-lg cursor-pointer transition-colors text-xs"
        :class="store.selectedSymbol === item.symbol ? 'bg-blue-600/15 border border-blue-500/30' : 'hover:bg-[#1A202C]'"
      >
        <!-- 资产名称与关注星标 -->
        <div class="col-span-4 flex items-center space-x-1.5">
          <button
            @click.stop="store.toggleFavorite(item.symbol)"
            class="text-gray-500 hover:text-amber-400 transition-colors text-xs"
          >
            {{ store.favorites.includes(item.symbol) ? '★' : '☆' }}
          </button>
          <div>
            <div class="font-bold text-white font-mono">{{ item.symbol }}</div>
            <div class="text-[10px] text-gray-500 truncate max-w-[60px]">{{ item.name }}</div>
          </div>
        </div>

        <!-- 价格 -->
        <div class="col-span-4 text-right font-mono font-medium text-gray-200">
          ${{ formatPrice(item.price) }}
        </div>

        <!-- 涨跌幅 -->
        <div class="col-span-4 text-right font-mono font-semibold">
          <span
            class="px-1.5 py-0.5 rounded text-[11px]"
            :class="item.change_24h >= 0 ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'"
          >
            {{ item.change_24h >= 0 ? '+' : '' }}{{ item.change_24h }}%
          </span>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="displayTokens.length === 0" class="py-8 text-center text-xs text-gray-500">
        无匹配的代币资产
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePriceStore } from '../stores/priceStore'

const store = usePriceStore()
const activeTab = ref<'all' | 'favorites'>('all')

const displayTokens = computed(() => {
  if (activeTab.value === 'favorites') {
    return store.favoriteTokens
  }
  return store.filteredTokens
})

const formatPrice = (val: number) => {
  if (val >= 1000) return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (val >= 1) return val.toFixed(2)
  return val.toFixed(4)
}
</script>
