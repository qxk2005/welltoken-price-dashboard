<template>
  <div class="fixed inset-0 bg-black/35 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in select-none">
    <div
      class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl flex flex-col shadow-[0_20px_60px_rgba(0,0,0,0.18)] overflow-hidden font-sans text-xs transition-all duration-300"
      :class="currentStep === 3 ? 'w-[1140px] max-w-[96vw] max-h-[90vh]' : 'w-[940px] max-w-[92vw] max-h-[88vh]'"
    >
      
      <!-- 1. 弹窗顶部：标题与关闭按钮 -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] flex items-center justify-between bg-[#F9F9FB]">
        <div class="flex items-center space-x-2">
          <span class="text-base">{{ props.initialChannel ? '📡' : '🚀' }}</span>
          <h3 class="font-bold text-sm text-[#1D1D1F]">
            <span v-if="props.initialChannel">重新探测与同步模型 ({{ props.initialChannel.name }})</span>
            <span v-else>添加供应商与中转渠道向导 (Relay-Watch & Smart Mapping)</span>
          </h3>
        </div>
        <button
          @click="emit('close')"
          class="w-7 h-7 rounded-full bg-[#E5E5EA] hover:bg-[#D1D1D6] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center text-xs font-bold transition-all"
        >
          ✕
        </button>
      </div>

      <!-- 2. 步骤指示器 (Apple 精简胶囊进度条) -->
      <div class="px-6 py-3 bg-[#FFFFFF] border-b border-[#E5E5EA] flex items-center justify-between">
        <div
          v-for="(step, idx) in steps"
          :key="step.number"
          class="flex items-center space-x-2 cursor-default"
          :class="{
            'text-[#0071E3] font-bold': currentStep === step.number,
            'text-[#34C759] font-medium': currentStep > step.number,
            'text-[#86868B]': currentStep < step.number
          }"
        >
          <div
            class="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-mono transition-all"
            :class="
              currentStep === step.number
                ? 'bg-[#0071E3] text-white shadow-xs'
                : currentStep > step.number
                ? 'bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6]'
                : 'bg-[#F2F2F7] text-[#86868B] border border-[#E5E5EA]'
            "
          >
            <span v-if="currentStep > step.number">✓</span>
            <span v-else>{{ step.number }}</span>
          </div>
          <span class="text-xs">{{ step.title }}</span>
          <span v-if="idx < steps.length - 1" class="text-[#D1D1D6] ml-2">›</span>
        </div>
      </div>

      <!-- 3. 步骤主体内容区 -->
      <div class="p-6 flex-1 overflow-y-auto min-h-[360px] bg-[#FFFFFF]">
        
        <!-- ==================== Step 1: 基础配置 ==================== -->
        <div v-if="currentStep === 1" class="space-y-4 animate-fade-in">
          <!-- 快捷操作：一键从 models.dev 导入官方全量数据库 -->
          <div class="p-4 bg-gradient-to-r from-[#F0F7FF] to-[#F5FAFF] rounded-2xl border border-[#CCE4FB] flex items-center justify-between shadow-xs">
            <div class="space-y-1">
              <div class="flex items-center space-x-1.5">
                <span class="text-base">⚡</span>
                <span class="font-bold text-[#0071E3] text-xs">一键导入全网官方数据库 (models.dev)</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#0071E3] text-white">推荐</span>
              </div>
              <p class="text-[11px] text-[#6E6E73]">
                无需手动配置，一键获取 {{ store.syncStatus?.total_active_sites || store.relaySites.length || 193 }} 家供应商中转渠道与数千条全网比价条目。
              </p>
            </div>

            <button
              type="button"
              @click="handleOneClickSync"
              :disabled="isSyncingModelsDev"
              class="px-4 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-50 text-white font-bold text-xs shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer whitespace-nowrap"
            >
              <span v-if="isSyncingModelsDev" class="animate-spin text-sm">⏳</span>
              <span v-else>🚀</span>
              <span>{{ isSyncingModelsDev ? '正在全网同步中...' : '立即一键全量同步' }}</span>
            </button>
          </div>

          <div class="p-3 bg-[#F2F2F7]/70 rounded-xl border border-[#E5E5EA] text-[#6E6E73] text-[11px] leading-relaxed">
            💡 或者手动接入基于 <strong>NewAPI</strong>、<strong>OneAPI</strong>、<strong>Sub2API</strong> 或自建聚合网关的中转服务。系统将自动探测连通性并拉取原始模型列表。
          </div>

          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">渠道/站点名称 (Name) *</label>
                <input
                  v-model="form.name"
                  type="text"
                  placeholder="例如: 极速云 AI 聚合 (NewAPI)"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none transition-all"
                />
              </div>

              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">API 基础端点地址 (Base URL) *</label>
                <input
                  v-model="form.base_url"
                  type="text"
                  placeholder="https://api.my-relay.com/v1"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-all"
                />
              </div>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">系统类型 (Site Type)</label>
                <select
                  v-model="form.site_type"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none transition-all"
                >
                  <option value="newapi">NewAPI / OneAPI 架构</option>
                  <option value="sub2api">Sub2API 包月/额度架构</option>
                  <option value="custom">通用自建 OpenAI 兼容网关</option>
                </select>
              </div>

              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">渠道结算货币 (Currency) *</label>
                <div class="grid grid-cols-2 gap-1.5 bg-[#F2F2F7] p-1 rounded-xl border border-[#E5E5EA]">
                  <button
                    type="button"
                    @click="form.currency = 'CNY'"
                    class="py-1 rounded-lg text-xs font-bold transition-all flex items-center justify-center space-x-1"
                    :class="form.currency === 'CNY' ? 'bg-[#FFFFFF] text-[#0071E3] shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>🇨🇳</span>
                    <span>人民币 CNY</span>
                  </button>
                  <button
                    type="button"
                    @click="form.currency = 'USD'"
                    class="py-1 rounded-lg text-xs font-bold transition-all flex items-center justify-center space-x-1"
                    :class="form.currency === 'USD' ? 'bg-[#FFFFFF] text-[#0071E3] shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>🇺🇸</span>
                    <span>美元 USD</span>
                  </button>
                </div>
              </div>

              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">充值折算汇率 (1元换多少美元额度)</label>
                <input
                  v-model.number="form.recharge_rate"
                  type="number"
                  step="0.01"
                  placeholder="1.0"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-all"
                />
              </div>
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">中转站 API Key (用于鉴权、模型拉取与实时测速)</label>
              <input
                v-model="form.api_key"
                type="password"
                placeholder="sk-..."
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-all"
              />
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">备注说明 (可选)</label>
              <input
                v-model="form.notes"
                type="text"
                placeholder="例如: 支持高并发 Claude / DeepSeek 特殊渠道"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none transition-all"
              />
            </div>
          </div>
        </div>

        <!-- ==================== Step 2: 连通性探测 & 抓取 ==================== -->
        <div v-else-if="currentStep === 2" class="space-y-5 animate-fade-in flex flex-col items-center justify-center py-6">
          <div v-if="isProbing" class="flex flex-col items-center space-y-4 py-8">
            <div class="relative w-16 h-16 flex items-center justify-center">
              <div class="absolute inset-0 rounded-full border-4 border-[#0071E3]/20 animate-ping"></div>
              <div class="w-12 h-12 rounded-full bg-[#0071E3] flex items-center justify-center text-white text-xl shadow-lg">
                📡
              </div>
            </div>
            <div class="text-center">
              <div class="font-bold text-sm text-[#1D1D1F]">正在探测端点连通性并抓取模型列表...</div>
              <div class="text-[#86868B] text-xs mt-1 font-mono">{{ form.base_url }}</div>
            </div>
          </div>

          <div v-else class="w-full space-y-4">
            <!-- 探测结果状态卡片 -->
            <div
              class="p-4 rounded-xl border flex items-center justify-between"
              :class="probeResult.is_online ? 'bg-[#E6F4EA]/40 border-[#CEEAD6]' : 'bg-[#FDE8E8]/40 border-[#FAD2D2]'"
            >
              <div class="flex items-center space-x-3">
                <div
                  class="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold"
                  :class="probeResult.is_online ? 'bg-[#34C759] text-white' : 'bg-[#FF3B30] text-white'"
                >
                  {{ probeResult.is_online ? '✓' : '✕' }}
                </div>
                <div>
                  <div class="font-bold text-xs flex items-center space-x-2" :class="probeResult.is_online ? 'text-[#137333]' : 'text-[#C5221F]'">
                    <span>{{ probeResult.is_online ? '端点连接正常 (Online)' : '端点连通失败 / 鉴权错误' }}</span>
                    <span
                      v-if="probeResult.fetch_source"
                      class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]"
                    >
                      ⚡ {{ probeResult.fetch_source }}
                    </span>
                  </div>
                  <div class="text-[11px] text-[#6E6E73] mt-0.5 font-mono">
                    HTTP 状态码: {{ probeResult.status_code || 'N/A' }} | 实时延迟: {{ probeResult.latency_ms }} ms
                  </div>
                </div>
              </div>

              <button
                @click="runProbe"
                class="px-3 py-1.5 rounded-lg bg-[#FFFFFF] border border-[#E5E5EA] hover:bg-[#F2F2F7] text-[#0071E3] font-medium transition-all"
              >
                🔄 重新探测
              </button>
            </div>

            <!-- 统计指标格 -->
            <div v-if="probeResult.is_online" class="grid grid-cols-3 gap-3">
              <div class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                <div class="text-[#86868B] text-[11px]">发现原始模型数</div>
                <div class="text-lg font-bold font-mono text-[#1D1D1F] mt-1">{{ probeResult.raw_count }}</div>
              </div>
              <div class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                <div class="text-[#86868B] text-[11px]">已精准匹配标准模型</div>
                <div class="text-lg font-bold font-mono text-[#34C759] mt-1">{{ probeResult.matched_count }}</div>
              </div>
              <div class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                <div class="text-[#86868B] text-[11px]">待确认/未匹配模型</div>
                <div class="text-lg font-bold font-mono text-[#FF9500] mt-1">{{ probeResult.unmatched_count }}</div>
              </div>
            </div>

            <!-- 目标结算分组选择器 (Group-based Pricing 支持) -->
            <div
              v-if="probeResult.available_groups && probeResult.available_groups.length > 0"
              class="p-3.5 bg-[#F2F2F7] rounded-xl border border-[#E5E5EA] space-y-2 animate-fade-in"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-1.5 text-xs font-bold text-[#1D1D1F]">
                  <span>🎯</span>
                  <span>选择目标结算分组 (Group)</span>
                </div>
                <span class="text-[11px] text-[#86868B]">共发现 {{ probeResult.available_groups.length }} 个定价分组</span>
              </div>
              <div class="flex items-center space-x-3">
                <select
                  v-model="probeResult.selected_group"
                  @change="onSelectedGroupChange"
                  class="flex-1 bg-white border border-[#E5E5EA] rounded-xl px-3 py-2 text-xs font-medium text-[#1D1D1F] focus:outline-none focus:border-[#0071E3]"
                >
                  <option
                    v-for="g in probeResult.available_groups"
                    :key="g.name"
                    :value="g.name"
                  >
                    {{ g.name }} (倍率: {{ g.ratio }}x{{ g.desc ? ` · ${g.desc}` : '' }}, 覆盖 {{ g.model_count }} 款模型)
                  </option>
                </select>
              </div>
            </div>

            <!-- Key 专属令牌特权状态卡片 -->
            <div
              v-if="probeResult.token_group || probeResult.has_special_pricing"
              class="p-3 bg-[#E8F2FD] border border-[#CCE4FB] rounded-xl flex items-center justify-between text-xs text-[#0071E3] animate-fade-in"
            >
              <div class="flex items-center space-x-2">
                <span class="font-bold">🔑 识别到令牌分组:</span>
                <span class="px-2 py-0.5 rounded bg-white font-mono font-bold text-[#0071E3] border border-[#CCE4FB] shadow-2xs">
                  {{ probeResult.token_group || '特权令牌' }}
                </span>
                <span v-if="probeResult.special_pricing_count > 0" class="text-[#137333] font-medium">
                  (已发现 {{ probeResult.special_pricing_count }} 款模型享受 Key 专属特权折扣！)
                </span>
              </div>
              <span class="text-[11px] text-[#0071E3]/80">已在第3步默认应用优惠特权价</span>
            </div>

            <div v-if="probeResult.error" class="p-3 bg-[#FFF3CD] border border-[#FFEEBA] text-[#856404] rounded-xl text-[11px]">
              ⚠️ 探测提示: {{ probeResult.error }}
            </div>
          </div>
        </div>

        <!-- ==================== Step 3: 智能映射与审核确认 ==================== -->
        <div v-else-if="currentStep === 3" class="space-y-3 animate-fade-in flex flex-col h-full">
          <!-- 筛选与统计工具条 (第一行: 匹配状态 + 全选/清空) -->
          <div class="flex items-center justify-between bg-[#F9F9FB] p-2.5 rounded-xl border border-[#E5E5EA]">
            <div class="flex items-center space-x-2">
              <span class="text-[#6E6E73] font-medium">状态筛选:</span>
              <button
                @click="mappingFilter = 'all'"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
                :class="mappingFilter === 'all' ? 'bg-[#0071E3] text-white font-bold' : 'text-[#6E6E73] hover:bg-[#E5E5EA]'"
              >
                当前视图 ({{ filteredMappings.length }})
              </button>
              <button
                @click="mappingFilter = 'matched'"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
                :class="mappingFilter === 'matched' ? 'bg-[#34C759] text-white font-bold' : 'text-[#6E6E73] hover:bg-[#E5E5EA]'"
              >
                已匹配 ({{ matchedMappingsCount }})
              </button>
              <button
                @click="mappingFilter = 'unmatched'"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
                :class="mappingFilter === 'unmatched' ? 'bg-[#FF9500] text-white font-bold' : 'text-[#6E6E73] hover:bg-[#E5E5EA]'"
              >
                待确认 ({{ unmatchedMappingsCount }})
              </button>
            </div>

            <!-- 全选 / 清空当前视图模型 & 特权倍率快捷应用 -->
            <div class="flex items-center space-x-2">
              <div v-if="hasSpecialPricingInMappings" class="flex items-center space-x-1 mr-2 bg-[#E8F2FD]/50 px-2 py-0.5 rounded-lg border border-[#CCE4FB]">
                <span class="text-[10px] text-[#0071E3] font-bold">特权倍率:</span>
                <button
                  @click="batchApplyRatio('key')"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-white text-[#0071E3] border border-[#CCE4FB] hover:bg-[#0071E3] hover:text-white transition-colors"
                >
                  全部使用Key特权
                </button>
                <button
                  @click="batchApplyRatio('public')"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-white text-[#6E6E73] border border-[#E5E5EA] hover:bg-[#F2F2F7] transition-colors"
                >
                  公开倍率
                </button>
              </div>
              <span class="text-[11px] text-[#86868B]">已选收录: <b class="text-[#0071E3] font-mono">{{ selectedMappingsCount }}</b> 款</span>
              <span class="text-[#D1D1D6]">|</span>
              <button
                @click="toggleSelectAll(true)"
                class="text-[11px] text-[#0071E3] hover:underline"
              >
                全选
              </button>
              <span class="text-[#D1D1D6]">|</span>
              <button
                @click="toggleSelectAll(false)"
                class="text-[11px] text-[#86868B] hover:underline"
              >
                清空
              </button>
            </div>
          </div>

          <!-- 分组多选胶囊筛选栏 (第二行: 严格按选中分组过滤) -->
          <div
            v-if="probeResult.available_groups && probeResult.available_groups.length > 0"
            class="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs"
          >
            <span class="text-[#6E6E73] font-medium text-[11px] whitespace-nowrap flex items-center space-x-1">
              <span>🎯</span>
              <span>分组多选过滤:</span>
            </span>
            <button
              @click="toggleGroupFilter('all')"
              class="px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all whitespace-nowrap"
              :class="selectedGroupFilters.includes('all') ? 'bg-[#1D1D1F] text-white font-bold shadow-2xs' : 'bg-[#F2F2F7] text-[#6E6E73] hover:bg-[#E5E5EA]'"
            >
              全部 ({{ mappingsList.length }})
            </button>
            <button
              v-for="g in probeResult.available_groups"
              :key="g.name"
              @click="toggleGroupFilter(g.name)"
              class="px-2.5 py-1 rounded-lg text-[10px] font-mono transition-all whitespace-nowrap flex items-center space-x-1 border"
              :class="selectedGroupFilters.includes(g.name) ? 'bg-[#0071E3] text-white font-bold border-[#0071E3] shadow-2xs' : 'bg-[#FFFFFF] text-[#6E6E73] border-[#E5E5EA] hover:border-[#0071E3]'"
            >
              <span>{{ g.name }}</span>
              <span class="opacity-80 text-[9px]">({{ getGroupModelCount(g.name) }})</span>
            </button>
          </div>

          <!-- 映射对照数据表格 -->
          <div class="flex-1 border border-[#E5E5EA] rounded-xl overflow-x-auto overflow-y-auto max-h-[460px] min-h-[340px] custom-scrollbar shadow-2xs">
            <table class="w-full min-w-[1040px] text-left border-collapse">
              <thead class="bg-[#F2F2F7] sticky top-0 z-20 text-[11px] text-[#6E6E73] border-b border-[#E5E5EA] shadow-2xs">
                <tr>
                  <th class="py-2.5 px-3 text-center w-10">收录</th>
                  <th class="py-2.5 px-3.5 min-w-[190px]">渠道模型 & 分组</th>
                  <th class="py-2.5 px-1 text-center w-6">➔</th>
                  <th class="py-2.5 px-3 min-w-[280px]">对应 models.dev 标准模型</th>
                  <th class="py-2.5 px-3 text-center w-32 font-semibold">标准官方原价 ({{ form.currency === 'USD' ? '$' : '¥' }})</th>
                  <th class="py-2.5 px-3 text-center w-28 font-semibold">计费倍率 & 机制</th>
                  <th class="py-2.5 px-3.5 text-center w-36 font-semibold">折算实际单价 (每1M - {{ form.currency === 'USD' ? 'USD $' : 'CNY ¥' }})</th>
                  <th class="py-2.5 px-3 text-center w-16">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#E5E5EA] text-[11px]">
                <tr
                  v-for="(item, idx) in filteredMappings"
                  :key="item.item_key || idx"
                  class="hover:bg-[#F9F9FB] transition-colors"
                  :class="{'bg-[#FFF9E6]/30': !item.is_matched}"
                >
                  <!-- 1. 勾选 -->
                  <td class="py-2 px-2.5 text-center">
                    <input
                      type="checkbox"
                      v-model="item.is_selected"
                      class="rounded text-[#0071E3] focus:ring-0 cursor-pointer"
                    />
                  </td>

                  <!-- 2. 原始模型名称与所属分组徽章 -->
                  <td class="py-2 px-3">
                    <div class="font-mono font-bold text-[#1D1D1F] truncate" :title="item.channel_model_name">
                      {{ item.channel_model_name }}
                    </div>
                    <div class="mt-0.5 flex items-center space-x-1">
                      <span class="px-1.5 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold inline-block shadow-2xs">
                        🎯 {{ item.group_name }}
                      </span>
                      <span
                        v-if="item.match_type"
                        class="px-1.5 py-0.2 rounded border text-[9px] font-mono inline-block shadow-2xs"
                        :class="getMatchBadgeClass(item.match_type)"
                      >
                        {{ getMatchBadgeLabel(item.match_type) }}
                      </span>
                    </div>
                  </td>

                  <!-- 3. 箭头 -->
                  <td class="py-2 px-1 text-center text-[#86868B]">➔</td>

                  <!-- 4. 目标标准模型下拉选择 (支持模糊搜索与新建别名) -->
                  <td class="py-2 px-3 min-w-[240px]">
                    <ModelSearchSelect
                      v-model="item.standard_model_id"
                      :models-catalog="store.modelsCatalog"
                      :raw-model-name="item.channel_model_name"
                      :current-price-usd="item.input_price_usd"
                      :current-price-cny="item.input_price_cny"
                      :currency="form.currency"
                      @change="onStandardModelChange(item)"
                    />
                  </td>

                  <!-- 5. 【第一段】标准官方原价 (入 / 出 / 缓) -->
                  <td class="py-2 px-2.5 text-center">
                    <div v-if="item.official_input_cny > 0 || item.official_input_price > 0" class="inline-flex flex-col items-center bg-[#F9F9FB] px-2 py-0.5 rounded-lg border border-[#E5E5EA] text-[10px] font-mono text-[#6E6E73] w-full">
                      <div class="flex items-center justify-between w-full">
                        <span>入:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.official_input_price.toFixed(3)}` : `¥${(item.official_input_cny || item.official_input_price * (store.usdToCnyRate || 7.25)).toFixed(2)}` }}</span>
                      </div>
                      <div class="flex items-center justify-between w-full">
                        <span>出:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.official_output_price.toFixed(3)}` : `¥${(item.official_output_cny || item.official_output_price * (store.usdToCnyRate || 7.25)).toFixed(2)}` }}</span>
                      </div>
                      <div v-if="(item.official_cache_cny > 0 || item.official_cache_price > 0)" class="flex items-center justify-between w-full text-[9px] text-[#86868B]">
                        <span>缓:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.official_cache_price.toFixed(3)}` : `¥${(item.official_cache_cny || item.official_cache_price * (store.usdToCnyRate || 7.25)).toFixed(2)}` }}</span>
                      </div>
                    </div>
                    <span v-else class="text-[10px] text-[#AEAEB2] font-mono">--</span>
                  </td>

                  <!-- 6. 【第二段】计费倍率 & 机制 -->
                  <td class="py-2 px-2.5 text-center">
                    <div class="flex flex-col items-center space-y-0.5">
                      <span
                        class="px-1.5 py-0.2 rounded font-mono text-[10px] font-bold border shadow-2xs"
                        :class="item.has_ratio_diff && item.applied_ratio_source === 'key' ? 'bg-[#E6F4EA] text-[#137333] border-[#CEEAD6]' : 'bg-[#F2F2F7] text-[#1D1D1F] border-[#E5E5EA]'"
                      >
                        {{ item.custom_ratio !== null ? `${item.custom_ratio}x` : '1.0x' }}
                      </span>
                      <span
                        class="text-[9px] px-1 rounded-sm"
                        :class="item.match_type === 'exact' ? 'text-[#0071E3]' : (item.match_type === 'global_alias' ? 'text-[#AF52DE]' : 'text-[#86868B]')"
                      >
                        {{ item.has_ratio_diff ? (item.applied_ratio_source === 'key' ? 'Key特权' : '公开倍率') : '分组倍率' }}
                      </span>
                    </div>
                  </td>

                  <!-- 7. 【第三段】折算实际单价 (精致高亮卡片) -->
                  <td class="py-2 px-3 text-center">
                    <div class="inline-flex flex-col items-center bg-[#F4FBF7] px-2.5 py-1 rounded-lg border border-[#CEEAD6] w-full text-[11px] font-mono">
                      <div class="flex items-center justify-between w-full space-x-2">
                        <span class="text-[#86868B]">入:</span>
                        <span class="font-bold text-[#137333]">
                          {{ form.currency === 'USD' ? `$${item.input_price_usd.toFixed(3)}` : `¥${item.input_price_cny.toFixed(2)}` }}
                        </span>
                      </div>
                      <div class="flex items-center justify-between w-full space-x-2">
                        <span class="text-[#86868B]">出:</span>
                        <span class="font-bold text-[#0071E3]">
                          {{ form.currency === 'USD' ? `$${item.output_price_usd.toFixed(3)}` : `¥${item.output_price_cny.toFixed(2)}` }}
                        </span>
                      </div>
                      <div v-if="item.cache_price_cny > 0 || item.cache_price_usd > 0" class="flex items-center justify-between w-full space-x-2 text-[10px] text-[#34C759]">
                        <span class="text-[#86868B]">缓:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.cache_price_usd.toFixed(3)}` : `¥${item.cache_price_cny.toFixed(3)}` }}</span>
                      </div>
                    </div>
                  </td>

                  <!-- 8. 固化为全局规则 -->
                  <td class="py-2 px-2 text-center whitespace-nowrap">
                    <button
                      v-if="item.standard_model_id"
                      @click="promoteAlias(item)"
                      class="text-[10px] px-2 py-0.5 rounded bg-[#F2F2F7] hover:bg-[#0071E3] hover:text-white text-[#0071E3] border border-[#E5E5EA] transition-all shadow-2xs cursor-pointer"
                      title="将此映射固化为全局智能别名库规则，未来所有渠道自动生效"
                    >
                      ⭐ 固化
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ==================== Step 4: 费率倍率确认 & 最终入库 ==================== -->
        <div v-else-if="currentStep === 4" class="space-y-4 animate-fade-in">
          <div class="p-4 bg-[#E8F2FD]/50 rounded-2xl border border-[#CCE4FB] space-y-3">
            <div class="font-bold text-xs text-[#0071E3] flex items-center space-x-1.5">
              <span>✓</span>
              <span>映射审核完成，即将生成渠道与模型定价关联</span>
            </div>
            <div class="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span class="text-[#6E6E73]">渠道名称:</span>
                <span class="font-bold text-[#1D1D1F] ml-2">{{ form.name }}</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">目标结算分组:</span>
                <span class="font-bold font-mono text-[#0071E3] ml-2">{{ probeResult.selected_group || '默认' }}</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">确认收录模型数:</span>
                <span class="font-bold font-mono text-[#34C759] ml-2">{{ selectedMappingsCount }} 款</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">充值折算汇率:</span>
                <span class="font-bold font-mono text-[#1D1D1F] ml-2">{{ form.recharge_rate }}x</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">全局兜底模型倍率:</span>
                <span class="font-bold font-mono text-[#1D1D1F] ml-2">{{ form.default_ratio }}x ({{ (form.default_ratio * 10).toFixed(1) }}折)</span>
              </div>
            </div>
          </div>

          <!-- 即将入库的模型定价清单预览 (所见即所得) -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-[#1D1D1F]">📋 即将收录入库的模型清单 (共 {{ selectedMappings.length }} 款)</span>
              <span class="text-[11px] text-[#86868B]">仅选中的条目会写入数据库</span>
            </div>
            <div class="border border-[#E5E5EA] rounded-xl overflow-hidden max-h-[140px] overflow-y-auto">
              <table class="w-full text-left border-collapse text-[11px]">
                <thead class="bg-[#F2F2F7] text-[#6E6E73] sticky top-0 border-b border-[#E5E5EA]">
                  <tr>
                    <th class="py-1.5 px-3">渠道模型名</th>
                    <th class="py-1.5 px-3">归属分组</th>
                    <th class="py-1.5 px-3">映射标准模型</th>
                    <th class="py-1.5 px-3 text-right">折算实际单价</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E5E5EA]">
                  <tr v-for="item in selectedMappings" :key="item.item_key" class="hover:bg-[#F9F9FB]">
                    <td class="py-1.5 px-3 font-mono font-bold text-[#1D1D1F]">{{ item.channel_model_name }}</td>
                    <td class="py-1.5 px-3">
                      <span class="px-1.5 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold">
                        🎯 {{ item.group_name }}
                      </span>
                    </td>
                    <td class="py-1.5 px-3 font-mono text-[#0071E3] font-semibold">{{ item.standard_model_id }}</td>
                    <td class="py-1 px-2 text-right font-mono font-bold text-[#137333]">
                      {{ form.currency === 'USD' ? `$${item.input_price_usd.toFixed(3)}` : `¥${item.input_price_cny.toFixed(2)}` }} / 1M
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="space-y-2">
            <label class="block text-[#6E6E73] font-medium">全局默认模型倍率 (Default Model Ratio)</label>
            <div class="flex items-center space-x-3">
              <input
                v-model.number="form.default_ratio"
                type="number"
                step="0.05"
                min="0.01"
                max="5.0"
                class="w-32 bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
              />
              <span class="text-[#86868B] text-xs">
                (示例: 0.65 代表官方基准价的 65%，即 6.5 折)
              </span>
            </div>
          </div>

          <div class="p-3 bg-[#F2F2F7] rounded-xl text-[11px] text-[#6E6E73] space-y-1 border border-[#E5E5EA]">
            <div class="font-bold text-[#1D1D1F] flex items-center space-x-1">
              <span>💡</span>
              <span>倍率折算优先级规则：</span>
            </div>
            <div>• 优先采用第 3 步中从中转站公开接口（/api/pricing）提取或手动设定的「原生独立倍率」；</div>
            <div>• 未提供独立倍率的模型，将统一按照上述「全局默认模型倍率」进行价格折算入库。</div>
          </div>
        </div>

      </div>

      <!-- 4. 弹窗底部操作按钮条 -->
      <div class="px-6 py-4 border-t border-[#E5E5EA] bg-[#F9F9FB] flex items-center justify-between">
        <div>
          <button
            v-if="currentStep > 1"
            @click="currentStep--"
            class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-medium transition-all"
          >
            ◀ 上一步
          </button>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="emit('close')"
            class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-medium transition-all"
          >
            取消
          </button>

          <button
            v-if="currentStep < 4"
            @click="goNextStep"
            :disabled="isNextDisabled"
            class="px-5 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white font-medium shadow-sm disabled:opacity-40 transition-all flex items-center space-x-1"
          >
            <span>下一步 ▶</span>
          </button>

          <button
            v-else
            @click="submitWizard"
            :disabled="isSubmitting"
            class="px-6 py-2 rounded-xl bg-[#34C759] hover:bg-[#2DB84D] active:bg-[#249D3F] text-white font-bold shadow-sm disabled:opacity-40 transition-all flex items-center space-x-1"
          >
            <span v-if="isSubmitting">⏳ 入库中...</span>
            <span v-else>🎉 完成并确认入库</span>
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import ModelSearchSelect from './ModelSearchSelect.vue'

const props = defineProps<{
  initialChannel?: any
  initialStep?: number
}>()

const emit = defineEmits(['close', 'success'])
const store = useDashboardStore()

const currentStep = ref(props.initialStep || 1)
const isProbing = ref(false)
const isSubmitting = ref(false)
const mappingFilter = ref<'all' | 'matched' | 'unmatched'>('all')

const steps = [
  { number: 1, title: '基础配置' },
  { number: 2, title: '连通探测' },
  { number: 3, title: '智能映射' },
  { number: 4, title: '费率入库' }
]

const form = reactive({
  name: props.initialChannel?.name || '',
  base_url: props.initialChannel?.base_url || '',
  site_type: props.initialChannel?.site_type || 'newapi',
  currency: props.initialChannel?.currency || 'CNY',
  recharge_rate: props.initialChannel?.recharge_rate ?? 1.0,
  default_ratio: 0.65,
  api_key: props.initialChannel?.api_key || '',
  notes: props.initialChannel?.notes || ''
})

onMounted(() => {
  if (props.initialStep === 2 && form.base_url) {
    runProbe()
  }
})

const probeResult = reactive({
  is_online: false,
  status_code: 0,
  latency_ms: 0,
  raw_count: 0,
  matched_count: 0,
  unmatched_count: 0,
  fetch_source: '',
  token_group: '',
  has_special_pricing: false,
  special_pricing_count: 0,
  available_groups: [] as any[],
  selected_group: '',
  error: ''
})

const mappingsList = ref<any[]>([])
const selectedGroupFilters = ref<string[]>(['all'])

const matchedMappingsCount = computed(() => filteredMappings.value.filter(m => m.is_matched).length)
const unmatchedMappingsCount = computed(() => filteredMappings.value.filter(m => !m.is_matched).length)
const selectedMappings = computed(() => mappingsList.value.filter(m => m.is_selected && m.standard_model_id))
const selectedMappingsCount = computed(() => selectedMappings.value.length)
const hasSpecialPricingInMappings = computed(() => mappingsList.value.some(m => m.has_ratio_diff))

function getGroupModelCount(gName: string) {
  return mappingsList.value.filter(m => m.group_name === gName).length
}

function toggleGroupFilter(gName: string) {
  if (gName === 'all') {
    selectedGroupFilters.value = ['all']
    return
  }
  if (selectedGroupFilters.value.includes('all')) {
    selectedGroupFilters.value = [gName]
    return
  }
  if (selectedGroupFilters.value.includes(gName)) {
    selectedGroupFilters.value = selectedGroupFilters.value.filter(g => g !== gName)
    if (selectedGroupFilters.value.length === 0) {
      selectedGroupFilters.value = ['all']
    }
  } else {
    selectedGroupFilters.value.push(gName)
  }
}

function onSelectedGroupChange() {
  const gName = probeResult.selected_group
  if (gName) {
    selectedGroupFilters.value = [gName]
  }
}

function batchApplyRatio(source: 'key' | 'public') {
  for (const m of mappingsList.value) {
    if (m.has_ratio_diff) {
      m.applied_ratio_source = source
      m.custom_ratio = source === 'key' ? m.key_ratio : m.public_ratio
    }
  }
}

const filteredMappings = computed(() => {
  let list = mappingsList.value

  // 1. 匹配状态过滤
  if (mappingFilter.value === 'matched') {
    list = list.filter(m => m.is_matched)
  } else if (mappingFilter.value === 'unmatched') {
    list = list.filter(m => !m.is_matched)
  }

  // 2. 分组多选过滤 (严格只显示选中分组的模型)
  if (!selectedGroupFilters.value.includes('all') && selectedGroupFilters.value.length > 0) {
    list = list.filter(m => selectedGroupFilters.value.includes(m.group_name))
  }

  return list
})

const isNextDisabled = computed(() => {
  if (currentStep.value === 1) {
    return !form.name.trim() || !form.base_url.trim()
  }
  if (currentStep.value === 2) {
    return isProbing.value || (!probeResult.is_online && mappingsList.value.length === 0)
  }
  if (currentStep.value === 3) {
    return selectedMappingsCount.value === 0
  }
  return false
})

async function runProbe() {
  isProbing.value = true
  probeResult.error = ''
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/probe`, {
      base_url: form.base_url,
      api_key: form.api_key,
      site_type: form.site_type,
      target_group: probeResult.selected_group || undefined
    })
    probeResult.is_online = res.data.is_online
    probeResult.status_code = res.data.status_code
    probeResult.latency_ms = res.data.latency_ms
    probeResult.raw_count = res.data.raw_count
    probeResult.matched_count = res.data.matched_count
    probeResult.unmatched_count = res.data.unmatched_count
    probeResult.fetch_source = res.data.fetch_source || ''
    probeResult.token_group = res.data.token_group || ''
    probeResult.has_special_pricing = res.data.has_special_pricing || false
    probeResult.special_pricing_count = res.data.special_pricing_count || 0
    probeResult.available_groups = res.data.available_groups || []
    probeResult.selected_group = res.data.selected_group || (probeResult.available_groups[0]?.name || '')
    probeResult.error = res.data.error

    const rawList = res.data.mappings || []
    const defaultActiveGroup = probeResult.token_group || probeResult.selected_group || (probeResult.available_groups[0]?.name || '')
    
    // 精准收敛：仅将当前默认激活分组下的匹配模型初始设为 is_selected = true，其余分组模型全部设为 false
    rawList.forEach((m: any) => {
      if (defaultActiveGroup && m.group_name === defaultActiveGroup && m.standard_model_id) {
        m.is_selected = true
      } else if (!defaultActiveGroup && m.standard_model_id) {
        m.is_selected = true
      } else {
        m.is_selected = false
      }
    })
    mappingsList.value = rawList

    // 默认分组筛选器：优先绑定当前令牌所属分组，若无则默认选中目标分组
    if (probeResult.token_group) {
      selectedGroupFilters.value = [probeResult.token_group]
    } else if (probeResult.selected_group) {
      selectedGroupFilters.value = [probeResult.selected_group]
    } else {
      selectedGroupFilters.value = ['all']
    }
  } catch (e: any) {
    probeResult.is_online = false
    probeResult.fetch_source = ''
    probeResult.token_group = ''
    probeResult.has_special_pricing = false
    probeResult.special_pricing_count = 0
    probeResult.available_groups = []
    probeResult.selected_group = ''
    probeResult.error = e.response?.data?.detail || e.message || '网络连接超时'
  } finally {
    isProbing.value = false
  }
}

async function goNextStep() {
  if (currentStep.value === 1) {
    currentStep.value = 2
    await runProbe()
  } else if (currentStep.value === 2) {
    currentStep.value = 3
  } else if (currentStep.value === 3) {
    currentStep.value = 4
  }
}

function toggleSelectAll(val: boolean) {
  filteredMappings.value.forEach(m => {
    if (m.standard_model_id) {
      m.is_selected = val
    }
  })
}

function roundNum(val: number, decimals: number): number {
  return Number(Math.round(Number(val + 'e' + decimals)) + 'e-' + decimals)
}

function onStandardModelChange(item: any) {
  if (item.standard_model_id) {
    item.is_matched = true
    item.is_selected = true
    item.match_type = 'channel_custom'
    const std = store.modelsCatalog.find(m => m.model_id.toLowerCase() === item.standard_model_id.toLowerCase())
    if (std) {
      item.standard_model_name = std.name
      item.provider = std.provider
      item.series = std.series
      item.official_input_price = std.official_input_price
      item.official_output_price = std.official_output_price
      item.official_cache_price = std.official_cache_price
      item.official_input_cny = roundNum(std.official_input_price * 7.25, 2)
      item.official_output_cny = roundNum(std.official_output_price * 7.25, 2)
      item.official_cache_cny = roundNum(std.official_cache_price * 7.25, 3)

      const ratio = item.custom_ratio !== null ? item.custom_ratio : (item.public_ratio || 1.0)
      const recharge = form.recharge_rate || 1.0
      item.input_price_usd = roundNum(std.official_input_price * ratio * recharge, 3)
      item.output_price_usd = roundNum(std.official_output_price * ratio * recharge, 3)
      item.cache_price_usd = roundNum(std.official_cache_price * ratio * recharge, 3)
      item.input_price_cny = roundNum(item.official_input_cny * ratio * recharge, 2)
      item.output_price_cny = roundNum(item.official_output_cny * ratio * recharge, 2)
      item.cache_price_cny = roundNum(item.official_cache_cny * ratio * recharge, 3)
    }
  } else {
    item.is_matched = false
    item.match_type = 'unmapped'
  }
}

async function promoteAlias(item: any) {
  try {
    await axios.post(`${store.apiUrl}/api/v1/channels/promote-alias`, {
      raw_pattern: item.channel_model_name,
      standard_model_id: item.standard_model_id,
      notes: `由向导固化的规则 (${form.name})`
    })
    item.match_type = 'global_alias'
    alert(`✓ 已将 "${item.channel_model_name}" ➔ "${item.standard_model_id}" 成功固化为全局别名规则！`)
  } catch (e: any) {
    alert(`固化失败: ${e.message}`)
  }
}

function getMatchBadgeClass(type: string) {
  switch (type) {
    case 'exact':
      return 'bg-[#E6F4EA] text-[#137333] border-[#CEEAD6]'
    case 'global_alias':
      return 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB] font-bold'
    case 'rule_normalized':
      return 'bg-[#F3E8FD] text-[#8E24AA] border-[#E1BEE7]'
    case 'channel_custom':
      return 'bg-[#E0F2FE] text-[#0369A1] border-[#BAE6FD]'
    case 'fuzzy':
      return 'bg-[#FEF3C7] text-[#92400E] border-[#FDE68A]'
    default:
      return 'bg-[#F2F2F7] text-[#86868B] border-[#E5E5EA]'
  }
}

function getMatchBadgeLabel(type: string) {
  switch (type) {
    case 'exact':
      return '精确匹配'
    case 'global_alias':
      return '全局别名'
    case 'rule_normalized':
      return '规则剥离'
    case 'channel_custom':
      return '自定义'
    case 'fuzzy':
      return '模糊推断'
    default:
      return '未识别'
  }
}

async function submitWizard() {
  isSubmitting.value = true
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/wizard-create`, {
      site_id: props.initialChannel?.id || undefined,
      name: form.name,
      base_url: form.base_url,
      api_key: form.api_key,
      site_type: form.site_type,
      currency: form.currency,
      selected_group: probeResult.selected_group,
      recharge_rate: form.recharge_rate,
      default_ratio: form.default_ratio,
      notes: form.notes,
      mappings: mappingsList.value
    })
    if (res.data.status === 'success') {
      await store.fetchRelaySites()
      await store.fetchComparisonMatrix()
      emit('success', res.data)
      emit('close')
    }
  } catch (e: any) {
    alert(`创建渠道失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isSubmitting.value = false
  }
}

const isSyncingModelsDev = ref(false)

async function handleOneClickSync() {
  isSyncingModelsDev.value = true
  try {
    await store.triggerFullSync()
    emit('success')
    emit('close')
  } catch (e: any) {
    alert(`同步失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isSyncingModelsDev.value = false
  }
}
</script>
