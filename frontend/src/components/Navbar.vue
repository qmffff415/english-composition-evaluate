<script setup>
defineProps({
  examCategory: {
    type: String,
    default: '英语一'
  },
  systemStatus: {
    type: Object,
    default: () => ({ status: 'checking', milvus: {}, models: {} })
  },
  currentModelName: {
    type: String,
    default: 'deepseek-chat'
  },
  currentProviderName: {
    type: String,
    default: 'DeepSeek'
  },
  isCustomModel: {
    type: Boolean,
    default: false
  }
})

defineEmits(['openHistory', 'openModelSettings', 'openLibrary', 'switchExamCategory'])
</script>

<template>
  <header class="navbar">
    <div class="nav-container">
      <div class="brand-section">
        <div class="brand-mark">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"></path>
            <path d="M6 6h10"></path>
            <path d="M6 10h10"></path>
            <path d="m9 16 2 2 4-4"></path>
          </svg>
        </div>
        <div class="brand-text">
          <h1 class="brand-name">考研英语写作评卷</h1>
        </div>

        <!-- 考研科目快速切换胶囊 -->
        <div class="exam-category-switch">
          <button
            type="button"
            class="exam-pill-btn"
            :class="{ active: examCategory === '英语一' }"
            @click="$emit('switchExamCategory', '英语一')"
            title="切换为考研英语一（大作文满分20分图画作文，小作文满分10分）"
          >
            <span class="exam-name">英语（一）</span>
            <span class="exam-badge">20分图画</span>
          </button>
          <button
            type="button"
            class="exam-pill-btn"
            :class="{ active: examCategory === '英语二' }"
            @click="$emit('switchExamCategory', '英语二')"
            title="切换为考研英语二（大作文满分15分图表作文，小作文满分10分）"
          >
            <span class="exam-name">英语（二）</span>
            <span class="exam-badge">15分图表</span>
          </button>
        </div>
      </div>

      <div class="nav-actions">
        <!-- 知识库状态 -->
        <div class="status-chip">
          <span class="live-dot"></span>
          <span class="status-text">知识库在线</span>
        </div>

        <!-- 真题范文库 -->
        <button
          type="button"
          class="nav-btn library-btn"
          title="查阅 2010-2025 年全部 16 年真题与高分标杆范文库"
          @click="$emit('openLibrary')"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
          </svg>
          <span>真题范文库</span>
        </button>

        <!-- 模型配置 -->
        <button
          type="button"
          class="nav-btn model-btn"
          :class="{ 'is-custom': isCustomModel }"
          title="点击切换评卷大模型服务商与参数"
          @click="$emit('openModelSettings')"
        >
          <span class="provider-pill">{{ currentProviderName }}</span>
          <span class="model-name-label">{{ currentModelName }}</span>
          <span v-if="isCustomModel" class="custom-tag">自定义</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="gear-icon">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0 2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </button>

        <!-- 历史报告 -->
        <button class="nav-btn history-btn" @click="$emit('openHistory')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span>历史</span>
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  background: var(--ink);
  position: sticky;
  top: 0;
  z-index: 50;
  padding: 0;
  border-bottom: 1px solid rgba(232, 168, 56, 0.08);
}

.nav-container {
  max-width: 1340px;
  margin: 0 auto;
  padding: 0.65rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--amber) 0%, var(--amber-dim) 100%);
  color: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(232, 168, 56, 0.30);
}

.brand-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--paper);
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.brand-sub {
  font-size: 0.7rem;
  color: var(--text-on-dark-muted);
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* ── 英语一 / 英语二 试卷胶囊切换 ── */
.exam-category-switch {
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, 0.35);
  padding: 3px;
  border-radius: var(--radius-full, 9999px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  margin-left: 0.5rem;
}

.exam-pill-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.28rem 0.75rem;
  border-radius: var(--radius-full, 9999px);
  border: none;
  background: transparent;
  color: var(--text-on-dark-muted, #94a3b8);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

.exam-pill-btn:hover {
  color: var(--text-on-dark, #f8fafc);
}

.exam-pill-btn.active {
  background: linear-gradient(135deg, #e8a838 0%, #d49228 100%);
  color: #1a1714;
  box-shadow: 0 2px 8px rgba(232, 168, 56, 0.35);
}

.exam-badge {
  font-size: 0.65rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  color: inherit;
  font-weight: 500;
}

.exam-pill-btn.active .exam-badge {
  background: rgba(0, 0, 0, 0.15);
  color: #1a1714;
  font-weight: 700;
}

/* ── Nav Actions ── */
.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  color: var(--text-on-dark-muted);
  background: rgba(255, 255, 255, 0.05);
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-full);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 0 2px rgba(42, 157, 110, 0.25);
  animation: glow-breathe 2.5s ease-in-out infinite;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.7rem;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-on-dark);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.10);
  border-color: rgba(255, 255, 255, 0.18);
}

.library-btn:hover {
  border-color: rgba(42, 157, 110, 0.4);
  color: #a6e4c8;
}

.model-btn {
  font-family: var(--font-mono);
  font-size: 0.74rem;
}

.model-btn.is-custom {
  border-color: rgba(232, 168, 56, 0.3);
}

.model-btn:hover {
  border-color: var(--amber);
  color: var(--amber);
}

.custom-tag {
  font-size: 0.6rem;
  background: var(--amber);
  color: var(--ink);
  padding: 0.05rem 0.3rem;
  border-radius: 3px;
  font-weight: 700;
  font-family: var(--font-body);
}

.gear-icon {
  opacity: 0.5;
  margin-left: 1px;
  transition: all 0.3s ease;
}

.model-btn:hover .gear-icon {
  opacity: 1;
  transform: rotate(45deg);
}

/* 登录/注册按钮 */
.login-btn {
  background: rgba(153, 27, 27, 0.25);
  border-color: rgba(153, 27, 27, 0.5);
  color: #fecaca;
}

.login-btn:hover {
  background: rgba(153, 27, 27, 0.45);
  border-color: #ef4444;
  color: #ffffff;
}

/* 已登录用户胶囊 */
.user-menu-wrapper {
  position: relative;
}

.user-profile-btn {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.65rem 0.3rem 0.35rem;
  border-radius: var(--radius-full, 9999px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-on-dark, #ffffff);
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-profile-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.user-avatar-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #991b1b;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: var(--font-display, serif);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.user-name-text {
  font-size: 0.78rem;
  font-weight: 600;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow-down {
  opacity: 0.6;
  transition: transform 0.2s ease;
}

.arrow-down.open {
  transform: rotate(180deg);
}

/* 下拉菜单 Popover */
.user-dropdown-popover {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 220px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(12, 18, 34, 0.2);
  border: 1px solid rgba(12, 18, 34, 0.1);
  overflow: hidden;
  z-index: 100;
  animation: popoverFadeIn 0.18s ease;
}

@keyframes popoverFadeIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.popover-header {
  padding: 0.85rem 1rem;
  background: var(--paper-warm, #fcfbf9);
  border-bottom: 1px solid var(--paper-border, #edebe5);
}

.popover-user-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-ink, #0c1222);
}

.popover-email {
  font-size: 0.75rem;
  color: var(--text-muted, #71717a);
  margin-top: 2px;
  word-break: break-all;
}

.popover-divider {
  height: 1px;
  background: var(--paper-border, #edebe5);
}

.popover-menu {
  padding: 0.4rem;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.75rem;
  border-radius: 8px;
  border: none;
  background: transparent;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-ink, #0c1222);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.menu-item:hover {
  background: var(--paper-card, #f7f5f0);
}

.menu-item.logout {
  color: #dc2626;
}

.menu-item.logout:hover {
  background: #fef2f2;
}

@media (max-width: 860px) {
  .status-chip {
    display: none;
  }
  .library-btn span {
    display: none;
  }
}
</style>
