<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  currentExamCategory: {
    type: String,
    default: '全部'
  }
})

const emit = defineEmits(['close', 'useEssay'])

// 数据状态
const essays = ref([])
const loading = ref(false)
const error = ref('')

// 筛选与搜索状态
const searchQuery = ref('')
const selectedExamCategory = ref(props.currentExamCategory || '全部') // '全部' | '英语一' | '英语二'
const selectedType = ref('全部') // '全部' | '小作文' | '大作文'
const selectedYear = ref('全部') // '全部' | 2025 | 2024 ...
const selectedCategory = ref('全部') // 体裁筛选
const selectedEssayId = ref(null)

watch(() => props.currentExamCategory, (newCat) => {
  if (newCat) selectedExamCategory.value = newCat
})

// 复制成功提示
const copiedToast = ref('')

// 获取所有体裁类型选项
const availableCategories = computed(() => {
  const cats = new Set()
  essays.value.forEach(item => {
    const matchExam = selectedExamCategory.value === '全部' || (item.exam_category || '英语二') === selectedExamCategory.value
    if (matchExam && (selectedType.value === '全部' || item.type === selectedType.value)) {
      if (item.category) cats.add(item.category)
      else if (item.sub_type) cats.add(item.sub_type)
    }
  })
  return ['全部', ...Array.from(cats)]
})

// 年份列表 (2025 -> 2010)
const availableYears = computed(() => {
  const years = Array.from(new Set(essays.value.map(e => e.year))).sort((a, b) => b - a)
  return ['全部', ...years]
})

// 过滤后的列表
const filteredEssays = computed(() => {
  let list = essays.value

  // 考试类别过滤
  if (selectedExamCategory.value !== '全部') {
    list = list.filter(e => (e.exam_category || '英语二') === selectedExamCategory.value)
  }

  // 类型过滤
  if (selectedType.value !== '全部') {
    list = list.filter(e => e.type === selectedType.value)
  }

  // 年份过滤
  if (selectedYear.value !== '全部') {
    list = list.filter(e => e.year === Number(selectedYear.value))
  }

  // 体裁过滤
  if (selectedCategory.value !== '全部') {
    list = list.filter(e => e.category === selectedCategory.value || e.sub_type === selectedCategory.value)
  }

  // 关键词检索
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(e => {
      const yearMatch = String(e.year).includes(q)
      const titleMatch = (e.title || '').toLowerCase().includes(q)
      const catMatch = (e.category || e.sub_type || '').toLowerCase().includes(q)
      const promptCnMatch = (e.prompt_cn || '').toLowerCase().includes(q)
      const promptEnMatch = (e.prompt_en || '').toLowerCase().includes(q)
      const essayMatch = (e.sample_essay || '').toLowerCase().includes(q)
      return yearMatch || titleMatch || catMatch || promptCnMatch || promptEnMatch || essayMatch
    })
  }

  return list
})

// 当前选中的范文对象
const currentEssay = computed(() => {
  if (!filteredEssays.value.length) return null
  if (selectedEssayId.value) {
    const found = filteredEssays.value.find(e => e.id === selectedEssayId.value)
    if (found) return found
  }
  return filteredEssays.value[0]
})

// 加载真题范文数据
async function loadLibraryData() {
  if (essays.value.length > 0) return
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/essay-library')
    if (!res.ok) {
      throw new Error('获取真题范文库失败')
    }
    const data = await res.json()
    if (data.success && Array.isArray(data.data)) {
      essays.value = data.data
      if (essays.value.length > 0 && !selectedEssayId.value) {
        selectedEssayId.value = essays.value[0].id
      }
    } else {
      throw new Error(data.error || '数据格式异常')
    }
  } catch (err) {
    error.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// 监听弹窗打开时加载数据
watch(
  () => props.show,
  (val) => {
    if (val) {
      loadLibraryData()
      // 如果当前没有选中项，默认选中第一篇
      if (!selectedEssayId.value && essays.value.length > 0) {
        selectedEssayId.value = essays.value[0].id
      }
    }
  },
  { immediate: true }
)

// 当过滤条件改变导致当前项不在列表中时，自动回退到过滤列表的第一项
watch(filteredEssays, (newList) => {
  if (newList.length > 0) {
    const exists = newList.some(e => e.id === selectedEssayId.value)
    if (!exists) {
      selectedEssayId.value = newList[0].id
    }
  }
})

function selectEssay(item) {
  selectedEssayId.value = item.id
}

function handleResetFilters() {
  searchQuery.value = ''
  selectedType.value = '全部'
  selectedYear.value = '全部'
  selectedCategory.value = '全部'
}

// 复制到剪贴板
async function copyText(text, label = '内容') {
  try {
    await navigator.clipboard.writeText(text)
    showToast(`✓ 已成功复制${label}到剪贴板`)
  } catch (err) {
    // 回退方法
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    showToast(`✓ 已成功复制${label}到剪贴板`)
  }
}

function showToast(msg) {
  copiedToast.value = msg
  setTimeout(() => {
    if (copiedToast.value === msg) {
      copiedToast.value = ''
    }
  }, 2200)
}

// 一键填入评卷器并开始体验
function handleUseCurrentEssay() {
  if (!currentEssay.value) return
  const essay = currentEssay.value
  
  // 组装格式规范的题目
  const header = `【${essay.year}年${essay.type} · ${essay.category || essay.sub_type}】`
  const topic = `${header} ${essay.title}（${essay.prompt_en}）`

  emit('useEssay', {
    type: essay.type,
    topic: topic,
    text: essay.sample_essay,
    exam_category: essay.exam_category || '英语二',
    item: essay
  })
  
  emit('close')
}

// 快捷键 Esc 关闭
function handleKeyDown(e) {
  if (e.key === 'Escape' && props.show) {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div v-if="show" class="library-overlay animate-fade-in" @click.self="$emit('close')">
    <div class="library-modal">
      <!-- 顶部 Header 导航栏 -->
      <header class="modal-header">
        <div class="header-left">
          <div class="header-icon-badge">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"></path>
              <path d="M6 6h10"></path>
              <path d="M6 10h10"></path>
              <path d="m9 16 2 2 4-4"></path>
            </svg>
          </div>
          <div>
            <div class="title-with-pill">
              <h2 class="modal-title">历年真题与标杆范文库</h2>
              <span class="count-pill">2010–2025 · 共{{ filteredEssays.length }}篇</span>
            </div>
            <p class="modal-subtitle">收录全套官方真题、第一档标杆范文与评分解析</p>
          </div>
        </div>

        <div class="header-actions">
          <button class="close-btn" title="关闭 (Esc)" @click="$emit('close')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </header>

      <!-- 快捷搜索与多维筛选过滤栏 -->
      <section class="filters-bar">
        <!-- 搜索输入框 -->
        <div class="search-box-wrapper">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索年份、体裁或关键词..."
          />
          <button v-if="searchQuery" class="clear-query-btn" @click="searchQuery = ''">✕</button>
        </div>

        <!-- 试卷分类切换 (全部 / 英语一 / 英语二) -->
        <div class="type-segmented exam-category-segmented">
          <button
            v-for="ec in ['全部', '英语一', '英语二']"
            :key="ec"
            type="button"
            class="segment-btn"
            :class="{ active: selectedExamCategory === ec }"
            @click="selectedExamCategory = ec"
          >
            {{ ec }}
            <span class="badge-count">
              {{ ec === '全部' ? essays.length : essays.filter(e => (e.exam_category || '英语二') === ec).length }}
            </span>
          </button>
        </div>

        <!-- 题型切换 Segmented Tabs -->
        <div class="type-segmented">
          <button
            v-for="t in ['全部', '小作文', '大作文']"
            :key="t"
            type="button"
            class="segment-btn"
            :class="{ active: selectedType === t }"
            @click="selectedType = t"
          >
            {{ t }}
            <span class="badge-count">
              {{ t === '全部' ? essays.length : essays.filter(e => e.type === t).length }}
            </span>
          </button>
        </div>

        <!-- 年份下拉/选择快捷滑块 -->
        <div class="year-select-wrap">
          <span class="filter-label">年份:</span>
          <select v-model="selectedYear" class="styled-select">
            <option v-for="y in availableYears" :key="y" :value="y">
              {{ y === '全部' ? '全部年份 (16年)' : `${y} 年` }}
            </option>
          </select>
        </div>

        <!-- 体裁下拉 -->
        <div v-if="availableCategories.length > 2" class="category-select-wrap">
          <span class="filter-label">体裁/图表:</span>
          <select v-model="selectedCategory" class="styled-select">
            <option v-for="c in availableCategories" :key="c" :value="c">
              {{ c === '全部' ? '全部体裁' : c }}
            </option>
          </select>
        </div>

        <!-- 重置条件 -->
        <button
          v-if="searchQuery || selectedType !== '全部' || selectedYear !== '全部' || selectedCategory !== '全部'"
          type="button"
          class="reset-filter-btn"
          @click="handleResetFilters"
        >
          重置筛选
        </button>
      </section>

      <!-- 主体双栏内容区域 (Master-Detail) -->
      <div class="library-body">
        <!-- 左侧：题目列表清单 -->
        <aside class="sidebar-list">
          <div class="list-meta-header">
            <span>共 {{ filteredEssays.length }} 篇真题</span>
          </div>

          <!-- 加载中/错误/空状态 -->
          <div v-if="loading" class="sidebar-status-box">
            <div class="spinner"></div>
            <span>正在加载历年真题库...</span>
          </div>

          <div v-else-if="error" class="sidebar-status-box error-box">
            <span>{{ error }}</span>
            <button class="retry-btn" @click="loadLibraryData">重试</button>
          </div>

          <div v-else-if="filteredEssays.length === 0" class="sidebar-status-box empty-box">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <p>未找到匹配的真题</p>
            <button class="clear-filter-btn" @click="handleResetFilters">清空筛选条件</button>
          </div>

          <!-- 题目卡片列表 -->
          <div v-else class="essay-cards-scroll">
            <div
              v-for="item in filteredEssays"
              :key="item.id"
              class="essay-list-card"
              :class="{ 'card-active': currentEssay && currentEssay.id === item.id }"
              @click="selectEssay(item)"
            >
              <div class="card-top-row">
                <span class="year-badge">{{ item.year }}年</span>
                <span class="type-tag" :class="item.type === '小作文' ? 'tag-small' : 'tag-big'">
                  {{ item.type }}
                </span>
                <span class="category-pill">{{ item.category || item.sub_type }}</span>
                <span class="score-pill">{{ item.score }}</span>
              </div>

              <h4 class="card-title">{{ item.title }}</h4>

              <p class="card-prompt-snip">
                {{ item.prompt_cn || item.prompt_en }}
              </p>

              <div class="card-footer-meta">
                <span class="word-stat">{{ item.word_count }} words</span>
                <span class="band-stat">{{ item.band }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- 右侧：范文深度研读视窗 (Detail View) -->
        <main class="reading-view">
          <div v-if="currentEssay" class="reading-container">
            <!-- 顶部研读卡片头部与操作栏 -->
            <div class="reading-header-panel">
              <div class="panel-left">
                <div class="meta-tags-line">
                  <span class="big-year-pill">{{ currentEssay.year }} 年</span>
                  <span class="tag-bold" :class="currentEssay.type === '小作文' ? 'tag-small' : 'tag-big'">
                    {{ currentEssay.type }}
                  </span>
                  <span class="category-capsule">
                    {{ currentEssay.category || currentEssay.sub_type }}
                  </span>
                  <span class="band-tag-gold">
                    {{ currentEssay.band }} · {{ currentEssay.score }}
                  </span>
                  <span class="word-counter-pill">
                    {{ currentEssay.word_count }} 词
                  </span>
                </div>
                <h3 class="reading-title">{{ currentEssay.title }}</h3>
              </div>

              <!-- 核心交互按钮组 -->
              <div class="action-buttons-group">
                <button
                  type="button"
                  class="action-btn btn-primary-apply"
                  @click="handleUseCurrentEssay"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                  </svg>
                  <span>填入评卷器</span>
                </button>

                <button
                  type="button"
                  class="action-btn btn-outline"
                  title="复制英文范文全文"
                  @click="copyText(currentEssay.sample_essay, '范文')"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                  <span>复制范文</span>
                </button>

                <button
                  type="button"
                  class="action-btn btn-subtle"
                  title="复制题目"
                  @click="copyText(currentEssay.prompt_cn + '\n' + currentEssay.prompt_en, '原题')"
                >
                  <span>复制题目</span>
                </button>
              </div>
            </div>

            <!-- Toast 复制提示浮层 -->
            <transition name="toast-fade">
              <div v-if="copiedToast" class="copied-toast">
                {{ copiedToast }}
              </div>
            </transition>

            <!-- 详细内容滚动卡片 -->
            <div class="reading-scroll-content">
              <!-- 1. 原题呈现与写作要求 -->
              <div class="content-block prompt-section">
                <div class="block-header">
                  <div class="block-icon">📌</div>
                  <h4 class="block-title">真题要求</h4>
                </div>
                <div class="prompt-body-card">
                  <div class="prompt-cn-box">
                    <span class="lang-label">中文要求:</span>
                    <p class="prompt-text">{{ currentEssay.prompt_cn }}</p>
                  </div>
                  <div class="prompt-en-box">
                    <span class="lang-label">Directions:</span>
                    <p class="prompt-en-text">{{ currentEssay.prompt_en }}</p>
                  </div>
                </div>
              </div>

              <!-- 2. 第一档标杆范文 -->
              <div class="content-block essay-section">
                <div class="block-header justify-between">
                  <div class="flex items-center gap-2">
                    <div class="block-icon">🏆</div>
                    <h4 class="block-title">标杆范文</h4>
                  </div>
                </div>
                <div class="essay-paper-card">
                  <pre class="essay-typography">{{ currentEssay.sample_essay }}</pre>
                </div>
              </div>

              <!-- 3. 采分点与结构剖析 -->
              <div v-if="currentEssay.analysis" class="content-block analysis-section">
                <div class="block-header">
                  <div class="block-icon">💡</div>
                  <h4 class="block-title">评分要点与结构解析</h4>
                </div>
                
                <div class="analysis-grid">
                  <!-- 谋篇布局结构 -->
                  <div class="analysis-card structure-card">
                    <h5 class="sub-title">
                      <span class="bullet">📐</span> 谋篇布局
                    </h5>
                    <p class="sub-text">{{ currentEssay.analysis.structure }}</p>
                  </div>

                  <!-- 评分采分关键点 -->
                  <div class="analysis-card scoring-card">
                    <h5 class="sub-title">
                      <span class="bullet">🎯</span> 核心采分点
                    </h5>
                    <p class="sub-text">{{ currentEssay.analysis.scoring_points }}</p>
                  </div>
                </div>

                <!-- 高分闪光句式与亮点词汇 -->
                <div v-if="currentEssay.analysis.highlights && currentEssay.analysis.highlights.length" class="highlights-box">
                  <h5 class="sub-title">
                    <span class="bullet">✨</span> 亮点表达与句式
                  </h5>
                  <div class="highlight-tags-cloud">
                    <div
                      v-for="(h, idx) in currentEssay.analysis.highlights"
                      :key="idx"
                      class="highlight-capsule"
                      title="点击复制此表达"
                      @click="copyText(h, '表达')"
                    >
                      <span>{{ h }}</span>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-detail-hint">
            <p>请在左侧列表中选择一篇真题进行研读</p>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 弹窗遮罩背景 */
.library-overlay {
  position: fixed;
  inset: 0;
  background: rgba(12, 18, 34, 0.72);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

/* 弹窗卡片主体 (宽屏大视窗，高度最大化) */
.library-modal {
  width: 95vw;
  max-width: 1420px;
  height: 90vh;
  max-height: 900px;
  background: var(--paper-warm);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  border: 1px solid var(--paper-border);
}

/* 顶部 Header */
.modal-header {
  padding: 1.15rem 1.75rem;
  background: var(--paper-card);
  border-bottom: 1px solid var(--paper-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon-badge {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--ink);
  color: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-with-pill {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.modal-title {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-ink);
  letter-spacing: -0.015em;
  margin: 0;
}

.count-pill {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--amber-dim);
  background: var(--amber-subtle);
  border: 1px solid var(--amber-border);
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-full);
}

.modal-subtitle {
  font-size: 0.82rem;
  color: var(--text-secondary);
  margin: 0.2rem 0 0 0;
}

.close-btn {
  background: transparent;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: var(--paper-subtle);
  color: var(--text-ink);
}

/* 筛选与搜索工具栏 */
.filters-bar {
  padding: 0.75rem 1.75rem;
  background: var(--paper-warm);
  border-bottom: 1px solid var(--paper-border);
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-box-wrapper {
  position: relative;
  flex: 1;
  min-width: 240px;
  max-width: 420px;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.45rem 2rem 0.45rem 2.25rem;
  font-size: 0.86rem;
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-sm);
  outline: none;
  background: #ffffff;
  color: var(--text-ink);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.search-input:focus {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px rgba(12, 18, 34, 0.08);
}

.clear-query-btn {
  position: absolute;
  right: 0.5rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0.2rem;
}

.clear-query-btn:hover {
  color: var(--text-ink);
}

/* Segmented Control 题型切换 */
.type-segmented {
  display: inline-flex;
  background: var(--paper-subtle);
  border: 1px solid var(--paper-border);
  padding: 3px;
  border-radius: var(--radius-md);
}

.segment-btn {
  background: transparent;
  border: none;
  padding: 0.35rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.segment-btn.active {
  background: #ffffff;
  color: var(--text-ink);
  box-shadow: 0 1px 3px rgba(12, 18, 34, 0.08);
}

.badge-count {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  background: rgba(12, 18, 34, 0.06);
  padding: 1px 5px;
  border-radius: 10px;
}

.segment-btn.active .badge-count {
  background: var(--ink);
  color: var(--paper);
}

/* 下拉菜单 */
.year-select-wrap,
.category-select-wrap {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.filter-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.styled-select {
  padding: 0.4rem 0.65rem;
  font-size: 0.82rem;
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-sm);
  background: #ffffff;
  color: var(--text-ink);
  outline: none;
  cursor: pointer;
}

.styled-select:focus {
  border-color: var(--ink);
}

.reset-filter-btn {
  font-size: 0.8rem;
  color: var(--danger);
  background: var(--danger-light);
  border: 1px solid var(--danger-border);
  padding: 0.35rem 0.65rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.reset-filter-btn:hover {
  background: #ffffff;
}

/* 双栏布局 */
.library-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  background: var(--paper-warm);
}

/* 左侧栏 */
.sidebar-list {
  width: 380px;
  min-width: 340px;
  background: var(--paper-card);
  border-right: 1px solid var(--paper-border);
  display: flex;
  flex-direction: column;
}

.list-meta-header {
  padding: 0.65rem 1rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--paper-border-soft);
  display: flex;
  justify-content: space-between;
  background: var(--paper-warm);
}

.hint-text {
  color: var(--text-muted);
}

.sidebar-status-box {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.88rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--paper-border);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.essay-cards-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

/* 列表单张卡片 */
.essay-list-card {
  padding: 0.85rem 1rem;
  background: #ffffff;
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
}

.essay-list-card:hover {
  border-color: var(--slate-mid);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.essay-list-card.card-active {
  background: var(--paper-subtle);
  border-color: var(--ink);
  box-shadow: 0 0 0 2px var(--ink);
}

.card-top-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.45rem;
  flex-wrap: wrap;
}

.year-badge {
  font-family: var(--font-mono);
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-ink);
  background: var(--paper-subtle);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.type-tag {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.tag-small {
  background: #eff6ff;
  color: #1d4ed8;
}

.tag-big {
  background: #fef3c7;
  color: #b45309;
}

.category-pill {
  font-size: 0.72rem;
  color: var(--text-secondary);
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.score-pill {
  font-size: 0.72rem;
  font-weight: 600;
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  margin-left: auto;
}

.card-title {
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-ink);
  margin: 0 0 0.35rem 0;
  line-height: 1.35;
}

.card-prompt-snip {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.72rem;
  color: var(--text-muted);
  border-top: 1px dashed var(--paper-border);
  padding-top: 0.35rem;
}

.word-stat {
  font-weight: 500;
}

.band-stat {
  color: var(--amber-dim);
  font-weight: 600;
}

/* 右侧研读区 */
.reading-view {
  flex: 1;
  background: var(--paper-warm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.reading-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 顶部信息面板 */
.reading-header-panel {
  padding: 1.25rem 2rem;
  background: var(--paper-card);
  border-bottom: 1px solid var(--paper-border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
}

.meta-tags-line {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.big-year-pill {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 700;
  background: var(--ink);
  color: var(--paper);
  padding: 0.2rem 0.65rem;
  border-radius: 4px;
}

.tag-bold {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.2rem 0.65rem;
  border-radius: 4px;
}

.category-capsule {
  font-size: 0.8rem;
  font-weight: 500;
  background: var(--paper-subtle);
  color: var(--text-body);
  padding: 0.2rem 0.65rem;
  border-radius: 4px;
  border: 1px solid var(--paper-border);
}

.band-tag-gold {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--amber-dim);
  background: var(--amber-subtle);
  border: 1px solid var(--amber-border);
  padding: 0.2rem 0.65rem;
  border-radius: 4px;
}

.word-counter-pill {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 500;
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
}

.reading-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-ink);
  margin: 0;
  line-height: 1.35;
}

/* 操作按钮 */
.action-buttons-group {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-shrink: 0;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.95rem;
  font-size: 0.84rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.btn-primary-apply {
  background: var(--ink);
  color: var(--paper);
  border: 1px solid transparent;
  box-shadow: 0 4px 12px rgba(12, 18, 34, 0.15);
}

.btn-primary-apply:hover {
  background: #18233c;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(12, 18, 34, 0.22);
}

.btn-outline {
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  color: var(--text-ink);
}

.btn-outline:hover {
  background: #ffffff;
  border-color: var(--ink);
}

.btn-subtle {
  background: var(--paper-subtle);
  border: 1px solid var(--paper-border);
  color: var(--text-secondary);
}

.btn-subtle:hover {
  background: #ffffff;
  color: var(--text-ink);
}

/* 复制 Toast */
.copied-toast {
  position: absolute;
  top: 5.5rem;
  right: 2rem;
  background: var(--ink);
  color: #ffffff;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  z-index: 100;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.2s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 滚动内容区 */
.reading-scroll-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem 2.5rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 内容板块 */
.content-block {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  box-shadow: var(--shadow-sm);
}

.block-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
}

.justify-between {
  justify-content: space-between;
}

.block-icon {
  font-size: 1.15rem;
}

.block-title {
  font-family: var(--font-display);
  font-size: 0.96rem;
  font-weight: 700;
  color: var(--text-ink);
  margin: 0;
}

.essay-meta-hint {
  font-size: 0.78rem;
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 0.15rem 0.55rem;
  border-radius: 4px;
  font-weight: 600;
}

/* 题目卡片排版 */
.prompt-body-card {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  background: var(--paper-warm);
  padding: 1rem 1.25rem;
  border-radius: var(--radius-sm);
  border-left: 4px solid var(--ink);
}

.lang-label {
  font-family: var(--font-display);
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
  display: block;
}

.prompt-text {
  font-size: 0.88rem;
  color: var(--text-ink);
  line-height: 1.6;
  margin: 0;
}

.prompt-en-text {
  font-size: 0.86rem;
  color: var(--text-secondary);
  line-height: 1.55;
  font-style: italic;
  margin: 0;
}

/* 范文纸张排版 */
.essay-paper-card {
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-sm);
  padding: 1.5rem 1.75rem;
}

.essay-typography {
  font-family: var(--font-body);
  font-size: 0.98rem;
  line-height: 1.85;
  color: var(--text-ink);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  letter-spacing: 0.01em;
}

/* 深度剖析网格 */
.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

@media (max-width: 900px) {
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

.analysis-card {
  padding: 1rem 1.15rem;
  border-radius: var(--radius-sm);
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
}

.structure-card {
  border-left: 3px solid var(--purple);
}

.scoring-card {
  border-left: 3px solid var(--success);
}

.sub-title {
  font-family: var(--font-display);
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--text-ink);
  margin: 0 0 0.45rem 0;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.bullet {
  font-size: 0.95rem;
}

.sub-text {
  font-size: 0.84rem;
  color: var(--text-body);
  line-height: 1.6;
  margin: 0;
}

/* 亮点标签云 */
.highlights-box {
  background: var(--paper-warm);
  border: 1px dashed var(--paper-border);
  border-radius: var(--radius-sm);
  padding: 1rem 1.15rem;
}

.highlight-tags-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.highlight-capsule {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-ink);
  background: var(--paper-subtle);
  border: 1px solid var(--paper-border);
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.15s ease;
}

.highlight-capsule:hover {
  background: #ffffff;
  border-color: var(--ink);
  transform: translateY(-1px);
}

.empty-detail-hint {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.95rem;
}

/* 响应式适配 */
@media (max-width: 1024px) {
  .library-modal {
    width: 98vw;
    height: 94vh;
  }
  .sidebar-list {
    width: 320px;
    min-width: 280px;
  }
  .reading-header-panel {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .library-body {
    flex-direction: column;
  }
  .sidebar-list {
    width: 100%;
    height: 35%;
    border-right: none;
    border-bottom: 1px solid var(--paper-border);
  }
  .reading-view {
    height: 65%;
  }
}
</style>
