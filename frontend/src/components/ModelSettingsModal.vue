<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  targetProviderId: {
    type: String,
    default: ''
  },
  currentConfig: {
    type: Object,
    default: () => ({
      activeProviderId: 'deepseek',
      providerId: 'deepseek',
      modelName: 'deepseek-chat',
      apiKey: '',
      baseUrl: 'https://api.deepseek.com',
      isCustom: false,
      providers: {}
    })
  }
})

const emit = defineEmits(['close', 'save'])

// 内置主流大模型服务商预设模板（确保离线、首屏及断网状态下所有厂商卡片始终完备可见）
const DEFAULT_PRESETS = [
  {
    id: 'deepseek',
    name: 'DeepSeek',
    provider: 'DeepSeek',
    base_url: 'https://api.deepseek.com',
    default_model: 'deepseek-chat',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    doc_url: 'https://platform.deepseek.com/api_keys',
    description: '最具性价比，深度适配考研英语大纲评分要求'
  },
  {
    id: 'qwen',
    name: '阿里通义千问 (Qwen)',
    provider: 'Alibaba Cloud',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    default_model: 'qwen-plus',
    models: ['qwen-plus', 'qwen-max', 'qwen-turbo', 'qwen2.5-72b-instruct'],
    doc_url: 'https://dashscope.console.aliyun.com/apiKey',
    description: '中文与中英互译理解能力极强，响应迅速'
  },
  {
    id: 'moonshot',
    name: '月之暗面 (Kimi)',
    provider: 'Moonshot AI',
    base_url: 'https://api.moonshot.cn/v1',
    default_model: 'moonshot-v1-8k',
    models: ['moonshot-v1-8k', 'moonshot-v1-32k'],
    doc_url: 'https://platform.moonshot.cn/console/api-keys',
    description: '长上下文与篇章逻辑理解出色'
  },
  {
    id: 'zhipu',
    name: '智谱清言 (GLM)',
    provider: 'Zhipu AI',
    base_url: 'https://open.bigmodel.cn/api/paas/v4',
    default_model: 'glm-4-flash',
    models: ['glm-4-flash', 'glm-4', 'glm-4-plus'],
    doc_url: 'https://open.bigmodel.cn/usercenter/apikeys',
    description: '国产前沿基座模型，轻量级免费或低成本'
  },
  {
    id: 'ollama',
    name: '本地部署 Ollama',
    provider: 'Local Ollama',
    base_url: 'http://localhost:11434/v1',
    default_model: 'qwen2.5:7b',
    models: ['qwen2.5:7b', 'llama3.1:8b', 'deepseek-r1:7b'],
    doc_url: 'https://ollama.com',
    description: '完全离线私有化运行，无需消耗外部 API Token'
  },
  {
    id: 'custom',
    name: '自定义兼容接口 (Custom)',
    provider: 'Custom',
    base_url: '',
    default_model: '',
    models: [],
    doc_url: '',
    description: '支持任意第三方兼容端点或本地自建模型服务'
  }
]

// 预设服务商列表：初始即装载完整默认预设，避免异步网络延迟或未起服务时卡片丢失
const presets = ref(JSON.parse(JSON.stringify(DEFAULT_PRESETS)))
const presetsLoaded = ref(false)

// 默认各厂商初始模板映射（互不干扰）
const defaultProvidersMap = {
  deepseek: {
    modelName: 'deepseek-chat',
    apiKey: '',
    baseUrl: 'https://api.deepseek.com'
  },
  qwen: {
    modelName: 'qwen-plus',
    apiKey: '',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1'
  },
  moonshot: {
    modelName: 'moonshot-v1-8k',
    apiKey: '',
    baseUrl: 'https://api.moonshot.cn/v1'
  },
  zhipu: {
    modelName: 'glm-4-flash',
    apiKey: '',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4'
  },
  ollama: {
    modelName: 'qwen2.5:7b',
    apiKey: '',
    baseUrl: 'http://localhost:11434/v1'
  },
  custom: {
    modelName: '',
    apiKey: '',
    baseUrl: ''
  }
}

// 核心状态：每个厂商独立存储自己的配置对象，绝对不共享数据
const providerConfigs = ref(JSON.parse(JSON.stringify(defaultProvidersMap)))
const selectedProviderId = ref('deepseek')
const showApiKey = ref(false)

// 测试连通性状态
const testing = ref(false)
const testResult = ref(null)

// 当前正在查看/编辑的服务商预设元数据
const activePreset = computed(() => {
  return presets.value.find(p => p.id === selectedProviderId.value) || {
    id: selectedProviderId.value || 'custom',
    name: selectedProviderId.value === 'custom' ? '自定义兼容接口 (Custom)' : '服务商',
    models: [],
    base_url: '',
    doc_url: ''
  }
})

// 确保特定厂商配置项存在，并返回其专属引用
function ensureProviderConfig(pId) {
  if (!providerConfigs.value[pId]) {
    const preset = presets.value.find(p => p.id === pId)
    const fallback = defaultProvidersMap[pId] || { modelName: '', apiKey: '', baseUrl: '' }
    providerConfigs.value[pId] = {
      modelName: preset?.default_model || fallback.modelName || '',
      apiKey: '',
      baseUrl: preset?.base_url || fallback.baseUrl || ''
    }
  }
  return providerConfigs.value[pId]
}

// 当前选中厂商专属的配置项（实时双向绑定当前厂商自己的数据）
const currentConfigItem = computed(() => {
  return ensureProviderConfig(selectedProviderId.value)
})

// 从后端拉取预设列表（优雅合并）
async function fetchPresets() {
  if (presetsLoaded.value) return
  try {
    const res = await fetch('/api/llm/presets')
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data.presets) && data.presets.length > 0) {
        // 合并预设，保证前端兜底字段完备
        const merged = DEFAULT_PRESETS.map(dp => {
          const remote = data.presets.find(rp => rp.id === dp.id)
          return remote ? { ...dp, ...remote } : dp
        })
        data.presets.forEach(rp => {
          if (!merged.some(m => m.id === rp.id)) {
            merged.push(rp)
          }
        })
        presets.value = merged
      }
      // 用最新预设补充各厂商默认值（若前端尚无该厂商配置）
      presets.value.forEach(p => {
        if (!providerConfigs.value[p.id]) {
          providerConfigs.value[p.id] = {
            modelName: p.default_model || '',
            apiKey: '',
            baseUrl: p.base_url || ''
          }
        }
      })
    }
    presetsLoaded.value = true
  } catch (err) {
    console.warn('获取服务端模型预设列表失败，已安全回退至内置完整厂商预设')
    presets.value = JSON.parse(JSON.stringify(DEFAULT_PRESETS))
    presetsLoaded.value = true
  }
}

onMounted(() => {
  fetchPresets()
  syncFromProps()
})

watch(() => props.show, (newVal) => {
  if (newVal) {
    if (!presetsLoaded.value) {
      fetchPresets()
    }
    syncFromProps()
    testResult.value = null
  }
})

watch(() => props.targetProviderId, (newId) => {
  if (newId) {
    selectedProviderId.value = newId
    ensureProviderConfig(newId)
  }
})

// 从外部传入的 props 同步数据（保留各厂商独立配置）
function syncFromProps() {
  if (!props.currentConfig) return

  const pId = props.targetProviderId || props.currentConfig.activeProviderId || props.currentConfig.providerId || 'deepseek'
  selectedProviderId.value = pId

  // 如果传入了多厂商独立字典，逐项合并
  if (props.currentConfig.providers && typeof props.currentConfig.providers === 'object') {
    for (const [key, val] of Object.entries(props.currentConfig.providers)) {
      if (val && typeof val === 'object') {
        providerConfigs.value[key] = {
          modelName: val.modelName !== undefined ? val.modelName : (defaultProvidersMap[key]?.modelName || ''),
          apiKey: val.apiKey || '',
          baseUrl: val.baseUrl !== undefined ? val.baseUrl : (defaultProvidersMap[key]?.baseUrl || '')
        }
      }
    }
  } else if (props.currentConfig.providerId) {
    // 兼容旧格式只同步激活的那个厂商
    ensureProviderConfig(pId)
    providerConfigs.value[pId].modelName = props.currentConfig.modelName || providerConfigs.value[pId].modelName
    providerConfigs.value[pId].apiKey = props.currentConfig.apiKey || ''
    providerConfigs.value[pId].baseUrl = props.currentConfig.baseUrl || providerConfigs.value[pId].baseUrl
  }
}

// 切换厂商：仅改变当前选中的厂商标签，绝不修改、覆盖或混入任何其他厂商的数据！
function handleSelectPreset(preset) {
  selectedProviderId.value = preset.id
  ensureProviderConfig(preset.id)
  testResult.value = null
}

// 单独清空/重置当前厂商的专属配置，不影响其他任何厂商
function resetCurrentProvider() {
  const pId = selectedProviderId.value
  const preset = activePreset.value
  const fallback = defaultProvidersMap[pId] || { modelName: '', apiKey: '', baseUrl: '' }

  providerConfigs.value[pId] = {
    modelName: preset?.default_model || fallback.modelName || '',
    apiKey: '',
    baseUrl: preset?.base_url || fallback.baseUrl || ''
  }
  testResult.value = null
}

// 判断厂商是否有自定义存储的专属 Key 或配置
function isProviderConfigured(pId) {
  const conf = providerConfigs.value[pId]
  if (!conf) return false
  if (pId === 'ollama') {
    return Boolean(conf.baseUrl && conf.baseUrl !== 'http://localhost:11434/v1') ||
           Boolean(conf.modelName && conf.modelName !== 'qwen2.5:7b')
  }
  return Boolean(conf.apiKey && conf.apiKey.trim())
}

// 测试连通性（使用当前选中厂商自己的专属配置测试）
async function handleTestConnection() {
  const conf = currentConfigItem.value
  if (!conf.modelName.trim()) {
    testResult.value = { success: false, error: '请先填写或选择模型名称' }
    return
  }

  // 严禁默认借用 .env 私有密钥，非本地必须填写专属 API Key
  if (selectedProviderId.value !== 'ollama' && !conf.apiKey.trim()) {
    testResult.value = {
      success: false,
      error: `未填写 API Key！.env 属于私有配置，禁止默认借用。请在输入框中填入 ${activePreset.value.name} 的专属 API Key。`
    }
    return
  }

  testing.value = true
  testResult.value = null

  try {
    const res = await fetch('/api/llm/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: conf.apiKey.trim(),
        base_url: conf.baseUrl.trim(),
        model_name: conf.modelName.trim()
      })
    })

    const data = await res.json()
    if (res.ok && data.success) {
      testResult.value = {
        success: true,
        message: data.message || `测试成功！模型 ${data.model_name} 响应正常`,
        latency: data.latency_ms
      }
    } else {
      testResult.value = {
        success: false,
        error: data.error || '测试失败，请检查该厂商配置'
      }
    }
  } catch (err) {
    testResult.value = {
      success: false,
      error: `网络请求失败: ${err.message}`
    }
  } finally {
    testing.value = false
  }
}

// 保存配置：持久化每个厂商专属的独立数据，并将当前选中的厂商设为激活模型
function handleSave() {
  const pId = selectedProviderId.value
  const current = currentConfigItem.value

  const isCustom = Boolean(
    (current.apiKey && current.apiKey.trim()) ||
    pId !== 'deepseek' ||
    current.modelName !== 'deepseek-chat' ||
    current.baseUrl !== 'https://api.deepseek.com'
  )

  emit('save', {
    activeProviderId: pId,
    providers: JSON.parse(JSON.stringify(providerConfigs.value)),
    currentConfig: {
      providerId: pId,
      modelName: current.modelName.trim() || 'deepseek-chat',
      apiKey: current.apiKey.trim(),
      baseUrl: current.baseUrl.trim() || 'https://api.deepseek.com',
      isCustom
    }
  })
}
</script>

<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-container">
      <!-- 弹窗标题 -->
      <div class="modal-header">
        <div class="header-title-box">
          <div class="header-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
          <div>
            <h3 class="modal-title">大模型配置</h3>
            <p class="modal-subtitle">设置服务商与 API Key</p>
          </div>
        </div>
        <button type="button" class="close-btn" @click="$emit('close')">×</button>
      </div>

      <!-- 弹窗内容 -->
      <div class="modal-body">
        <!-- 常用服务商切换卡片 -->
        <div class="section-title-row">
          <span class="section-title">选择服务商</span>
        </div>

        <div class="provider-grid">
          <button
            v-for="p in presets"
            :key="p.id"
            type="button"
            class="provider-card"
            :class="{ active: selectedProviderId === p.id }"
            @click="handleSelectPreset(p)"
          >
            <div class="provider-card-top">
              <div class="provider-card-name">{{ p.name }}</div>
              <div class="provider-badge-group">
                <span
                  v-if="props.currentConfig?.activeProviderId === p.id"
                  class="provider-active-badge"
                  title="当前系统正在启用的评卷服务商"
                >
                  当前启用
                </span>
                <span
                  v-if="isProviderConfigured(p.id)"
                  class="provider-configured-badge"
                  title="该厂商已配置专属独立数据"
                >
                  已配置
                </span>
              </div>
            </div>
            <div class="provider-card-sub">{{ p.description }}</div>
          </button>
        </div>

        <!-- 当前选中厂商的专属配置表单 -->
        <div class="editing-header-bar">
          <div class="editing-info">
            <strong>{{ activePreset.name }}</strong>
          </div>
          <button
            type="button"
            class="btn-reset-provider"
            title="清空当前厂商专属 Key 与设置"
            @click="resetCurrentProvider"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="1 4 1 10 7 10"></polyline>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
            </svg>
            重置当前厂商
          </button>
        </div>

        <div class="form-grid">
          <!-- 模型名称 -->
          <div class="form-group">
            <label class="form-label">
              模型名称
              <span class="required">*</span>
            </label>
            <input
              v-model="currentConfigItem.modelName"
              type="text"
              class="form-input"
              placeholder="例如: deepseek-chat, qwen-plus, glm-4-flash"
            />
          </div>

          <!-- API Key -->
          <div class="form-group">
            <div class="label-row">
              <label class="form-label">
                API Key
                <span v-if="selectedProviderId !== 'ollama'" class="required">*</span>
              </label>
              <a
                v-if="activePreset.doc_url"
                :href="activePreset.doc_url"
                target="_blank"
                rel="noreferrer"
                class="doc-link"
              >
                获取密钥 ↗
              </a>
            </div>
            <div class="input-with-action">
              <input
                v-model="currentConfigItem.apiKey"
                :type="showApiKey ? 'text' : 'password'"
                class="form-input font-mono"
                :placeholder="`输入专属 API Key (sk-...)`"
                autocomplete="off"
              />
              <button
                type="button"
                class="input-action-btn"
                :title="showApiKey ? '隐藏密钥' : '显示密钥'"
                @click="showApiKey = !showApiKey"
              >
                <svg v-if="showApiKey" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                  <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
              </button>
            </div>
            <div class="form-hint">
              Key 仅保存在本地浏览器中，不上传服务器。
            </div>
          </div>

          <!-- Base URL -->
          <div class="form-group">
            <label class="form-label">
              API Base URL
              <span class="required">*</span>
            </label>
            <input
              v-model="currentConfigItem.baseUrl"
              type="text"
              class="form-input font-mono"
              placeholder="例如: https://api.deepseek.com 或 https://dashscope.aliyuncs.com/compatible-mode/v1"
            />
          </div>
        </div>

        <!-- 测试连通性展示区 -->
        <div class="test-row">
          <button
            type="button"
            class="btn-test"
            :disabled="testing || !currentConfigItem.modelName.trim()"
            @click="handleTestConnection"
          >
            <template v-if="testing">
              <span class="mini-spinner"></span>
              正在测试...
            </template>
            <template v-else>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
              测试连通性
            </template>
          </button>

          <!-- 测试反馈标签 -->
          <div v-if="testResult" class="test-feedback-box" :class="{ success: testResult.success, error: !testResult.success }">
            <template v-if="testResult.success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
              <span>{{ testResult.message }}</span>
            </template>
            <template v-else>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>{{ testResult.error }}</span>
            </template>
          </div>
        </div>
      </div>

      <!-- 底部操作区 -->
      <div class="modal-footer">
        <div class="footer-left">
          <span class="save-hint">启用 <strong>{{ activePreset.name }}</strong> 评卷</span>
        </div>
        <div class="footer-right">
          <button type="button" class="btn-cancel" @click="$emit('close')">
            取消
          </button>
          <button type="button" class="btn-save" @click="handleSave">
            保存并启用此模型
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(12, 18, 34, 0.72);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-container {
  background: var(--paper-warm);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  width: 100%;
  max-width: 720px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--paper-border);
}

.modal-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--paper-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--paper-card);
}

.header-title-box {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.header-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: var(--ink);
  color: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-title {
  font-family: var(--font-display);
  font-size: 1.12rem;
  font-weight: 700;
  color: var(--text-ink);
}

.modal-subtitle {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin-top: 0.15rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.35rem;
  color: var(--text-muted);
  cursor: pointer;
  line-height: 1;
  padding: 0.25rem;
  transition: color 0.15s ease;
}

.close-btn:hover {
  color: var(--text-ink);
}

.modal-body {
  padding: 1.4rem 1.5rem;
  overflow-y: auto;
}

.isolation-notice-banner {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 0.65rem 0.95rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.25rem;
  font-size: 0.78rem;
  color: #166534;
  line-height: 1.45;
}

.notice-icon {
  flex-shrink: 0;
  color: #15803d;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.65rem;
}

.section-title {
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-ink);
}

.section-tip {
  font-size: 0.74rem;
  color: var(--text-muted);
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 0.65rem;
  margin-bottom: 1.25rem;
}

.provider-card {
  padding: 0.75rem 0.85rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--paper-border);
  background: var(--paper-card);
  text-align: left;
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
}

.provider-card:hover {
  border-color: var(--slate-mid);
  transform: translateY(-1px);
}

.provider-card.active {
  border-color: var(--ink);
  background: #ffffff;
  box-shadow: 0 0 0 2px var(--ink);
}

.provider-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.4rem;
}

.provider-card-name {
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-ink);
}

.provider-badge-group {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
}

.provider-active-badge {
  font-size: 0.68rem;
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  padding: 0.1rem 0.35rem;
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.provider-configured-badge {
  font-size: 0.68rem;
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
  padding: 0.1rem 0.35rem;
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.provider-card-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  line-height: 1.35;
}

.editing-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 0.85rem;
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
}

.editing-info {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.editing-info strong {
  color: var(--text-ink);
}

.btn-reset-provider {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  padding: 0.25rem 0.55rem;
  border-radius: var(--radius-sm);
  font-size: 0.74rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-reset-provider:hover {
  background: #ffffff;
  color: var(--danger);
  border-color: var(--danger-border);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-ink);
}

.form-scope-tag {
  font-size: 0.7rem;
  background: var(--paper-subtle);
  color: var(--text-secondary);
  padding: 0.05rem 0.35rem;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.required {
  color: var(--danger);
}

.doc-link {
  font-size: 0.78rem;
  color: var(--amber-dim);
  text-decoration: none;
  font-weight: 600;
}

.doc-link:hover {
  text-decoration: underline;
}

.form-input {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  background: #ffffff;
  color: var(--text-ink);
}

.form-input:focus {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px rgba(12, 18, 34, 0.08);
}

.font-mono {
  font-family: var(--font-mono);
  font-size: 0.85rem;
}

.input-with-action {
  position: relative;
  display: flex;
  align-items: center;
}

.input-action-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s ease;
}

.input-action-btn:hover {
  color: var(--text-ink);
}

.form-hint {
  font-size: 0.74rem;
  color: var(--text-muted);
  margin-top: 0.15rem;
}

.test-row {
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px dashed var(--paper-border);
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-test {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 1rem;
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-ink);
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-test:hover:not(:disabled) {
  background: #ffffff;
  border-color: var(--ink);
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-feedback-box {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.82rem;
  padding: 0.45rem 0.8rem;
  border-radius: var(--radius-md);
}

.test-feedback-box.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.test-feedback-box.error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.modal-footer {
  padding: 1.1rem 1.5rem;
  border-top: 1px solid var(--paper-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--paper-card);
  gap: 1rem;
}

.footer-left {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.footer-left strong {
  color: var(--text-ink);
}

.footer-right {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.btn-cancel {
  padding: 0.6rem 1.1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--paper-border);
  background: var(--paper-warm);
  color: var(--text-secondary);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel:hover {
  background: #ffffff;
  color: var(--text-ink);
}

.btn-save {
  padding: 0.6rem 1.35rem;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  background: var(--ink);
  color: var(--paper);
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(12, 18, 34, 0.15);
  transition: all 0.2s ease;
}

.btn-save:hover {
  background: #18233c;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(12, 18, 34, 0.22);
}

.mini-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(12, 18, 34, 0.2);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
