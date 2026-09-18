<template>
  <div class="workbench-wrapper" :class="{ 'ai-docked-right': aiDialogDocked, 'theme-light': themeMode === 'light', 'theme-dark': themeMode === 'dark', 'is-canvas-fullscreen': isFullscreen }">
    <!-- 动态光晕背景 -->
    <div class="workbench-ambient">
      <div class="wa-blob wa1"></div>
      <div class="wa-blob wa2"></div>
      <div class="wa-blob wa3"></div>
      <div class="wa-blob wa4"></div>
    </div>
    <!-- 完整模板代码 -->
    <div
      ref="aiDialog"
      class="ai-dialog-container"
      :class="{
        'expanded': !aiDialogCollapsed,
        'mode-bottom': aiDialogMode === 'bottom' && !aiDialogDocked,
        'mode-right': aiDialogMode === 'right' && !aiDialogDocked,
        'mode-hidden': aiDialogMode === 'hidden',
        'is-dragging': isDraggingAiDialog,
        'docked-right': aiDialogDocked
      }"
      :style="getAiDialogStyle()"
      @mousedown="startDragAiDialog"
      @click="handleAiDialogClick"
    >
      <!-- 对话框头部 -->
      <div class="ai-dialog-header" @click.stop="toggleAiDialog">
        <div class="ai-dialog-brand">
          <div class="ai-icon-wrap">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
              <line x1="8" y1="22" x2="16" y2="22"/>
            </svg>
          </div>
          <div class="ai-dialog-title" v-show="!aiDialogDocked || !aiDialogCollapsed">
            <span class="ai-title-main">AI 智能助手</span>
            <span class="ai-title-sub">{{ aiDialogCollapsed ? '点击展开对话' : '随时询问故障树相关问题' }}</span>
          </div>
        </div>

        <div class="ai-dialog-controls" v-show="!aiDialogDocked || !aiDialogCollapsed">
          <div class="ai-status" :class="{ 'thinking': aiChatBusy }">
            <span class="status-dot"></span>
            <span class="status-text">{{ aiChatBusy ? '思考中...' : '就绪' }}</span>
          </div>
          <button class="ai-toggle-btn" v-if="!aiDialogDocked && aiDialogMode !== 'hidden'" @click.stop="toggleAiDialog" title="折叠/展开">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" :style="{ transform: aiDialogCollapsed ? 'rotate(180deg)' : 'rotate(0deg)' }">
              <path d="M4 6l4 4 4-4"/>
            </svg>
          </button>
          <button class="ai-mode-btn" @click.stop="cycleAiDialogMode" :title="aiDialogDocked ? '切换到悬浮模式' : '切换展示模式 (底部/右侧/隐藏)'">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="8" cy="8" r="6"/>
              <path v-if="aiDialogDocked" d="M5 8h6M8 5v6"/>
              <path v-else d="M8 4v8M4 8h8"/>
            </svg>
          </button>
          <button v-if="aiDialogDocked" class="ai-close-dock-btn" @click.stop="undockAiDialog" title="取消固定">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4l8 8M12 4l-8 8"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 对话框内容区 -->
      <div class="ai-dialog-body" v-show="!aiDialogCollapsed || (aiDialogDocked && !aiDialogCollapsed)">
        <div class="ai-dialog-content">
          <div ref="aiDialogMessages" class="ai-messages">
            <div v-if="!aiChatMessages.length" class="ai-welcome">
              <div class="welcome-icon">
                <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4M12 8h.01"/>
                </svg>
              </div>
              <h4>故障树智能分析助手</h4>
              <p>我可以帮你分析当前故障树、解释逻辑结构、提供优化建议等。</p>
              <div class="ai-quick-actions-bubbles">
                <button v-for="(action, idx) in quickActions" :key="idx"
                        @click.stop="sendQuickAction(action)"
                        class="quick-action-bubble">
                  {{ action.label }}
                </button>
              </div>
            </div>

            <div v-for="(msg, idx) in aiChatMessages" :key="idx"
                 :class="['ai-message', msg.role === 'user' ? 'user-message' : 'assistant-message']">
              <div class="message-avatar">
                <svg v-if="msg.role === 'user'" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <path d="M12 8v8M8 12h8"/>
                </svg>
              </div>
              <div class="message-bubble">
                <div class="message-text" v-html="formatMessage(msg.text)"></div>
                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>

            <div v-if="aiChatBusy" class="ai-message assistant-message typing">
              <div class="message-avatar">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <path d="M12 8v8M8 12h8"/>
                </svg>
              </div>
              <div class="message-bubble">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
              </div>
            </div>
          </div>
          <div class="ai-input-area">
            <div class="input-wrap">
              <textarea
                v-model="aiChatInput"
                class="ai-dialog-input"
                placeholder="输入你的问题，例如：分析当前故障树的关键路径..."
                @keydown.enter.exact.prevent="sendAiChatMessage"
                @keydown.enter.shift.exact="insertNewline"
                rows="1"
                ref="aiInput"
              ></textarea>
              <button
                class="ai-send-btn"
                :disabled="!aiChatInput.trim() || aiChatBusy"
                @click.stop="sendAiChatMessage"
              >
                <svg v-if="!aiChatBusy" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
                <span v-else class="send-spinner"></span>
              </button>
            </div>
            <div class="input-hint">
              <span>Enter 发送</span>
              <span class="hint-dot">·</span>
              <span>Shift + Enter 换行</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="container" ref="container">
      <!-- 左侧悬浮导航栏 - 重构版 -->
      <nav class="floating-nav"
           :class="{ 'expanded': navExpanded, 'mobile': isMobile }"
           @mouseenter="handleNavEnter"
           @mouseleave="handleNavLeave">
        <div class="floating-nav-inner">
          <div class="nav-brand-card" @click="scrollToSection('toolbar')">
            <div class="nav-brand-mark">FTA</div>
            <div class="nav-brand-copy">
              <strong>AI FTA Workbench</strong>
              <span>从原始描述到结构化故障树的在线分析体验</span>
            </div>
          </div>

          <div class="nav-group-label">快速导航</div>

          <div class="nav-item nav-home" :class="{ 'active': activeSection === 'home' }" @click="$emit('go-home')" title="返回首页">
            <div class="nav-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
            </div>
            <span class="nav-label">返回首页</span>
            <small class="nav-meta">Landing</small>
            <div class="nav-active-indicator"></div>
          </div>

          <div class="nav-divider"></div>

          <div class="nav-item" :class="{ 'active': activeSection === 'ai' }" @click="scrollToSection('ai')" title="AI 生产输入">
            <div class="nav-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
            </div>
            <span class="nav-label">AI 生产输入</span>
            <small class="nav-meta">抽取源文本</small>
            <div class="nav-active-indicator"></div>
          </div>

          <div class="nav-item" :class="{ 'active': activeSection === 'dot' }" @click="scrollToSection('dot')" title="DOT 控制台">
            <div class="nav-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <line x1="8" y1="8" x2="16" y2="8"/>
                <line x1="8" y1="12" x2="16" y2="12"/>
                <line x1="8" y1="16" x2="12" y2="16"/>
                <circle cx="17" cy="16" r="1.5" fill="currentColor" stroke="none"/>
              </svg>
            </div>
            <span class="nav-label">DOT 控制台</span>
            <small class="nav-meta">解析与导出</small>
            <div class="nav-active-indicator"></div>
          </div>

          <div class="nav-item" :class="{ 'active': activeSection === 'toolbar' }" @click="scrollToSection('toolbar')" title="节点工具栏">
            <div class="nav-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
              </svg>
            </div>
            <span class="nav-label">节点工具栏</span>
            <small class="nav-meta">拖拽建立结构</small>
            <div class="nav-active-indicator"></div>
          </div>

          <div class="nav-item" :class="{ 'active': activeSection === 'props' }" @click="scrollToSection('props')" title="属性面板">
            <div class="nav-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <span class="nav-label">属性面板</span>
            <small class="nav-meta">节点详情</small>
            <div v-if="selectedNodes.length > 0 || selectedNode" class="nav-badge">{{ selectedNodes.length || 1 }}</div>
            <div class="nav-active-indicator"></div>
          </div>

          <div class="nav-item" :class="{ 'active': activeSection === 'history' }" @click="scrollToSection('history')" title="历史记录">
            <div class="nav-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <span class="nav-label">历史记录</span>
            <small class="nav-meta">回溯分析过程</small>
            <div class="nav-active-indicator"></div>
          </div>

          <div class="nav-divider"></div>

          <div class="nav-item nav-canvas" :class="{ 'active': activeSection === 'canvas' }" @click="scrollToSection('canvas')" title="画布区域">
            <div class="nav-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
            <span class="nav-label">画布区域</span>
            <small class="nav-meta">查看当前故障树</small>
            <div class="nav-active-indicator"></div>
          </div>

          <div class="nav-spacer"></div>

          <button
            class="theme-toggle-nav"
            :title="themeMode === 'light' ? '切换到深色模式' : '切换到浅色模式'"
            @click.stop="toggleThemeMode"
          >
            <div class="nav-icon-wrap theme-toggle-icon-wrap">
              <svg v-if="themeMode === 'light'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="4"/>
                <path d="M12 2v2"/>
                <path d="M12 20v2"/>
                <path d="m4.93 4.93 1.41 1.41"/>
                <path d="m17.66 17.66 1.41 1.41"/>
                <path d="M2 12h2"/>
                <path d="M20 12h2"/>
                <path d="m6.34 17.66-1.41 1.41"/>
                <path d="m19.07 4.93-1.41 1.41"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3a6 6 0 1 0 9 9 9 9 0 1 1-9-9z"/>
              </svg>
            </div>
            <div class="theme-toggle-copy" v-show="navExpanded">
              <strong>{{ themeMode === 'light' ? '浅色模式' : '深色模式' }}</strong>
              <span>{{ themeMode === 'light' ? '点击切换深色' : '点击切换浅色' }}</span>
            </div>
          </button>
        </div>
      </nav>

      <!-- 移动端底部 Tab 栏 -->
      <nav v-if="isMobile" class="mobile-tab-bar">
        <div class="mobile-tab-item" :class="{ 'active': activeSection === 'ai' }" @click="scrollToSection('ai')">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span>AI输入</span>
        </div>
        <div class="mobile-tab-item" :class="{ 'active': activeSection === 'dot' }" @click="scrollToSection('dot')">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
          <span>DOT</span>
        </div>
        <div class="mobile-tab-item" :class="{ 'active': activeSection === 'canvas' }" @click="scrollToSection('canvas')">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
          <span>画布</span>
        </div>
        <div class="mobile-tab-item" :class="{ 'active': activeSection === 'toolbar' }" @click="scrollToSection('toolbar')">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          <span>工具</span>
        </div>
        <div class="mobile-tab-item" :class="{ 'active': activeSection === 'props' }" @click="scrollToSection('props')">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span>属性</span>
        </div>
      </nav>

      <!-- 中间：主内容区（画布） -->
      <div class="main-content" :class="{ 'ai-docked': aiDialogDocked, 'has-widget-open': hasOpenWidget }">

        <!-- 故障树工作区（画布） -->
        <div class="panel col-right canvas-stage" id="section-canvas" ref="canvasStage" :class="{ 'is-canvas-fullscreen': isFullscreen, 'canvas-stage-light': themeMode === 'light', 'canvas-stage-dark': themeMode === 'dark' }">
          <div v-if="isFullscreen" class="fullscreen-toolbar-float">
            <div class="fullscreen-toolbar-panel" :class="themeMode === 'dark' ? 'fullscreen-toolbar-panel-dark' : 'fullscreen-toolbar-panel-light'">
              <div class="fullscreen-toolbar-title">节点工具栏</div>

              <div class="fullscreen-toolbar-section">
                <div class="fullscreen-toolbar-section-title">逻辑门</div>
                <div class="fullscreen-symbol-grid">
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="或门 (OR)" @dragstart="dragStart($event, 'gate', 'OR')">
                    <svg class="gate-svg" viewBox="-20 -25 40 50">
                      <path d="M -16 19 C -6 13 6 13 16 19 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z" :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.22)' : 'rgba(13,33,165,0.22)'" :stroke="themeMode === 'dark' ? '#a5b4fc' : '#4F7FFF'" stroke-width="2.2"/>
                    </svg>
                    <span>或门</span>
                  </div>
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="与门 (AND)" @dragstart="dragStart($event, 'gate', 'AND')">
                    <svg class="gate-svg" viewBox="-20 -25 40 50">
                      <path d="M 16 -8 C 11 -25 -11 -25 -16 -8 V 19 H 16 Z" :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.18)' : 'rgba(30,160,80,0.22)'" :stroke="themeMode === 'dark' ? '#67e8f9' : '#2ECC71'" stroke-width="2.2"/>
                    </svg>
                    <span>与门</span>
                  </div>
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="异或门 (XOR)" @dragstart="dragStart($event, 'gate', 'XOR')">
                    <svg class="gate-svg" viewBox="-20 -25 40 50">
                      <path d="M 16 20 Q 0 11 -16 20 L -16 19 C -5 13 6 13 16 19 M -16 15 C -6 9 6 9 16 15 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z" :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.20)' : 'rgba(230,120,0,0.22)'" :stroke="themeMode === 'dark' ? '#c4b5fd' : '#FF9500'" stroke-width="2.2"/>
                    </svg>
                    <span>异或</span>
                  </div>
                </div>
              </div>

              <div class="fullscreen-toolbar-section">
                <div class="fullscreen-toolbar-section-title">事件符号</div>
                <div class="fullscreen-symbol-grid">
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="顶事件" @dragstart="dragStart($event, 'event', 'top')">
                    <svg class="event-svg" viewBox="-25 -25 50 50">
                      <path d="M -20 -15 V 8 H 19 V -15 Z" :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.24)' : 'rgba(220,30,30,0.22)'" :stroke="themeMode === 'dark' ? '#a5b4fc' : '#FF3B30'" stroke-width="2.2"/>
                    </svg>
                    <span>顶事件</span>
                  </div>
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="中间事件" @dragstart="dragStart($event, 'event', 'intermediate')">
                    <svg class="event-svg" viewBox="-25 -25 50 50">
                      <path d="M -20 -15 V 8 H 19 V -15 Z" :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.14)' : 'rgba(13,33,165,0.20)'" :stroke="themeMode === 'dark' ? '#67e8f9' : '#4F7FFF'" stroke-width="2.2"/>
                    </svg>
                    <span>中间</span>
                  </div>
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="基本事件" @dragstart="dragStart($event, 'event', 'basic')">
                    <svg class="event-svg" viewBox="-25 -25 50 50">
                      <path d="M 20 0 A 1 1 0 0 0 -20 0 A 1 1 0 0 0 20 0 Z" :fill="themeMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(30,160,80,0.22)'" :stroke="themeMode === 'dark' ? 'rgba(255,255,255,0.24)' : '#2ECC71'" stroke-width="2.2"/>
                    </svg>
                    <span>基本</span>
                  </div>
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="未开展事件" @dragstart="dragStart($event, 'event', 'undeveloped')">
                    <svg class="event-svg" viewBox="0 0 60 50">
                      <polygon points="30,8 52,25 30,42 8,25" :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.18)' : 'rgba(160,40,210,0.20)'" :stroke="themeMode === 'dark' ? '#c4b5fd' : '#BF5FFF'" stroke-width="2.2"/>
                    </svg>
                    <span>未开展</span>
                  </div>
                  <div class="symbol-item fullscreen-symbol-item" draggable="true" title="初始事件" @dragstart="dragStart($event, 'event', 'initial')">
                    <svg class="event-svg" viewBox="0 0 60 50">
                      <path d="M10,40 L10,20 L30,5 L50,20 L50,40 Z" :fill="themeMode === 'dark' ? 'rgba(245,158,11,0.20)' : 'rgba(220,140,0,0.22)'" :stroke="themeMode === 'dark' ? '#fcd34d' : '#FF9F0A'" stroke-width="2.2"/>
                    </svg>
                    <span>初始</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="panel-content canvas-container" ref="canvasContainer">
            <div class="workspace-headline">
              <span class="monitor-dot"></span>
              <div class="history-controls">
                <button
                  class="layout-btn"
                  @click="undo"
                  :disabled="historyIndex <= 0"
                  title="撤销 (Ctrl+Z)"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16">
                    <path d="M4 8 L8 4 M4 8 L8 12 M4 8 L14 8" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
                  </svg>
                </button>
                <button
                  class="layout-btn"
                  @click="redo"
                  :disabled="historyIndex >= history.length - 1"
                  title="重做 (Ctrl+Y)"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16">
                    <path d="M12 8 L8 4 M12 8 L8 12 M12 8 L2 8" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
                  </svg>
                </button>
              </div>
              <div class="headline-divider"></div>
              <button
                :class="['layout-btn', { active: layoutDirection === 'horizontal' }]"
                @click="setLayoutDirection('horizontal')"
                title="从左往右布局"
              >
                <svg width="20" height="16" viewBox="0 0 20 16">
                  <line x1="2" y1="8" x2="8" y2="8" stroke="currentColor" stroke-width="2"/>
                  <line x1="8" y1="4" x2="8" y2="12" stroke="currentColor" stroke-width="2"/>
                  <line x1="8" y1="4" x2="18" y2="4" stroke="currentColor" stroke-width="2"/>
                  <line x1="8" y1="12" x2="18" y2="12" stroke="currentColor" stroke-width="2"/>
                  <circle cx="2" cy="8" r="2" fill="currentColor"/>
                  <circle cx="18" cy="4" r="2" fill="currentColor"/>
                  <circle cx="18" cy="12" r="2" fill="currentColor"/>
                </svg>
                <span>从左往右</span>
              </button>
              <button
                :class="['layout-btn', { active: layoutDirection === 'vertical' }]"
                @click="setLayoutDirection('vertical')"
                title="从上往下布局"
              >
                <svg width="16" height="20" viewBox="0 0 16 20">
                  <line x1="8" y1="2" x2="8" y2="8" stroke="currentColor" stroke-width="2"/>
                  <line x1="4" y1="8" x2="12" y2="8" stroke="currentColor" stroke-width="2"/>
                  <line x1="4" y1="8" x2="4" y2="18" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="8" x2="12" y2="18" stroke="currentColor" stroke-width="2"/>
                  <circle cx="8" cy="2" r="2" fill="currentColor"/>
                  <circle cx="4" cy="18" r="2" fill="currentColor"/>
                  <circle cx="12" cy="18" r="2" fill="currentColor"/>
                </svg>
                <span>从上往下</span>
              </button>
              <button
                class="layout-btn"
                @click="autoLayout"
                title="自动重新布局"
              >
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <span>自动布局</span>
              </button>
              <button
                class="layout-btn"
                @click="fitView"
                title="适应视图"
              >
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <rect x="2" y="2" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"/>
                  <circle cx="8" cy="8" r="2" fill="currentColor"/>
                </svg>
                <span>适应视图</span>
              </button>
              <div class="headline-divider"></div>
              <div class="zoom-controls">
                <button class="layout-btn" @click="zoomOut" title="缩小">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="3" y1="8" x2="13" y2="8"/>
                  </svg>
                </button>
                <span class="zoom-level">{{ Math.round(zoom * 100) }}%</span>
                <button class="layout-btn" @click="zoomIn" title="放大">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="8" y1="3" x2="8" y2="13"/>
                    <line x1="3" y1="8" x2="13" y2="8"/>
                  </svg>
                </button>
                <button class="layout-btn" @click="resetZoom" title="重置视图">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <path d="M3 8a5 5 0 1 0 5-5"/>
                    <polyline points="3 3 3 8 8 8"/>
                  </svg>
                </button>
              </div>
              <button class="layout-btn" @click="saveTreeImage" title="保存故障树图片">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M13 2H3a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1z"/>
                  <path d="M8 12V6M5 9l3-3 3 3"/>
                </svg>
                <span>保存</span>
              </button>
              <button class="layout-btn" @click="toggleWorkbenchFullscreen" :title="isFullscreen ? '退出全屏' : '网页全屏'">
                <svg v-if="!isFullscreen" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M6 2H2v4M10 2h4v4M14 10v4h-4M2 10v4h4"/>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M6 6H2V2M10 6h4V2M10 10h4v4M6 10H2v4"/>
                </svg>
                <span>{{ isFullscreen ? '退出全屏' : '全屏' }}</span>
              </button>
              <span class="workspace-tag"></span>
            </div>

            <!-- 右键菜单 -->
            <div v-if="contextMenu.show" class="context-menu" :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
              <div class="menu-item menu-item--danger" @click="deleteContextNode">
                <svg class="menu-icon" viewBox="0 0 16 16" fill="none"><polyline points="2,4 14,4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M5 4V2.5A.5.5 0 0 1 5.5 2h5a.5.5 0 0 1 .5.5V4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><rect x="3" y="4" width="10" height="9" rx="1.5" stroke="currentColor" stroke-width="1.4"/><line x1="6" y1="7" x2="6" y2="10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><line x1="10" y1="7" x2="10" y2="10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                删除节点
              </div>
              <div class="menu-item" @click="editNodeLabel" v-if="!contextMenu.isGate">
                <svg class="menu-icon" viewBox="0 0 16 16" fill="none"><path d="M11.5 2.5a1.414 1.414 0 0 1 2 2L5 13H3v-2L11.5 2.5z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>
                编辑标签
              </div>
              <div class="menu-item" @click="duplicateNode">
                <svg class="menu-icon" viewBox="0 0 16 16" fill="none"><rect x="5" y="5" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.4"/><path d="M3 11V3.5A1.5 1.5 0 0 1 4.5 2H11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                复制节点
              </div>
              <div class="menu-divider"></div>
              <div class="menu-item" @click="connectToParent">
                <svg class="menu-icon" viewBox="0 0 16 16" fill="none"><line x1="8" y1="13" x2="8" y2="3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><polyline points="4,7 8,3 12,7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
                连接到父节点
              </div>
              <div class="menu-item" @click="connectToChild">
                <svg class="menu-icon" viewBox="0 0 16 16" fill="none"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><polyline points="4,9 8,13 12,9" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
                连接到子节点
              </div>
            </div>

            <svg
              class="canvas"
              ref="canvas"
              @drop="handleDrop"
              @dragover.prevent
              @mousedown="startPan"
              @mousemove="handleMouseMove"
              @mouseup="endPan"
              @wheel.prevent="handleZoom"
              @click="hideContextMenu"
            >
              <!-- 网格定义 -->
              <defs>
                <linearGradient id="canvas-dark-bg" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#080914"/>
                  <stop offset="45%" stop-color="#121427"/>
                  <stop offset="100%" stop-color="#1a1330"/>
                </linearGradient>
                <pattern id="grid" :width="40 / zoom" :height="40 / zoom" patternUnits="userSpaceOnUse">
                  <line :x1="0" :y1="0" :x2="0" :y2="40 / zoom" :stroke="themeMode === 'dark' ? 'rgba(165, 180, 252, 0.18)' : 'rgba(13, 33, 165, 0.12)'" :stroke-width="1 / zoom"/>
                  <line :x1="0" :y1="0" :x2="40 / zoom" :y2="0" :stroke="themeMode === 'dark' ? 'rgba(165, 180, 252, 0.18)' : 'rgba(13, 33, 165, 0.12)'" :stroke-width="1 / zoom"/>
                </pattern>
                <pattern id="grid-fine" :width="8 / zoom" :height="8 / zoom" patternUnits="userSpaceOnUse">
                  <line :x1="0" :y1="0" :x2="0" :y2="8 / zoom" :stroke="themeMode === 'dark' ? 'rgba(34, 211, 238, 0.06)' : 'rgba(13, 33, 165, 0.06)'" :stroke-width="0.5 / zoom"/>
                  <line :x1="0" :y1="0" :x2="8 / zoom" :y2="0" :stroke="themeMode === 'dark' ? 'rgba(34, 211, 238, 0.06)' : 'rgba(13, 33, 165, 0.06)'" :stroke-width="0.5 / zoom"/>
                </pattern>
                <!-- 箭头标记 -->
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" :fill="themeMode === 'dark' ? 'rgba(165,180,252,0.92)' : 'rgba(4,2,3,0.70)'" />
                </marker>
                <marker id="arrowhead-reverse" markerWidth="10" markerHeight="7" refX="1" refY="3.5" orient="auto">
                  <polygon points="10 0, 0 3.5, 10 7" :fill="themeMode === 'dark' ? 'rgba(165,180,252,0.92)' : 'rgba(4,2,3,0.70)'" />
                </marker>
              </defs>

              <!-- 背景网格 -->
              <rect width="100%" height="100%" :fill="themeMode === 'dark' ? 'url(#canvas-dark-bg)' : 'rgba(240,244,253,0.5)'" />


              <!-- 画布内容 -->
              <g :transform="`translate(${panX}, ${panY}) scale(${zoom})`">
                <!-- virtual canvas background extends with pan/zoom -->
                <rect x="-50000" y="-50000" width="100000" height="100000" :fill="themeMode === 'dark' ? 'url(#canvas-dark-bg)' : 'rgba(240,244,253,0.3)'" />
                <rect x="-50000" y="-50000" width="100000" height="100000" fill="url(#grid)" />
                <rect x="-50000" y="-50000" width="100000" height="100000" fill="url(#grid-fine)" />
                <!-- 框选矩形 -->
                <rect
                  v-if="isBoxSelecting"
                  :x="boxSelectRect.x"
                  :y="boxSelectRect.y"
                  :width="boxSelectRect.width"
                  :height="boxSelectRect.height"
                  :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.16)' : 'rgba(255,255,0,0.15)'"
                  :stroke="themeMode === 'dark' ? '#a5b4fc' : '#040203'"
                  stroke-width="2"
                  stroke-dasharray="4,4"
                />

                <!-- 正在拖拽的连接线 -->
                <line
                  v-if="connectingFrom"
                  :x1="connectingFrom.x"
                  :y1="connectingFrom.y"
                  :x2="tempLineEnd.x"
                  :y2="tempLineEnd.y"
                  :stroke="themeMode === 'dark' ? '#22d3ee' : '#FF0000'"
                  stroke-width="2"
                  stroke-dasharray="5,5"
                />

                <!-- 连接线 - 改进后的绘制 -->
                <g class="edges">
                  <path
                    v-for="edge in pathEdges"
                    :key="'path-'+edge.id"
                    :d="edge.path"
                    fill="none"
                    :stroke="themeMode === 'dark' ? 'rgba(165,180,252,0.86)' : 'rgba(4,2,3,0.45)'" stroke-width="2"
                    :marker-end="edge.markerEnd ? 'url(#arrowhead)' : ''"
                    :marker-start="edge.markerStart ? 'url(#arrowhead-reverse)' : ''"
                  />
                </g>

                <!-- 节点 -->
                <g
                  v-for="node in nodes"
                  :key="node.id"
                  :transform="`translate(${node.x}, ${node.y})`"
                  class="node"
                  :class="{
                    selected: selectedNode && selectedNode.id === node.id,
                    'multi-selected': selectedNodes.includes(node)
                  }"
                  @mousedown.stop="startNodeDrag($event, node)"
                  @contextmenu.prevent="showContextMenu($event, node)"
                >
                  <!-- 多选时的外框 -->
                  <rect
                    v-if="selectedNodes.includes(node)"
                    :x="-55 * (node.scale || 1)"
                    :y="-40 * (node.scale || 1)"
                    :width="110 * (node.scale || 1)"
                    :height="80 * (node.scale || 1)"
                    rx="0"
                    fill="none"
                    :stroke="themeMode === 'dark' ? '#a5b4fc' : '#FF0000'"
                    stroke-width="2"
                    stroke-dasharray="4,3"
                    style="pointer-events: none;"
                  />

                  <!-- 连接点（左侧/上侧 - 输入） -->
                  <circle
                    v-if="layoutDirection === 'horizontal'"
                    :cx="-55 * (node.scale || 1)"
                    cy="0"
                    r="6"
                    :fill="themeMode === 'dark' ? '#a5b4fc' : '#FF0000'"
                    class="connection-point input"
                    @mousedown.stop="startConnect($event, node, 'input')"
                  />
                  <circle
                    v-else
                    cx="0"
                    :cy="-40 * (node.scale || 1)"
                    r="6"
                    :fill="themeMode === 'dark' ? '#a5b4fc' : '#FF0000'"
                    class="connection-point input"
                    @mousedown.stop="startConnect($event, node, 'input')"
                  />

                  <!-- 连接点（右侧/下侧 - 输出） -->
                  <circle
                    v-if="layoutDirection === 'horizontal'"
                    :cx="55 * (node.scale || 1)"
                    cy="0"
                    r="6"
                    :fill="themeMode === 'dark' ? '#22d3ee' : '#0000FF'"
                    class="connection-point output"
                    @mousedown.stop="startConnect($event, node, 'output')"
                  />
                  <circle
                    v-else
                    cx="0"
                    :cy="40 * (node.scale || 1)"
                    r="6"
                    :fill="themeMode === 'dark' ? '#22d3ee' : '#0000FF'"
                    class="connection-point output"
                    @mousedown.stop="startConnect($event, node, 'output')"
                  />

                  <!-- 顶事件：矩形 -->
                  <g v-if="node.shape === 'doubleoctagon'" :transform="`scale(${node.scale || 1})`">
                    <path
                      d="M -25 -20 V 15 H 24 V -20 Z"
                      :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.24)' : 'rgba(220,50,50,0.85)'"
                      :stroke="themeMode === 'dark' ? '#a5b4fc' : 'rgba(255,180,180,1)'"
                      stroke-width="1.5"
                    />
                  </g>

                  <!-- 或门 (OR Gate) -->
                  <g v-else-if="node.shape === 'gate' && node.gateType === 'OR'">
                    <g v-if="layoutDirection === 'horizontal'" transform="rotate(-90)">
                      <path
                        d="M -16 19 C -6 13 6 13 16 19 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z"
                        :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.22)' : 'rgba(30,100,255,0.80)'"
                        :stroke="themeMode === 'dark' ? '#a5b4fc' : 'rgba(160,210,255,1)'"
                        stroke-width="1.5"
                      />
                    </g>
                    <g v-else>
                      <path
                        d="M -16 19 C -6 13 6 13 16 19 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z"
                        :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.22)' : 'rgba(30,100,255,0.80)'"
                        :stroke="themeMode === 'dark' ? '#a5b4fc' : 'rgba(160,210,255,1)'"
                        stroke-width="1.5"
                      />
                    </g>
                  </g>

                  <!-- 与门 (AND Gate) -->
                  <g v-else-if="node.shape === 'gate' && node.gateType === 'AND'">
                    <g v-if="layoutDirection === 'horizontal'" transform="rotate(-90)">
                      <path
                        d="M 16 -8 C 11 -25 -11 -25 -16 -8 V 19 H 16 Z"
                        :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.18)' : 'rgba(30,180,80,0.82)'"
                        :stroke="themeMode === 'dark' ? '#67e8f9' : 'rgba(160,255,180,1)'"
                        stroke-width="1.5"
                      />
                    </g>
                    <g v-else>
                      <path
                        d="M 16 -8 C 11 -25 -11 -25 -16 -8 V 19 H 16 Z"
                        :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.18)' : 'rgba(30,180,80,0.82)'"
                        :stroke="themeMode === 'dark' ? '#67e8f9' : 'rgba(160,255,180,1)'"
                        stroke-width="1.5"
                      />
                    </g>
                  </g>

                  <!-- 异或门 (XOR Gate) -->
                  <g v-else-if="node.shape === 'gate' && node.gateType === 'XOR'">
                    <g v-if="layoutDirection === 'horizontal'" transform="rotate(-90)">
                      <path
                        d="M 16 20 Q 0 11 -16 20 L -16 19 C -5 13 6 13 16 19 M -16 15 C -6 9 6 9 16 15 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z"
                        :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.20)' : 'rgba(220,140,20,0.82)'"
                        :stroke="themeMode === 'dark' ? '#c4b5fd' : 'rgba(255,220,120,1)'"
                        stroke-width="1.5"
                      />
                    </g>
                    <g v-else>
                      <path
                        d="M 16 20 Q 0 11 -16 20 L -16 19 C -5 13 6 13 16 19 M -16 15 C -6 9 6 9 16 15 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z"
                        :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.20)' : 'rgba(220,140,20,0.82)'"
                        :stroke="themeMode === 'dark' ? '#c4b5fd' : 'rgba(255,220,120,1)'"
                        stroke-width="1.5"
                      />
                    </g>
                  </g>

                  <!-- 禁止门 (Inhibit Gate) -->
                  <g v-else-if="node.shape === 'gate' && node.gateType === 'INHIBIT'">
                    <g v-if="layoutDirection === 'horizontal'" transform="rotate(-90)">
                      <path
                        d="M 30 4 A 1 1 0 0 0 30 -4 M 14 0 L 8 0 M 8 5 L 8 -5 L 0 -11 L -8 -5 L -8 5 L 0 11 Z M 30 4 H 18 A 1 1 0 0 1 18 -4 h 12"
                        :fill="themeMode === 'dark' ? 'rgba(244,114,182,0.20)' : 'rgba(220,30,100,0.80)'"
                        :stroke="themeMode === 'dark' ? '#f9a8d4' : 'rgba(255,180,210,1)'"
                        stroke-width="2"
                      />
                    </g>
                    <g v-else>
                      <path
                        d="M 30 4 A 1 1 0 0 0 30 -4 M 14 0 L 8 0 M 8 5 L 8 -5 L 0 -11 L -8 -5 L -8 5 L 0 11 Z M 30 4 H 18 A 1 1 0 0 1 18 -4 h 12"
                        :fill="themeMode === 'dark' ? 'rgba(244,114,182,0.20)' : 'rgba(220,30,100,0.80)'"
                        :stroke="themeMode === 'dark' ? '#f9a8d4' : 'rgba(255,180,210,1)'"
                        stroke-width="2"
                      />
                    </g>
                  </g>

                  <!-- 优先与门 (Priority AND) -->
                  <g v-else-if="node.shape === 'gate' && node.gateType === 'PAND'">
                    <g v-if="layoutDirection === 'horizontal'">
                      <path
                        d="M-25,-20 L-25,15 Q0,25 25,15 L25,-20 Z"
                        :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.24)' : 'rgba(140,60,220,0.82)'"
                        :stroke="themeMode === 'dark' ? '#c4b5fd' : 'rgba(220,170,255,1)'"
                        stroke-width="2"
                      />
                      <text y="5" text-anchor="middle" font-size="12" fill="rgba(255,255,255,1)" font-weight="bold">&lt;</text>
                    </g>
                    <g v-else>
                      <path
                        d="M-20,-25 L-20,20 Q0,25 20,20 L20,-25 Z"
                        :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.24)' : 'rgba(140,60,220,0.82)'"
                        :stroke="themeMode === 'dark' ? '#c4b5fd' : 'rgba(220,170,255,1)'"
                        stroke-width="2"
                      />
                      <text y="5" text-anchor="middle" font-size="12" fill="rgba(255,255,255,1)" font-weight="bold">&lt;</text>
                    </g>
                  </g>

                  <!-- 中间事件：矩形 -->
                  <g v-else-if="node.shape === 'box'" :transform="`scale(${node.scale || 1})`">
                    <path
                      d="M -25 -20 V 15 H 24 V -20 Z"
                      :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.14)' : 'rgba(30,90,220,0.82)'"
                      :stroke="themeMode === 'dark' ? '#67e8f9' : 'rgba(160,210,255,1)'"
                      stroke-width="1.5"
                    />
                  </g>

                  <!-- 基本事件：圆形 -->
                  <g v-else-if="node.shape === 'basic'" :transform="`scale(${node.scale || 1})`">
                    <circle
                      cx="0"
                      cy="0"
                      r="22"
                      :fill="themeMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(30,160,70,0.82)'"
                      :stroke="themeMode === 'dark' ? 'rgba(255,255,255,0.22)' : 'rgba(160,255,180,1)'"
                      stroke-width="1.5"
                    />
                  </g>

                  <!-- 未开展事件：菱形 -->
                  <g v-else-if="node.shape === 'undeveloped'" :transform="`scale(${node.scale || 1})`">
                    <polygon
                      points="0,-25 25,0 0,25 -25,0"
                      :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.18)' : 'rgba(140,60,220,0.82)'"
                      :stroke="themeMode === 'dark' ? '#c4b5fd' : 'rgba(220,170,255,1)'"
                      stroke-width="1.5"
                    />
                  </g>

                  <!-- 初始事件：房子形 -->
                  <g v-else-if="node.shape === 'initial'" :transform="`scale(${node.scale || 1})`">
                    <path
                      d="M-25,20 L-25,0 L0,-20 L25,0 L25,20 Z"
                      :fill="themeMode === 'dark' ? 'rgba(245,158,11,0.20)' : 'rgba(210,140,20,0.85)'"
                      :stroke="themeMode === 'dark' ? '#fcd34d' : 'rgba(255,225,130,1)'"
                      stroke-width="1.5"
                    />
                  </g>

                  <!-- 条件事件：椭圆形 -->
                  <g v-else-if="node.shape === 'conditional'" :transform="`scale(${node.scale || 1})`">
                    <ellipse
                      cx="0"
                      cy="0"
                      rx="25"
                      ry="18"
                      :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.14)' : 'rgba(0,180,160,0.82)'"
                      :stroke="themeMode === 'dark' ? '#67e8f9' : 'rgba(120,240,220,1)'"
                      stroke-width="1.5"
                    />
                  </g>

                  <!-- 默认形状 -->
                  <g v-else :transform="`scale(${node.scale || 1})`">
                    <rect
                      x="-25"
                      y="-20"
                      width="50"
                      height="40"
                      rx="3"
                      :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.14)' : 'rgba(30,90,220,0.82)'"
                      :stroke="themeMode === 'dark' ? '#67e8f9' : 'rgba(160,210,255,1)'"
                      stroke-width="1.5"
                    />
                  </g>

                  <!-- 节点标签 - 支持多行 -->
                  <text
                    text-anchor="middle"
                    font-size="9"
                    fill="rgba(255,255,255,1)"
                    style="pointer-events: none;"
                  >
                    <tspan
                      v-for="(line, index) in getTextLines(node.label)"
                      :key="index"
                      x="0"
                      :dy="index === 0 ? -(getTextLines(node.label).length - 1) * 6 : 12"
                    >
                      {{ line }}
                    </tspan>
                  </text>
                </g>
              </g>
            </svg>
          </div>
        </div>

        <!-- 下拉式小组件面板 -->
        <div class="accordion-panels content-stage">
          <!-- AI 生产输入面板 -->
          <div
            id="section-ai"
            class="accordion-block card-block">
            <div class="accordion-toggle card-block-header always-open">
              <span class="accordion-toggle-main">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>AI 生产输入</span>
              </span>
              <svg class="accordion-arrow is-static" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6,9 12,15 18,9"/>
              </svg>
            </div>
              <div class="accordion-panel accordion-panel-open">
                <div class="panel-body card-block-body">
              <div class="ai-input-grid ai-input-grid-single">
                <div class="ai-input-group">
                  <label>系统名称</label>
                  <input v-model="aiSystem" class="ai-input" placeholder="输入系统名称..."/>
                </div>
                <div class="ai-input-group">
                  <label>顶事件</label>
                  <input v-model="aiTopEvent" class="ai-input" placeholder="输入顶事件..."/>
                </div>
              </div>
              <div class="ai-textarea-wrap">
                <label>原始文本</label>
                <textarea v-model="rawSourceText" class="ai-textarea" placeholder="粘贴原始文本，AI 自动抽取并生成故障树..."></textarea>
                <div class="ai-file-row">
                  <button class="ai-upload-btn" @click="$refs.aiFileInput.click()" title="上传文件（PDF、Word、TXT 等）">
                    <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M10 13V4M6 7l4-4 4 4"/>
                      <path d="M3 15h14v2H3z"/>
                    </svg>
                    上传文件
                  </button>
                  <span v-if="aiUploadedFileName" class="ai-uploaded-name">{{ aiUploadedFileName }}</span>
                  <input ref="aiFileInput" type="file" accept=".pdf,.doc,.docx,.txt,.md,.csv,.xls,.xlsx" style="display:none;" @change="handleAiFileUpload" />
                </div>
              </div>
              <label class="ai-checkbox">
                <input v-model="aiUseKnowledgeGraph" type="checkbox" />
                <span>写入知识图谱</span>
              </label>
              <div class="section-actions">
                <button class="primary" :disabled="aiBusy" @click="runAiExtraction">
                  <svg v-if="!aiBusy" viewBox="0 0 20 20" fill="none" width="16" height="16"><path d="M10 3v14M3 10h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                  <span class="ai-busy-dot" v-else></span>
                  {{ aiBusy ? '抽取中...' : '一键AI抽取' }}
                </button>
              </div>
              <div v-if="aiSuccessInfo" class="ai-success">{{ aiSuccessInfo }}</div>
              <div v-if="aiError" class="error">{{ aiError }}</div>
              <details v-if="workflowResultId" class="ai-debug-panel" open>
                <summary>审核、放行与建树</summary>
                <div class="ai-input-group">
                  <label>审核人</label>
                  <input v-model="reviewerName" class="ai-input" placeholder="请输入审核人姓名..." />
                </div>
                <div v-if="!reviewItems.length" class="ai-success">本次抽取没有可处理的故障记录。</div>
                <div v-for="item in reviewItems" :key="item.record.record_id" class="ai-input-group">
                  <label>
                    {{ item.record.description || item.record.fault_code || item.record.record_id }}
                    · {{ reviewStatusText(item.review && item.review.status) }}
                  </label>
                  <div>故障编号：{{ item.record.fault_code || '未提供' }}</div>
                  <div>组件：{{ item.record.component || '未提供' }}</div>
                  <div>原因：{{ item.record.causes && item.record.causes.length ? item.record.causes.join('、') : '未提供' }}</div>
                  <div v-if="item.evidenceSpans && item.evidenceSpans.length">
                    证据：<span v-for="evidence in item.evidenceSpans" :key="`${evidence.record_id}-${evidence.field}-${evidence.start}`">{{ evidence.quote }}</span>
                  </div>
                  <input
                    v-if="item.review && item.review.status === 'pending'"
                    v-model="reviewReasons[item.record.record_id]"
                    class="ai-input"
                    placeholder="拒绝或要求补充时填写原因；批准可选..."
                  />
                  <div v-if="item.review && item.review.status === 'pending'" class="action-row">
                    <button class="secondary small" :disabled="reviewBusyRecordId === item.record.record_id" @click="submitReviewDecision(item, 'approve')">批准</button>
                    <button class="secondary small" :disabled="reviewBusyRecordId === item.record.record_id" @click="submitReviewDecision(item, 'reject')">拒绝</button>
                    <button class="secondary small" :disabled="reviewBusyRecordId === item.record.record_id" @click="submitReviewDecision(item, 'revision')">要求补充</button>
                  </div>
                </div>
                <div v-if="workflowReleaseId" class="ai-success">已生成放行快照：{{ workflowReleaseId }}</div>
                <div v-if="workflowBlocked.length" class="error">
                  放行被拦截：{{ workflowBlocked.map(item => item.reason || item.status || item.record_id).join('；') }}
                </div>
                <div v-if="workflowError" class="error">{{ workflowError }}</div>
                <div class="section-actions">
                  <button
                    class="primary"
                    :disabled="releaseBusy || buildBusy || pendingReviewCount > 0 || !reviewItems.length"
                    @click="releaseAndBuild"
                  >
                    {{ releaseBusy || buildBusy ? '处理中...' : '放行并建树' }}
                  </button>
                </div>
              </details>
              <details v-if="aiItemsDebug && aiItemsDebug.length" class="ai-debug-panel">
                <summary>抽取结果</summary>
                <pre>{{ JSON.stringify(aiItemsDebug, null, 2) }}</pre>
              </details>
            </div>
          </div>
          </div>

          <div
            id="section-dot"
            class="accordion-block card-block">
            <div class="accordion-toggle card-block-header always-open">
              <span class="accordion-toggle-main">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8">
                  <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor"/>
                  <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-linecap="round"/>
                  <circle cx="17" cy="16" r="1.5" fill="currentColor"/>
                </svg>
                <span>DOT 控制台</span>
              </span>
              <svg class="accordion-arrow is-static" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6,9 12,15 18,9"/>
              </svg>
            </div>
            <div class="accordion-panel accordion-panel-open">
              <div class="panel-body card-block-body">
                <div class="dot-console-grid">
                  <div class="dot-console-pane">
                    <div class="dot-pane-title">DOT 输入区</div>
                    <textarea v-model="inputData" placeholder="输入DOT格式故障树数据..." class="dot-textarea"></textarea>
                    <div v-if="parseError" class="error">{{ parseError }}</div>
                    <div v-if="dotRenderInfo" class="ai-success">{{ dotRenderInfo }}</div>
                  </div>
                  <div class="dot-console-pane dot-console-meta-pane">
                    <div class="dot-pane-title">结构预览</div>
                    <div class="dot-insight-grid">
                      <div class="dot-insight-card">
                        <span>节点总数</span>
                        <strong>{{ nodes.length }}</strong>
                      </div>
                      <div class="dot-insight-card">
                        <span>连接总数</span>
                        <strong>{{ parsedData.edges.length }}</strong>
                      </div>
                      <div class="dot-insight-card">
                        <span>当前布局</span>
                        <strong>{{ layoutDirection === 'horizontal' ? '从左到右' : '从上到下' }}</strong>
                      </div>
                      <div class="dot-insight-card">
                        <span>缩放比例</span>
                        <strong>{{ Math.round(zoom * 100) }}%</strong>
                      </div>
                    </div>
                    <div class="dot-preview-tips">
                      <h4>使用建议</h4>
                      <ul>
                    <li>可输入原始故障描述文本，再点击“后端抽取并生成”，完成审核后才会进入画布。</li>
                        <li>如果画布已有内容，可先导出当前结构进行对照。</li>
                        <li>解析成功后可继续在画布中拖拽、调整、缩放并保存图片。</li>
                      </ul>
                    </div>
                  </div>
                </div>
              <div class="section-actions">
                <button @click="parseAndRenderViaBackend" class="primary" :disabled="dotSyncBusy">
                  {{ dotSyncBusy ? '后端抽取中...' : '后端抽取并生成' }}
                </button>
                <span class="dot-hint">后端流程会先保存抽取、证据和审核状态；仅前端解析仍可用于查看已有 DOT。</span>
                <div class="action-row">
                  <button @click="parseAndRender" class="secondary small">仅前端解析</button>
                  <button @click="loadExample" class="secondary small">加载示例</button>
                  <button @click="exportDot" class="secondary small">导出DOT</button>
                  <button @click="clearCanvas" class="danger small">清空</button>
                </div>
              </div>
            </div>
          </div>
          </div>

          <div
            id="section-toolbar"
            class="accordion-block card-block">
            <div class="accordion-toggle card-block-header always-open">
              <span class="accordion-toggle-main">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M10 3H3v7h7V3zM21 3h-7v7h7V3zM21 14h-7v7h7v-7zM10 14H3v7h7v-7z" stroke="currentColor"/>
                </svg>
                <span>节点工具栏</span>
              </span>
              <svg class="accordion-arrow is-static" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6,9 12,15 18,9"/>
              </svg>
            </div>
            <div class="accordion-panel accordion-panel-open">
              <div class="panel-body card-block-body">
              <div class="toolbar-grid">
                <div class="toolbar-group">
                  <h4>逻辑门</h4>
                  <div class="symbol-grid">
                    <div class="symbol-item" draggable="true" title="或门 (OR)" @dragstart="dragStart($event, 'gate', 'OR')">
                      <svg class="gate-svg" viewBox="-20 -25 40 50">
                        <path d="M -16 19 C -6 13 6 13 16 19 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z" :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.22)' : 'rgba(13,33,165,0.22)'" :stroke="themeMode === 'dark' ? '#a5b4fc' : '#4F7FFF'" stroke-width="2.2"/>
                      </svg>
                      <span>或门</span>
                    </div>
                    <div class="symbol-item" draggable="true" title="与门 (AND)" @dragstart="dragStart($event, 'gate', 'AND')">
                      <svg class="gate-svg" viewBox="-20 -25 40 50">
                        <path d="M 16 -8 C 11 -25 -11 -25 -16 -8 V 19 H 16 Z" :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.18)' : 'rgba(30,160,80,0.22)'" :stroke="themeMode === 'dark' ? '#67e8f9' : '#2ECC71'" stroke-width="2.2"/>
                      </svg>
                      <span>与门</span>
                    </div>
                    <div class="symbol-item" draggable="true" title="异或门 (XOR)" @dragstart="dragStart($event, 'gate', 'XOR')">
                      <svg class="gate-svg" viewBox="-20 -25 40 50">
                        <path d="M 16 20 Q 0 11 -16 20 L -16 19 C -5 13 6 13 16 19 M -16 15 C -6 9 6 9 16 15 V 0 Q 11 -17 0 -21 Q -11 -17 -16 0 Z" :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.20)' : 'rgba(230,120,0,0.22)'" :stroke="themeMode === 'dark' ? '#c4b5fd' : '#FF9500'" stroke-width="2.2"/>
                      </svg>
                      <span>异或</span>
                    </div>
                  </div>
                </div>
                <div class="toolbar-group">
                  <h4>事件符号</h4>
                  <div class="symbol-grid">
                    <div class="symbol-item" draggable="true" title="顶事件" @dragstart="dragStart($event, 'event', 'top')">
                      <svg class="event-svg" viewBox="-25 -25 50 50">
                        <path d="M -20 -15 V 8 H 19 V -15 Z" :fill="themeMode === 'dark' ? 'rgba(99,102,241,0.24)' : 'rgba(220,30,30,0.22)'" :stroke="themeMode === 'dark' ? '#a5b4fc' : '#FF3B30'" stroke-width="2.2"/>
                      </svg>
                      <span>顶事件</span>
                    </div>
                    <div class="symbol-item" draggable="true" title="中间事件" @dragstart="dragStart($event, 'event', 'intermediate')">
                      <svg class="event-svg" viewBox="-25 -25 50 50">
                        <path d="M -20 -15 V 8 H 19 V -15 Z" :fill="themeMode === 'dark' ? 'rgba(34,211,238,0.14)' : 'rgba(13,33,165,0.20)'" :stroke="themeMode === 'dark' ? '#67e8f9' : '#4F7FFF'" stroke-width="2.2"/>
                      </svg>
                      <span>中间</span>
                    </div>
                    <div class="symbol-item" draggable="true" title="基本事件" @dragstart="dragStart($event, 'event', 'basic')">
                      <svg class="event-svg" viewBox="-25 -25 50 50">
                        <path d="M 20 0 A 1 1 0 0 0 -20 0 A 1 1 0 0 0 20 0 Z" :fill="themeMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(30,160,80,0.22)'" :stroke="themeMode === 'dark' ? 'rgba(255,255,255,0.24)' : '#2ECC71'" stroke-width="2.2"/>
                      </svg>
                      <span>基本</span>
                    </div>
                    <div class="symbol-item" draggable="true" title="未开展事件" @dragstart="dragStart($event, 'event', 'undeveloped')">
                      <svg class="event-svg" viewBox="0 0 60 50">
                        <polygon points="30,8 52,25 30,42 8,25" :fill="themeMode === 'dark' ? 'rgba(139,92,246,0.18)' : 'rgba(160,40,210,0.20)'" :stroke="themeMode === 'dark' ? '#c4b5fd' : '#BF5FFF'" stroke-width="2.2"/>
                      </svg>
                      <span>未开展</span>
                    </div>
                    <div class="symbol-item" draggable="true" title="初始事件" @dragstart="dragStart($event, 'event', 'initial')">
                      <svg class="event-svg" viewBox="0 0 60 50">
                        <path d="M10,40 L10,20 L30,5 L50,20 L50,40 Z" :fill="themeMode === 'dark' ? 'rgba(245,158,11,0.20)' : 'rgba(220,140,0,0.22)'" :stroke="themeMode === 'dark' ? '#fcd34d' : '#FF9F0A'" stroke-width="2.2"/>
                      </svg>
                      <span>初始</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </div>

          <div
            id="section-props"
            class="accordion-block card-block">
            <div class="accordion-toggle card-block-header always-open">
              <span class="accordion-toggle-main">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor"/>
                  <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-linecap="round"/>
                </svg>
                <span>属性面板</span>
                <span v-if="selectedNodes.length > 0 || selectedNode" class="accordion-badge">{{ selectedNodes.length || 1 }}</span>
              </span>
              <svg class="accordion-arrow is-static" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6,9 12,15 18,9"/>
              </svg>
            </div>
            <div class="accordion-panel accordion-panel-open">
              <div class="panel-body card-block-body">
              <div class="props-overview-grid">
                <div class="props-overview-card">
                  <span>节点总数</span>
                  <strong>{{ nodes.length }}</strong>
                </div>
                <div class="props-overview-card">
                  <span>逻辑门</span>
                  <strong>{{ gateCount }}</strong>
                </div>
                <div class="props-overview-card">
                  <span>事件</span>
                  <strong>{{ basicEventCount }}</strong>
                </div>
                <div class="props-overview-card">
                  <span>连接</span>
                  <strong>{{ parsedData.edges.length }}</strong>
                </div>
              </div>
              <div class="fta-metrics-grid">
                <div class="fta-metric-card">
                  <span>根节点数</span>
                  <strong>{{ faultTreeMetrics.rootCount }}</strong>
                  <em>无父节点的起始事件/顶事件</em>
                </div>
                <div class="fta-metric-card">
                  <span>叶子节点数</span>
                  <strong>{{ faultTreeMetrics.leafCount }}</strong>
                  <em>无子节点的末端事件</em>
                </div>
                <div class="fta-metric-card">
                  <span>中间事件数</span>
                  <strong>{{ faultTreeMetrics.intermediateCount }}</strong>
                  <em>用于承接和分解故障逻辑</em>
                </div>
                <div class="fta-metric-card">
                  <span>重复事件数</span>
                  <strong>{{ faultTreeMetrics.repeatedEventCount }}</strong>
                  <em>被多个父节点复用的事件</em>
                </div>
                <div class="fta-metric-card">
                  <span>最大层级深度</span>
                  <strong>{{ faultTreeMetrics.maxDepth }}</strong>
                  <em>从根节点到叶子节点的最长层数</em>
                </div>
                <div class="fta-metric-card">
                  <span>平均分支系数</span>
                  <strong>{{ faultTreeMetrics.avgBranchFactor.toFixed(2) }}</strong>
                  <em>有子节点节点的平均分叉数</em>
                </div>
                <div class="fta-metric-card">
                  <span>最大扇出</span>
                  <strong>{{ faultTreeMetrics.maxFanOut }}</strong>
                  <em>单节点直接下游数量峰值</em>
                </div>
                <div class="fta-metric-card">
                  <span>最大扇入</span>
                  <strong>{{ faultTreeMetrics.maxFanIn }}</strong>
                  <em>单节点直接上游数量峰值</em>
                </div>
                <div class="fta-metric-card fta-metric-card-highlight">
                  <span>顶事件概率</span>
                  <strong>{{ faultTreeMetrics.topEventProbability !== null ? faultTreeMetrics.topEventProbability : '—' }}</strong>
                  <em>若 DOT 中显式给出 P= 值则展示</em>
                </div>
              </div>
              <div v-if="selectedNodes.length > 0" class="props-content">
                <p><strong>已选择:</strong> {{ selectedNodes.length }} 个节点</p>
                <div class="props-panel-note">可对多选节点执行批量删除与复制操作，适合整理局部故障树结构。</div>
                <div v-if="selectedNodes.length === 1" class="prop-details">
                  <div class="prop-row"><span class="prop-label">ID:</span><span class="prop-value">{{ selectedNodes[0].id }}</span></div>
                  <div class="prop-row"><span class="prop-label">标签:</span><span class="prop-value">{{ selectedNodes[0].label }}</span></div>
                  <div class="prop-row"><span class="prop-label">类型:</span><span class="prop-value">{{ getNodeTypeText(selectedNodes[0]) }}</span></div>
                  <div v-if="selectedNodes[0].probability" class="prop-row"><span class="prop-label">概率:</span><span class="prop-value">{{ selectedNodes[0].probability }}</span></div>
                </div>
                <div class="props-actions-row">
                  <button @click="deleteSelectedNodes" class="delete-btn">删除选中节点</button>
                  <button @click="copySelectedNodes" class="secondary small">复制节点</button>
                </div>
              </div>
              <div v-else-if="selectedNode" class="props-content">
                <div class="props-panel-note">当前为单节点详情，可查看节点类型、上下游关系和概率信息。</div>
                <div class="prop-details">
                  <div class="prop-row"><span class="prop-label">ID:</span><span class="prop-value">{{ selectedNode.id }}</span></div>
                  <div class="prop-row"><span class="prop-label">标签:</span><span class="prop-value">{{ selectedNode.label }}</span></div>
                  <div class="prop-row"><span class="prop-label">类型:</span><span class="prop-value">{{ getNodeTypeText(selectedNode) }}</span></div>
                  <div v-if="selectedNode.probability" class="prop-row"><span class="prop-label">概率:</span><span class="prop-value">{{ selectedNode.probability }}</span></div>
                  <div v-if="selectedNode.parent" class="prop-row"><span class="prop-label">父节点:</span><span class="prop-value">{{ selectedNode.parent }}</span></div>
                  <div v-if="selectedNode.children && selectedNode.children.length" class="prop-row">
                    <span class="prop-label">子节点:</span>
                    <span class="prop-value">{{ selectedNode.children.join(', ') }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="props-placeholder">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(13,33,165,0.2)" stroke-width="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/>
                </svg>
                <p>点击节点查看详情<br>Ctrl+拖拽 框选多个节点</p>
                <div class="props-placeholder-tips">
                  <span>支持查看节点上下游关系</span>
                  <span>支持多选后的批量操作</span>
                  <span>统计信息会随故障树结构实时变化</span>
                </div>
              </div>
              <div class="stats-mini">
                <div class="stat-badge">节点 {{ nodes.length }}</div>
                <div class="stat-badge">门 {{ gateCount }}</div>
                <div class="stat-badge">事件 {{ basicEventCount }}</div>
                <div class="stat-badge">连接 {{ parsedData.edges.length }}</div>
              </div>
            </div>
          </div>
          </div>

          <div
            id="section-history"
            class="accordion-block card-block">
            <div class="accordion-toggle card-block-header always-open">
              <span class="accordion-toggle-main">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8">
                  <circle cx="12" cy="12" r="9"/>
                  <polyline points="12,7 12,12 15,15"/>
                </svg>
                <span>历史记录</span>
              </span>
              <svg class="accordion-arrow is-static" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6,9 12,15 18,9"/>
              </svg>
            </div>
            <div class="accordion-panel accordion-panel-open">
              <div class="panel-body card-block-body">
              <div class="history-tabs">
                <button :class="['history-tab', historyTab==='tree' ? 'active' : '']" @click="historyTab='tree'">故障树</button>
                <button :class="['history-tab', historyTab==='chat' ? 'active' : '']" @click="historyTab='chat'">AI对话</button>
              </div>
              <div v-if="historyTab==='tree'" class="history-list">
                <div v-if="!faultTreeHistory.length" class="history-empty">暂无历史记录</div>
                <div v-for="item in faultTreeHistory" :key="item.id" class="history-item" @click="loadTreeHistory(item)">
                  <div class="history-item-title">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3h18v4H3zM3 10h12v4H3zM3 17h8v4H3z"/></svg>
                    <span>{{ item.title }}</span>
                  </div>
                  <div class="history-item-time">{{ item.time }}</div>
                </div>
              </div>
              <div v-if="historyTab==='chat'" class="history-list">
                <div v-if="!chatHistory.length" class="history-empty">暂无对话记录</div>
                <div v-for="item in chatHistory" :key="item.id" class="history-item">
                  <div class="history-item-title">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    <span class="history-item-q">{{ item.question }}</span>
                  </div>
                  <div class="history-item-answer">{{ item.answer }}</div>
                  <div class="history-item-time">{{ item.time }}</div>
                </div>
              </div>
              <button class="secondary small" style="width:100%;margin-top:8px;" @click="clearHistory">清空历史</button>
            </div>
          </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const EXAMPLE_FTA_DATA = `digraph FTA {
  rankdir=TB;
  graph [fontname=Helvetica];
  node [fontname=Helvetica];
  edge [fontname=Helvetica];
  top [label="Drone Crash", shape=doubleoctagon, style=filled, fillcolor=lightcoral];
  top_gate [label="OR", shape=diamond, width=0.5, height=0.5, fixedsize=true];
  top -> top_gate;
  e1 [label="Power System Failure\\nP=0.120", shape=box];
  top_gate -> e1;
  g2 [label="OR", shape=diamond, width=0.5, height=0.5, fixedsize=true];
  e1 -> g2;
  e3 [label="Motor Overheat\\nP=0.070", shape=ellipse];
  g2 -> e3;
  e4 [label="ESC Failure\\nP=0.030", shape=ellipse];
  g2 -> e4;
  e5 [label="Battery Issue\\nP=0.090", shape=box];
  top_gate -> e5;
  g6 [label="OR", shape=diamond, width=0.5, height=0.5, fixedsize=true];
  e5 -> g6;
  e7 [label="Voltage Drop\\nP=0.050", shape=ellipse];
  g6 -> e7;
  e8 [label="BMS Protection\\nP=0.030", shape=ellipse];
  g6 -> e8;
  e9 [label="Communication Loss\\nP=0.100", shape=box];
  top_gate -> e9;
  g10 [label="OR", shape=diamond, width=0.5, height=0.5, fixedsize=true];
  e9 -> g10;
  e11 [label="Signal Jamming\\nP=0.060", shape=ellipse];
  g10 -> e11;
  e12 [label="Video Module Error\\nP=0.020", shape=ellipse];
  g10 -> e12;
  e13 [label="Flight Control Loss\\nP=0.150", shape=box];
  top_gate -> e13;
  g14 [label="OR", shape=diamond, width=0.5, height=0.5, fixedsize=true];
  e13 -> g14;
  e15 [label="FC Software Crash\\nP=0.080", shape=ellipse];
  g14 -> e15;
  e16 [label="IMU Failure\\nP=0.040", shape=ellipse];
  g14 -> e16;
}`;

const CONFIGURED_API_BASE = (process.env.VUE_APP_API_BASE_URL || '').replace(/\/$/, '')

const API_BASE = (() => {
  try {
    const saved = localStorage.getItem('api_base_url')
    if (saved && /^https?:\/\//i.test(saved)) {
      return saved.replace(/\/$/, '')
    }
  } catch (e) {
    // Storage can be unavailable in restricted browser contexts.
  }
  return CONFIGURED_API_BASE
})()

export default {
  name: 'Workbench',
  emits: ['go-home'],
  data() {
    return {
      // AI 对话框新增状态 - 添加 docked 状态
      aiDialogMode: 'right', // 'bottom' | 'right' | 'hidden'
      aiDialogDocked: true,  // 新增：是否固定在右侧作为侧边栏（默认固定）
      aiDialogPosition: { x: 0, y: 0 },
      isDraggingAiDialog: false,
      aiDialogDragStart: { x: 0, y: 0, initialX: 0, initialY: 0 },
      hasDragged: false,
      dragThreshold: 5,
      // 新增：用于区分拖拽移动和展开收纳的标志
      aiDialogMovedThisSession: false,
      aiDialogWidth: 380, // 固定宽度
      // 保存每个模式下的位置
      aiDialogPositions: {
        'bottom': { x: 0, y: 0 },
        'right': { x: 0, y: 0 },
        'hidden': { x: 0, y: 0 }
      },

      // 原有数据保持不变
      aiDialogCollapsed: false,
      aiChatInput: '',
      aiChatBusy: false,
      aiChatMessages: [],
      quickActions: [
        { label: '分析关键路径', query: '请分析当前故障树的关键路径' },
        { label: '解释逻辑结构', query: '解释这个故障树的逻辑结构' },
        { label: '优化建议', query: '有什么优化这个故障树的建议？' },
        { label: '概率计算', query: '如何计算这个故障树的发生概率？' }
      ],
      // 新的导航栏状态
      navExpanded: false,
      themeMode: 'light',
      activeSection: null,
      isMobile: false,
      isFullscreen: false,
      navExpandTimeout: null,
      intersectionObserver: null,
      expandedSections: {
        ai: true,
        dot: true,
        toolbar: true,
        props: true,
        history: true
      },
      // 下拉式面板：当前激活的小组件（同一时间只打开一个）
      activeWidgetPanel: null,
      // 小组件排序和拖拽
      widgetOrder: ['ai', 'dot', 'toolbar', 'props', 'history'],
      defaultWidgetOrder: ['ai', 'dot', 'toolbar', 'props', 'history'],
      draggingWidget: null,
      dragOverWidget: null,
      widgetDragStartY: 0,
      widgetDragCurrentY: 0,
      isWidgetDragging: false,
      containerWidth: 0,
      containerHeight: 0,
      leftWidth: 400,
      topHeight: 300,
      toolbarWidth: 220,
      propHeight: 280,
      toolbarCollapsed: false,
      isToolbarResizing: false,
      isPropResizing: false,
      resizeStartToolbar: 0,
      resizeStartProp: 0,
      gridSize: 40,
      zoom: 1,
      panX: 50,
      panY: 50,
      isPanning: false,
      lastMouseX: 0,
      lastMouseY: 0,
      layoutDirection: 'horizontal',
      inputData: '',
      parseError: '',
      dotSyncBusy: false,
      dotRenderInfo: '',
      aiSystem: '',
      aiTopEvent: '',
      rawSourceText: '',
      aiUploadedFileName: '',
      aiUseKnowledgeGraph: false,
      aiBusy: false,
      aiError: '',
      aiSuccessInfo: '',
      aiItemsDebug: [],
      reviewerName: '',
      reviewItems: [],
      reviewReasons: {},
      reviewBusyRecordId: '',
      workflowResultId: '',
      workflowReleaseId: '',
      workflowBlocked: [],
      workflowBuildAttempt: null,
      workflowError: '',
      releaseBusy: false,
      buildBusy: false,
      nodes: [],
      edges: [],
      pathEdges: [],
      selectedNode: null,
      selectedNodes: [],
      parsedData: { nodes: {}, edges: [] },
      isVResizing: false,
      isHResizing: false,
      resizeStartX: 0,
      resizeStartY: 0,
      resizeStartLeft: 0,
      resizeStartTop: 0,
      isDraggingNode: false,
      draggedNode: null,
      dragOffsetX: 0,
      dragOffsetY: 0,
      isMultiDragging: false,
      isBoxSelecting: false,
      boxSelectStart: { x: 0, y: 0 },
      boxSelectRect: { x: 0, y: 0, width: 0, height: 0 },
      connectingFrom: null,
      connectingType: null,
      tempLineEnd: { x: 0, y: 0 },
      contextMenu: { show: false, x: 0, y: 0, node: null, isGate: false },
      clipboard: [],
      history: [],
      historyIndex: -1,
      faultTreeHistory: [],
      chatHistory: [],
      historyTab: 'tree',
      maxHistoryLength: 20,
      isRestoring: false,
      // 拖拽优化相关
      rafId: null,
      pendingMouseEvent: null
    }
  },

  computed: {
    gateCount() {
      return this.nodes.filter(n => n.type === 'gate').length
    },
    basicEventCount() {
      return this.nodes.filter(n => n.type === 'basic').length
    },
    faultTreeMetrics() {
      const nodes = Object.values(this.parsedData?.nodes || {})
      const edges = this.parsedData?.edges || []

      if (!nodes.length) {
        return {
          rootCount: 0,
          leafCount: 0,
          intermediateCount: 0,
          repeatedEventCount: 0,
          maxDepth: 0,
          avgBranchFactor: 0,
          maxFanOut: 0,
          maxFanIn: 0,
          topEventProbability: null
        }
      }

      const rootNodes = nodes.filter(node => !Array.isArray(node.parents) || node.parents.length === 0)
      const leafNodes = nodes.filter(node => !Array.isArray(node.children) || node.children.length === 0)
      const intermediateNodes = nodes.filter(node => node.type === 'intermediate')
      const repeatedEventNodes = nodes.filter(node => Array.isArray(node.parents) && node.parents.length > 1)

      const calcDepth = (nodeId, visited = new Set()) => {
        if (visited.has(nodeId)) return 0
        visited.add(nodeId)
        const node = this.parsedData.nodes[nodeId]
        if (!node || !Array.isArray(node.children) || node.children.length === 0) {
          visited.delete(nodeId)
          return 1
        }

        let maxChildDepth = 0
        node.children.forEach(childId => {
          maxChildDepth = Math.max(maxChildDepth, calcDepth(childId, visited))
        })
        visited.delete(nodeId)
        return maxChildDepth + 1
      }

      const maxDepth = rootNodes.length
        ? Math.max(...rootNodes.map(node => calcDepth(node.id)))
        : Math.max(...nodes.map(node => calcDepth(node.id)))

      const nonLeafNodes = nodes.filter(node => Array.isArray(node.children) && node.children.length > 0)
      const totalChildren = nonLeafNodes.reduce((sum, node) => sum + node.children.length, 0)
      const avgBranchFactor = nonLeafNodes.length ? totalChildren / nonLeafNodes.length : 0
      const maxFanOut = nonLeafNodes.length ? Math.max(...nonLeafNodes.map(node => node.children.length)) : 0
      const maxFanIn = nodes.length
        ? Math.max(...nodes.map(node => Array.isArray(node.parents) ? node.parents.length : 0))
        : 0

      const topNode = nodes.find(node => node.type === 'top')
      const topEventProbability = topNode && typeof topNode.probability === 'number'
        ? topNode.probability
        : null

      return {
        rootCount: rootNodes.length,
        leafCount: leafNodes.length,
        intermediateCount: intermediateNodes.length,
        repeatedEventCount: repeatedEventNodes.length,
        maxDepth,
        avgBranchFactor,
        maxFanOut,
        maxFanIn,
        topEventProbability
      }
    },
    // 获取排序后的小组件列表
    orderedWidgets() {
      return this.widgetOrder.map(id => ({
        id,
        name: this.getWidgetName(id),
        icon: this.getWidgetIcon(id)
      }))
    },
    // 是否有打开的小组件面板
    hasOpenWidget() {
      return this.activeWidgetPanel !== null
    },
    pendingReviewCount() {
      return this.reviewItems.filter(item => item.review && item.review.status === 'pending').length
    }
  },

  watch: {
    aiDialogDocked(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.$nextTick(() => {
          this.updateContainerSize()
          const delay = newVal ? 400 : 150
          setTimeout(() => {
            if (this.$refs && this.$refs.canvas) {
              this.fitView()
            }
          }, delay)
        })
      }
    }
  },

    mounted() {
    this.updateContainerSize()
    this.checkMobile()
    this.activeSection = 'toolbar'
    this.loadThemeMode()
    window.addEventListener('resize', this.handleResize)
    window.addEventListener('mousemove', this.handleGlobalMouseMove)
    window.addEventListener('mouseup', this.handleGlobalMouseUp)
    window.addEventListener('keydown', this.handleKeyDown)
    document.addEventListener('fullscreenchange', this.handleFullscreenChange)
    this.isFullscreen = !!document.fullscreenElement
    this.$nextTick(() => {
      this.parseAndRender()
      this.saveHistory()
      this.initIntersectionObserver()
    })
  },

  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    window.removeEventListener('mousemove', this.handleGlobalMouseMove)
    window.removeEventListener('mouseup', this.handleGlobalMouseUp)
    window.removeEventListener('keydown', this.handleKeyDown)
    document.removeEventListener('fullscreenchange', this.handleFullscreenChange)
    if (this.rafId) {
      cancelAnimationFrame(this.rafId)
    }
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect()
    }
    if (this.navExpandTimeout) {
      clearTimeout(this.navExpandTimeout)
    }
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
  },

  methods: {
    // ===== 小组件拖拽排序功能 =====

    // 获取小组件名称
    getWidgetName(id) {
      const names = {
        ai: 'AI 生产输入',
        dot: 'DOT 控制台',
        toolbar: '节点工具栏',
        props: '属性面板',
        history: '历史记录'
      }
      return names[id] || id
    },

    loadThemeMode() {
      try {
        const savedTheme = localStorage.getItem('workbench-theme-mode')
        if (savedTheme === 'dark' || savedTheme === 'light') {
          this.themeMode = savedTheme
        }
      } catch (e) {
        this.themeMode = 'light'
      }
    },

    toggleThemeMode() {
      this.themeMode = this.themeMode === 'light' ? 'dark' : 'light'
      try {
        localStorage.setItem('workbench-theme-mode', this.themeMode)
      } catch (e) {
        // ignore storage failure
      }
    },

    // 获取小组件图标
    getWidgetIcon(id) {
      const icons = {
        ai: 'lightning',
        dot: 'console',
        toolbar: 'grid',
        props: 'file',
        history: 'clock'
      }
      return icons[id] || 'box'
    },

    // 开始拖拽小组件
    startWidgetDrag(e, widgetId) {
      // 只允许左键拖拽
      if (e.button !== 0) return

      this.draggingWidget = widgetId
      this.isWidgetDragging = true
      this.widgetDragStartY = e.clientY

      // 添加拖拽时的视觉反馈
      const el = document.getElementById(`section-${widgetId}`)
      if (el) {
        el.classList.add('dragging')
      }

      // 阻止默认行为
      e.preventDefault()
      e.stopPropagation()

      // 添加全局事件监听
      document.addEventListener('mousemove', this.handleWidgetDragMove)
      document.addEventListener('mouseup', this.handleWidgetDragEnd)
      document.body.style.cursor = 'grabbing'
      document.body.style.userSelect = 'none'
    },

    // 拖拽移动中
    handleWidgetDragMove(e) {
      if (!this.isWidgetDragging || !this.draggingWidget) return

      this.widgetDragCurrentY = e.clientY

      // 检测拖拽经过的小组件
      const widgetElements = this.widgetOrder.map(id => ({
        id,
        el: document.getElementById(`section-${id}`)
      })).filter(item => item.el && item.id !== this.draggingWidget)

      // 找到最近的元素
      let closestWidget = null
      let closestDistance = Infinity

      widgetElements.forEach(({ id, el }) => {
        const rect = el.getBoundingClientRect()
        const centerY = rect.top + rect.height / 2
        const distance = Math.abs(e.clientY - centerY)

        if (distance < closestDistance) {
          closestDistance = distance
          closestWidget = id
        }
      })

      // 如果找到目标且距离足够近，准备交换位置
      if (closestWidget && closestDistance < 100) {
        this.dragOverWidget = closestWidget

        // 添加视觉反馈
        widgetElements.forEach(({ id, el }) => {
          if (id === closestWidget) {
            el.classList.add('drag-over')
          } else {
            el.classList.remove('drag-over')
          }
        })
      }
    },

    // 结束拖拽
    handleWidgetDragEnd(e) {
      if (!this.isWidgetDragging) return

      // 如果有目标小组件，交换位置
      if (this.dragOverWidget && this.dragOverWidget !== this.draggingWidget) {
        this.swapWidgets(this.draggingWidget, this.dragOverWidget)
      }

      // 清理视觉反馈
      this.widgetOrder.forEach(id => {
        const el = document.getElementById(`section-${id}`)
        if (el) {
          el.classList.remove('dragging', 'drag-over')
        }
      })

      // 清理状态
      this.draggingWidget = null
      this.dragOverWidget = null
      this.isWidgetDragging = false

      // 移除全局事件监听
      document.removeEventListener('mousemove', this.handleWidgetDragMove)
      document.removeEventListener('mouseup', this.handleWidgetDragEnd)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    },

    // 交换小组件位置
    swapWidgets(fromId, toId) {
      const fromIndex = this.widgetOrder.indexOf(fromId)
      const toIndex = this.widgetOrder.indexOf(toId)

      if (fromIndex === -1 || toIndex === -1) return

      // 创建新数组并交换位置
      const newOrder = [...this.widgetOrder]
      newOrder.splice(fromIndex, 1)
      newOrder.splice(toIndex, 0, fromId)

      this.widgetOrder = newOrder

      // 保存到 localStorage
      this.saveWidgetLayout()

      // 显示提示
      this.showToast('布局已更新', 'success')
    },

    // 保存小组件布局
    saveWidgetLayout() {
      return
    },

    // 加载小组件布局
    loadWidgetLayout() {
      this.activeWidgetPanel = null
    },

    // 重置小组件布局
    resetWidgetLayout() {
      this.widgetOrder = [...this.defaultWidgetOrder]
      this.expandedSections = {
        ai: true,
        dot: true,
        toolbar: true,
        props: true,
        history: true
      }
    },

    // 滚动容器解析
    getScrollContainer() {
      const mainContent = this.$el?.querySelector('.main-content')
      if (mainContent && mainContent.scrollHeight > mainContent.clientHeight + 4) {
        return mainContent
      }
      return window
    },

    scrollContainerTo(scrollRoot, top) {
      if (scrollRoot === window) {
        window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
        return
      }
      scrollRoot.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
    },

    // 滚动到指定区块 - 优化版带偏移量
    scrollToSection(sectionId) {
      this.activeSection = sectionId
      const scrollRoot = this.getScrollContainer()
      const rootTop = scrollRoot === window ? 0 : scrollRoot.getBoundingClientRect().top
      const offset = this.isMobile ? 104 : 96

      const element = document.getElementById(`section-${sectionId}`)
      if (element) {
        const top = element.getBoundingClientRect().top - rootTop + (scrollRoot === window ? window.pageYOffset : scrollRoot.scrollTop) - offset
        this.scrollContainerTo(scrollRoot, top)
        element.classList.add('highlight-section')
        setTimeout(() => {
          element.classList.remove('highlight-section')
        }, 2000)
      }
    },

    // 导航栏悬停处理
    handleNavEnter() {
      if (this.isMobile) return
      if (this.navExpandTimeout) {
        clearTimeout(this.navExpandTimeout)
        this.navExpandTimeout = null
      }
      this.navExpanded = true
    },

    handleNavLeave() {
      if (this.isMobile) return
      this.navExpandTimeout = setTimeout(() => {
        this.navExpanded = false
      }, 150)
    },

    // 检测移动端
    checkMobile() {
      this.isMobile = window.innerWidth <= 992
      this.navExpanded = !this.isMobile
    },

    // 窗口大小改变处理
    handleResize() {
      this.updateContainerSize()
      this.checkMobile()
    },

    async toggleWorkbenchFullscreen() {
      const target = this.$refs.canvasStage
      if (!target) return

      try {
        if (document.fullscreenElement === target) {
          await document.exitFullscreen()
          return
        }

        if (document.fullscreenElement) {
          await document.exitFullscreen()
        }

        await target.requestFullscreen()
      } catch (error) {
        console.error('切换故障树全屏失败:', error)
        this.showToast('全屏切换失败，请重试', 'warn')
      }
    },

    handleFullscreenChange() {
      const target = this.$refs.canvasStage
      this.isFullscreen = !!target && document.fullscreenElement === target

      this.$nextTick(() => {
        this.updateContainerSize()
        setTimeout(() => {
          if (this.$refs.canvas) {
            this.fitView()
          }
        }, 80)
      })
    },

    // 初始化 Intersection Observer 监测区块可见性
    initIntersectionObserver() {
      const options = {
        root: null,
        rootMargin: '-100px 0px -60% 0px',
        threshold: [0, 0.1, 0.25, 0.5]
      }

      this.intersectionObserver = new IntersectionObserver((entries) => {
        let maxVisibleSection = null
        let maxRatio = 0

        entries.forEach(entry => {
          if (entry.isIntersecting && entry.intersectionRatio > maxRatio) {
            const sectionId = entry.target.id.replace('section-', '')
            maxRatio = entry.intersectionRatio
            maxVisibleSection = sectionId
          }
        })

        // 如果没有区块高亮，检查画布区域
        if (!maxVisibleSection) {
          const canvasContainer = this.$refs.canvasContainer
          if (canvasContainer) {
            const canvasRect = canvasContainer.getBoundingClientRect()
            const canvasVisible = canvasRect.top < window.innerHeight * 0.6 && canvasRect.bottom > 100
            if (canvasVisible) {
              maxVisibleSection = 'canvas'
            }
          }
        }

        if (maxVisibleSection && maxRatio > 0.1) {
          this.activeSection = maxVisibleSection
        }
      }, options)

      // 监测所有区块
      this.$nextTick(() => {
        const sections = ['ai', 'dot', 'toolbar', 'props', 'history']
        sections.forEach(id => {
          const element = document.getElementById(`section-${id}`)
          if (element) {
            this.intersectionObserver.observe(element)
          }
        })
        // 也监测小组件整体区域
        const widgetsSection = document.getElementById('section-widgets')
        if (widgetsSection) {
          this.intersectionObserver.observe(widgetsSection)
        }
      })
    },

    // 切换区块展开/收起 - 保留兼容，当前为全部常开大卡片
    toggleSection(sectionId) {
      this.activeSection = sectionId
    },

    // 关闭当前面板
    closeWidgetPanel() {
      return
    },

    // AI 对话框样式计算
    getAiDialogStyle() {
      if (this.aiDialogDocked) {
        return {}
      }

      if (this.aiDialogMode === 'hidden') {
        return {
          transform: 'none',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          willChange: 'auto'
        }
      }

      if (this.aiDialogMode === 'right') {
        if (this.isDraggingAiDialog) {
          const screenWidth = window.innerWidth
          const dialogWidth = this.aiDialogWidth
          const baseLeft = screenWidth - 20 - dialogWidth
          const baseTop = 52

          return {
            position: 'fixed',
            left: `${baseLeft + this.aiDialogPosition.x}px`,
            top: `${baseTop + this.aiDialogPosition.y}px`,
            right: 'auto',
            bottom: 'auto',
            transform: 'none',
            transition: 'none',
            cursor: 'grabbing',
            willChange: 'left, top',
            zIndex: 1002,
            width: `${dialogWidth}px`,
            height: `calc(100vh - 72px)`
          }
        }

        return {
          position: 'fixed',
          right: '20px',
          left: 'auto',
          top: '52px',
          bottom: 'auto',
          transform: `translate3d(${-this.aiDialogPosition.x}px, ${this.aiDialogPosition.y}px, 0)`,
          transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          willChange: 'transform',
          width: `${this.aiDialogWidth}px`,
          height: `calc(100vh - 72px)`,
          zIndex: 1001
        }
      }

      return {
        position: 'fixed',
        left: '50%',
        right: 'auto',
        top: 'auto',
        bottom: '20px',
        transform: `translate3d(calc(-50% + ${this.aiDialogPosition.x}px), ${this.aiDialogPosition.y}px, 0)`,
        transition: this.isDraggingAiDialog ? 'none' : 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: this.isDraggingAiDialog ? 'grabbing' : 'grab',
        willChange: 'transform',
        zIndex: 1001
      }
    },

    startDragAiDialog(e) {
      const target = e.target
      // 排除按钮、控制区、输入框和文本域，这些元素需要正常交互
      if (target.closest('button') || target.closest('.ai-dialog-controls') || target.closest('input') || target.closest('textarea') || target.closest('.ai-input-area')) {
        return
      }

      if (this.aiDialogMode === 'hidden') return
      if (this.isDraggingAiDialog) return

      this.isDraggingAiDialog = true
      this.hasDragged = false

      this.aiDialogDragStart = {
        x: e.clientX,
        y: e.clientY,
        initialX: this.aiDialogPosition.x,
        initialY: this.aiDialogPosition.y
      }

      e.preventDefault()
      e.stopPropagation()
      document.body.style.userSelect = 'none'
      document.body.style.cursor = 'grabbing'
    },

    handleAiDialogClick() {
      if (this.hasDragged && this.aiDialogMovedThisSession) return

      if (this.aiDialogMode === 'hidden') {
        this.aiDialogMode = 'right'
        this.aiDialogCollapsed = false
        this.aiDialogPosition = { x: 0, y: 0 }
        this.$nextTick(() => {
          this.$refs.aiInput?.focus()
          this.scrollAiDialogToBottom()
        })
      }
    },

    toggleAiDialog() {
      if (this.hasDragged && this.aiDialogMovedThisSession) return

      if (this.aiDialogDocked) {
        this.aiDialogCollapsed = !this.aiDialogCollapsed
        this.$nextTick(() => {
          this.updateContainerSize()
          if (!this.aiDialogCollapsed) {
            this.$refs.aiInput?.focus()
          }
          setTimeout(() => {
            if (this.$refs && this.$refs.canvas) {
              this.fitView()
            }
          }, 350)
        })
        return
      }

      if (this.aiDialogMode === 'hidden') {
        this.aiDialogMode = 'right'
        this.aiDialogCollapsed = false
        this.aiDialogPosition = { x: 0, y: 0 }
        this.$nextTick(() => {
          this.scrollAiDialogToBottom()
          this.$refs.aiInput?.focus()
        })
        return
      }

      this.aiDialogCollapsed = !this.aiDialogCollapsed
      if (!this.aiDialogCollapsed) {
        this.$nextTick(() => {
          this.scrollAiDialogToBottom()
          this.$refs.aiInput?.focus()
        })
      }
    },

    cycleAiDialogMode() {
      if (this.aiDialogDocked) {
        this.aiDialogDocked = false
        this.aiDialogMode = 'right'
        this.aiDialogCollapsed = false
        this.aiDialogPosition = { ...this.aiDialogPositions['right'] }
        this.showToast('已切换到悬浮模式', 'info')
        return
      }

      this.aiDialogPositions[this.aiDialogMode] = { ...this.aiDialogPosition }

      const modes = ['bottom', 'right', 'hidden']
      const currentIndex = modes.indexOf(this.aiDialogMode)
      const nextMode = modes[(currentIndex + 1) % modes.length]

      this.aiDialogMode = nextMode

      if (nextMode === 'hidden') {
        this.aiDialogCollapsed = true
        this.aiDialogPosition = { ...this.aiDialogPositions['hidden'] }
      } else if (nextMode === 'right') {
        this.aiDialogCollapsed = false
        this.aiDialogPosition = { ...this.aiDialogPositions['right'] }
      } else {
        this.aiDialogCollapsed = false
        this.aiDialogPosition = { ...this.aiDialogPositions['bottom'] }
      }
    },

    undockAiDialog() {
      this.aiDialogDocked = false
      this.aiDialogMode = 'right'
      this.aiDialogCollapsed = false
      this.aiDialogPosition = { ...this.aiDialogPositions['right'] }
      this.showToast('已切换到悬浮模式', 'info')
    },

    // 全局鼠标事件处理
    handleGlobalMouseMove(e) {
      if (this.isDraggingAiDialog) {
        if (!this.rafId) {
          this.pendingMouseEvent = e
          this.rafId = requestAnimationFrame(() => {
            this.processAiDialogDrag(this.pendingMouseEvent)
            this.rafId = null
          })
        } else {
          this.pendingMouseEvent = e
        }
        return
      }

      if (this.isDraggingNode && this.draggedNode) {
        if (this.isBoxSelecting) this.isBoxSelecting = false

        if (this.isMultiDragging) {
          const rect = this.$refs.canvas.getBoundingClientRect()
          const mouseX = (e.clientX - rect.left - this.panX) / this.zoom
          const mouseY = (e.clientY - rect.top - this.panY) / this.zoom

          const deltaX = mouseX - this.dragOffsetX - this.draggedNode._initialX
          const deltaY = mouseY - this.dragOffsetY - this.draggedNode._initialY

          const snappedDeltaX = Math.round(deltaX / this.gridSize) * this.gridSize
          const snappedDeltaY = Math.round(deltaY / this.gridSize) * this.gridSize

          this.selectedNodes.forEach(node => {
            node.x = node._initialX + snappedDeltaX
            node.y = node._initialY + snappedDeltaY

            if (this.parsedData.nodes[node.id]) {
              this.parsedData.nodes[node.id].x = node.x
              this.parsedData.nodes[node.id].y = node.y
            }
          })

          this.updateEdges()
          return
        }

        if (!this.isMultiDragging) {
          const rect = this.$refs.canvas.getBoundingClientRect()
          const mouseX = (e.clientX - rect.left - this.panX) / this.zoom
          const mouseY = (e.clientY - rect.top - this.panY) / this.zoom

          let newX = mouseX - this.dragOffsetX
          let newY = mouseY - this.dragOffsetY

          newX = Math.round(newX / this.gridSize) * this.gridSize
          newY = Math.round(newY / this.gridSize) * this.gridSize

          const dx = newX - this.draggedNode.x
          const dy = newY - this.draggedNode.y

          this.draggedNode.x = newX
          this.draggedNode.y = newY
          if (this.parsedData.nodes[this.draggedNode.id]) {
            this.parsedData.nodes[this.draggedNode.id].x = newX
            this.parsedData.nodes[this.draggedNode.id].y = newY
          }

          const descendants = this.getDescendants(this.draggedNode.id)
          descendants.forEach(id => {
            const n = this.parsedData.nodes[id]
            if (n) {
              n.x = Math.round((n.x + dx) / this.gridSize) * this.gridSize
              n.y = Math.round((n.y + dy) / this.gridSize) * this.gridSize
            }
          })

          this.updateEdges()
          return
        }
      }

      if (this.isBoxSelecting && !this.isDraggingNode) {
        this.updateBoxSelect(e)
        return
      }

      if (this.connectingFrom) {
        const rect = this.$refs.canvas.getBoundingClientRect()
        this.tempLineEnd = {
          x: (e.clientX - rect.left - this.panX) / this.zoom,
          y: (e.clientY - rect.top - this.panY) / this.zoom
        }
      }

      if (this.isPanning) {
        this.panX += e.clientX - this.lastMouseX
        this.panY += e.clientY - this.lastMouseY
        this.lastMouseX = e.clientX
        this.lastMouseY = e.clientY
      }
    },

    processAiDialogDrag(e) {
      const dx = e.clientX - this.aiDialogDragStart.x
      const dy = e.clientY - this.aiDialogDragStart.y

      if (Math.abs(dx) > this.dragThreshold || Math.abs(dy) > this.dragThreshold) {
        this.hasDragged = true
        this.aiDialogMovedThisSession = true
      }

      let newX = this.aiDialogDragStart.initialX + dx
      let newY = this.aiDialogDragStart.initialY + dy

      const screenWidth = window.innerWidth
      const screenHeight = window.innerHeight
      const dialogWidth = this.aiDialogWidth

      if (this.aiDialogMode === 'right') {
        const baseLeft = screenWidth - 20 - dialogWidth
        const minVisible = 100

        const minX = -(baseLeft - minVisible)
        const maxX = minVisible

        newX = Math.max(minX, Math.min(maxX, newX))
        newY = Math.max(-40, Math.min(screenHeight - 100, newY))
      } else if (this.aiDialogMode === 'bottom') {
        const maxOffsetX = screenWidth * 0.4
        newX = Math.max(-maxOffsetX, Math.min(maxOffsetX, newX))
        newY = Math.max(-(screenHeight - 400), Math.min(0, newY))
      }

      this.aiDialogPosition.x = newX
      this.aiDialogPosition.y = newY
    },

    handleGlobalMouseUp(e) {
      let dockedThisTime = false

      if (this.rafId) {
        cancelAnimationFrame(this.rafId)
        this.rafId = null
      }

      try {
        if (this.isDraggingAiDialog && !this.aiDialogDocked) {
          document.body.style.userSelect = ''
          document.body.style.cursor = ''

          if (this.hasDragged) {
            const screenWidth = window.innerWidth
            const screenHeight = window.innerHeight
            const dialogWidth = this.aiDialogWidth
            const dialogHeight = 400

            if (this.aiDialogMode === 'right') {
              const baseLeft = screenWidth - 20 - dialogWidth
              const currentLeft = baseLeft + this.aiDialogPosition.x
              const currentTop = 52 + this.aiDialogPosition.y

              const distanceToRightEdge = screenWidth - (currentLeft + dialogWidth)

              if (distanceToRightEdge < 50 && !this.aiDialogCollapsed) {
                this.aiDialogDocked = true
                this.aiDialogPosition = { x: 0, y: 0 }
                dockedThisTime = true
                this.showToast('AI助手已固定到右侧', 'success')

                this.$nextTick(() => {
                  this.updateContainerSize()
                  setTimeout(() => {
                    if (this.$refs && this.$refs.canvas) {
                      this.fitView()
                    }
                  }, 400)
                })

                if (this.rafId) {
                  cancelAnimationFrame(this.rafId)
                  this.rafId = null
                }
                return
              } else if (currentLeft < screenWidth * 0.4) {
                const centerX = screenWidth / 2
                const relativeX = currentLeft - centerX + (dialogWidth / 2)

                this.aiDialogMode = 'bottom'
                this.aiDialogPosition.x = relativeX
                this.aiDialogPosition.y = Math.max(-100, currentTop - (screenHeight - dialogHeight))
                this.aiDialogPositions['bottom'] = { ...this.aiDialogPosition }
                this.showToast('已切换为底部悬浮模式', 'info')
              } else {
                const minVisible = 60
                const maxX = screenWidth - minVisible - 20
                const minX = -(screenWidth - minVisible - 20)

                this.aiDialogPosition.x = Math.max(minX, Math.min(maxX, this.aiDialogPosition.x))
                this.aiDialogPosition.y = Math.max(-40, Math.min(screenHeight - 100, this.aiDialogPosition.y))
                this.aiDialogPositions['right'] = { ...this.aiDialogPosition }
              }
            }
            else if (this.aiDialogMode === 'bottom') {
              const currentLeft = (screenWidth / 2) + this.aiDialogPosition.x - (dialogWidth / 2)
              const currentTop = screenHeight - dialogHeight + this.aiDialogPosition.y

              const dockThreshold = screenWidth * 0.65
              const isNearRightEdge = currentLeft > dockThreshold
              const isVerticallyValid = currentTop > screenHeight * 0.05 && currentTop < screenHeight * 0.8

              if (isNearRightEdge && isVerticallyValid && !this.aiDialogCollapsed) {
                this.aiDialogDocked = true
                this.aiDialogMode = 'right'
                this.aiDialogCollapsed = false
                this.aiDialogPosition = { x: 0, y: 0 }
                dockedThisTime = true
                this.showToast('AI助手已固定到右侧', 'success')

                this.$nextTick(() => {
                  this.updateContainerSize()
                  setTimeout(() => {
                    if (this.$refs && this.$refs.canvas) {
                      this.fitView()
                    }
                  }, 400)
                })

                if (this.rafId) {
                  cancelAnimationFrame(this.rafId)
                  this.rafId = null
                }
                return
              } else {
                const maxOffsetX = screenWidth * 0.4
                this.aiDialogPosition.x = Math.max(-maxOffsetX, Math.min(maxOffsetX, this.aiDialogPosition.x))
                this.aiDialogPosition.y = Math.max(-(screenHeight - dialogHeight - 100), Math.min(0, this.aiDialogPosition.y))
                this.aiDialogPositions['bottom'] = { ...this.aiDialogPosition }
              }
            }
          }
        }
      } finally {
        this.isPanning = false
        this.isDraggingNode = false
        this.isMultiDragging = false
        this.draggedNode = null
        this.isBoxSelecting = false

        this.isDraggingAiDialog = false
        if (!this.aiDialogMovedThisSession) {
          this.hasDragged = false
        }
        this.aiDialogMovedThisSession = false

        if (this.connectingFrom) {
          this.connectingFrom = null
          this.connectingType = null
        }
      }
    },

    sendQuickAction(action) {
      this.aiChatInput = action.query
      this.sendAiChatMessage()
    },

    insertNewline(e) {
      e.preventDefault()
      this.aiChatInput += '\n'
    },

    scrollAiDialogToBottom() {
      const container = this.$refs.aiDialogMessages
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },

    formatMessage(text) {
      return text.replace(/\n/g, '<br>')
    },

    formatTime(date) {
      if (!date) return ''
      const d = new Date(date)
      return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
    },

    handleFullscreenChange() {
      const target = this.$refs.canvasStage
      this.isFullscreen = !!target && document.fullscreenElement === target

      this.$nextTick(() => {
        this.updateContainerSize()
        setTimeout(() => {
          if (this.$refs.canvas) {
            this.fitView()
          }
        }, 120)
      })
    },

    async toggleWorkbenchFullscreen() {
      const target = this.$refs.canvasStage
      if (!target) return

      try {
        if (document.fullscreenElement === target) {
          await document.exitFullscreen()
          return
        }

        if (document.fullscreenElement) {
          await document.exitFullscreen()
        }

        await target.requestFullscreen()
      } catch (error) {
        console.error('切换故障树全屏失败:', error)
        this.showToast('全屏切换失败，请重试', 'warn')
      }
    },

    startToolbarResize(e) {
      this.isToolbarResizing = true
      this.resizeStartX = e.clientX
      this.resizeStartToolbar = this.toolbarWidth
      e.preventDefault()
    },

    startPropResize(e) {
      this.isPropResizing = true
      this.resizeStartY = e.clientY
      this.resizeStartProp = this.propHeight
      e.preventDefault()
    },

    updateContainerSize() {
      if (!this.$refs.container) return

      const rect = this.$refs.container.getBoundingClientRect()
      this.containerWidth = rect.width
      this.containerHeight = rect.height

      if (this.aiDialogDocked && !this.aiDialogCollapsed) {
        this.$nextTick(() => {
          if (this.$refs.canvasContainer) {
            setTimeout(() => {
              if (this.$refs.canvasContainer) {
                this.fitView()
              }
            }, 420)
          }
        })
      }
    },

    getTextLines(label) {
      if (!label) return ['']
      const maxCharsPerLine = 6
      const lines = []
      let currentLine = ''

      for (let char of String(label)) {
        if (currentLine.length >= maxCharsPerLine) {
          lines.push(currentLine)
          currentLine = char
        } else {
          currentLine += char
        }
      }
      if (currentLine) lines.push(currentLine)
      return lines.length > 0 ? lines : ['']
    },

    calculateNodeScale(node) {
      if (node.type === 'gate') {
        node.scale = 1
        return
      }

      const lines = this.getTextLines(node.label)
      const lineCount = lines.length

      if (lineCount <= 1) {
        node.scale = 1.0
      } else if (lineCount === 2) {
        node.scale = 1.2
      } else if (lineCount === 3) {
        node.scale = 1.4
      } else {
        node.scale = 1.6
      }
    },

    setLayoutDirection(direction) {
      this.layoutDirection = direction
      if (Object.keys(this.parsedData.nodes).length > 0) {
        this.calculateLayout()
      }
    },

    getNodeTypeText(node) {
      const typeMap = {
        'top': '顶事件 (Top Event)',
        'gate': `逻辑门 (${node.gateType || 'OR'})`,
        'intermediate': '中间事件 (Intermediate)',
        'basic': '基本事件 (Basic Event)',
        'undeveloped': '未开展事件 (Undeveloped)',
        'initial': '初始事件 (Initial)',
        'conditional': '条件事件 (Conditional)'
      }
      return typeMap[node.type] || node.type
    },

    truncateLabel(label, maxLen) {
      if (!label) return ''
      if (label.length <= maxLen) return label
      return label.substring(0, maxLen) + '...'
    },

    loadTreeHistory(item) {
      if (!item || !item.dot) {
        console.warn('Invalid history item:', item)
        return
      }
      this.activeSection = 'history'
      this.inputData = item.dot
      this.$nextTick(() => {
        this.parseAndRender()
        this.scrollToSection('history')
      })
    },

    clearHistory() {
      if (this.historyTab === 'tree') {
        this.faultTreeHistory = []
      } else {
        this.chatHistory = []
      }
    },

    saveHistory() {
      if (this.isRestoring) return

      const state = JSON.stringify({
        nodes: this.parsedData.nodes,
        edges: this.parsedData.edges
      })

      if (this.historyIndex < this.history.length - 1) {
        this.history = this.history.slice(0, this.historyIndex + 1)
      }

      this.history.push(state)

      if (this.history.length > this.maxHistoryLength) {
        this.history.shift()
      } else {
        this.historyIndex++
      }
    },

    undo() {
      if (this.historyIndex > 0) {
        this.historyIndex--
        this.restoreHistory()
      }
    },

    redo() {
      if (this.historyIndex < this.history.length - 1) {
        this.historyIndex++
        this.restoreHistory()
      }
    },

    restoreHistory() {
      this.isRestoring = true
      const state = JSON.parse(this.history[this.historyIndex])

      this.parsedData.nodes = state.nodes
      this.parsedData.edges = state.edges

      this.nodes = Object.values(state.nodes).map(node => {
        this.calculateNodeScale(node)
        return node
      })

      this.updateEdges()

      this.selectedNode = null
      this.selectedNodes = []

      this.$nextTick(() => {
        this.isRestoring = false
      })
    },

    loadExample() {
      this.inputData = EXAMPLE_FTA_DATA
      this.parseAndRender()
      this.saveHistory()
        const ftTitle = String(this.aiTopEvent || this.aiSystem || '故障树').trim() || '故障树'
        this.faultTreeHistory.unshift({
          id: Date.now(),
          title: ftTitle,
          dot: String(this.inputData || ''),
          time: new Date().toLocaleString('zh-CN')
        })
        if (this.faultTreeHistory.length > 20) this.faultTreeHistory.pop()
      this.showToast('已加载无人机故障树示例', 'success')
    },

    handleAiFileUpload(event) {
      const file = event.target.files && event.target.files[0]
      if (!file) return
      this.aiUploadedFileName = file.name
      const reader = new FileReader()
      reader.onload = (e) => {
        this.rawSourceText = e.target.result
      }
      reader.onerror = () => {
        this.aiUploadedFileName = ''
        alert('文件读取失败，请重试')
      }
      // 对于文本类文件直接读为文本；PDF 等二进制格式给出提示
      const textTypes = ['.txt', '.md', '.csv', '.log']
      const isText = textTypes.some(ext => file.name.toLowerCase().endsWith(ext))
      if (isText) {
        reader.readAsText(file, 'UTF-8')
      } else {
        // 非纯文本文件（PDF/Word/Excel）：提示用户，并将文件名记录供后续扩展
        this.rawSourceText = `[已选择文件: ${file.name}]\n如需解析 PDF/Word/Excel 内容，请将文件内容复制粘贴到此处，或联系后端接口处理。`
      }
      // 重置 input 以允许重复选同一文件
      event.target.value = ''
    },

    async runAiExtraction() {
      this.aiError = ''
      this.aiSuccessInfo = ''
      this.aiItemsDebug = []

      const raw = String(this.rawSourceText || '').trim()
      if (!raw) {
        this.aiError = '请先粘贴原始文本数据'
        return
      }

      this.aiBusy = true
      try {
        await this.startReviewFirstExtraction(raw)
      } catch (err) {
        this.aiError = err.message || '请求失败，请确认后端服务可用'
      } finally {
        this.aiBusy = false
      }
    },

    async requestWorkflowJson(path, options = {}) {
      const token = this.getAuthToken()
      const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
      if (token) {
        headers.Authorization = token.startsWith('Bearer ') ? token : `Bearer ${token}`
      }

      const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers
      })

      let payload = null
      try {
        payload = await response.json()
      } catch (error) {
        payload = null
      }

      if (!response.ok) {
        const detail = payload?.detail
        const message = typeof detail === 'string'
          ? detail
          : detail?.message || JSON.stringify(detail || {})
        throw new Error(message || `请求失败：${response.status}`)
      }
      return payload || {}
    },

    async startReviewFirstExtraction(raw) {
      this.workflowResultId = ''
      this.workflowReleaseId = ''
      this.workflowBlocked = []
      this.workflowBuildAttempt = null
      this.workflowError = ''
      this.reviewItems = []
      this.reviewReasons = {}
      this.reviewBusyRecordId = ''
      this.inputData = ''
      this.dotRenderInfo = ''

      const payload = await this.requestWorkflowJson('/api/fta/extract', {
        method: 'POST',
        body: JSON.stringify({
          text: raw,
          text_chunk_size_chars: 6000,
          text_chunk_overlap_chars: 300,
          prompt_profile: 'balanced'
        })
      })

      const records = Array.isArray(payload.records) ? payload.records : []
      const reviews = Array.isArray(payload.reviews) ? payload.reviews : []
      const evidenceSpans = Array.isArray(payload.evidence_spans) ? payload.evidence_spans : []
      const reviewByRecordId = Object.fromEntries(
        reviews.map(review => [review.record_id, review])
      )

      this.workflowResultId = String(payload.result_id || '')
      this.aiItemsDebug = records
      this.reviewItems = records.map(record => ({
        record,
        review: reviewByRecordId[record.record_id] || {
          record_id: record.record_id,
          status: 'pending',
          reason: 'missing_initial_review_state'
        },
        evidenceSpans: evidenceSpans.filter(span => span.record_id === record.record_id)
      }))

      if (!this.workflowResultId) {
        throw new Error('后端未返回抽取结果 ID，无法继续审核')
      }

      const pendingPayload = await this.requestWorkflowJson('/api/fta/reviews/pending')
      const pendingIds = new Set(
        (Array.isArray(pendingPayload.items) ? pendingPayload.items : [])
          .filter(item => item.result_id === this.workflowResultId)
          .map(item => item.record?.record_id)
      )
      this.reviewItems.forEach(item => {
        if (pendingIds.has(item.record.record_id)) {
          item.review = { ...item.review, status: 'pending' }
        }
      })

      const count = this.reviewItems.length
      this.aiSuccessInfo = `抽取完成：${count} 条故障记录，其中 ${this.pendingReviewCount} 条需要人工审核。`

      if (!count) {
        this.workflowError = '本次抽取没有形成可审核的故障记录。'
        return
      }

      if (this.pendingReviewCount === 0) {
        await this.releaseAndBuild()
      } else {
        this.dotRenderInfo = '当前等待人工审核，审核通过后才会生成故障树。'
      }
    },

    reviewStatusText(status) {
      const statusMap = {
        pending: '待审核',
        not_required: '规则判断无需审核',
        approved: '已批准',
        rejected: '已拒绝',
        revision: '待补充'
      }
      return statusMap[status] || status || '未知状态'
    },

    async submitReviewDecision(item, action) {
      const recordId = item?.record?.record_id
      if (!recordId) return

      const reviewer = String(this.reviewerName || '').trim()
      if (!reviewer) {
        this.workflowError = '请先填写审核人。'
        return
      }

      const reason = String(this.reviewReasons[recordId] || '').trim()
      if ((action === 'reject' || action === 'revision') && !reason) {
        this.workflowError = action === 'reject' ? '拒绝审核必须填写原因。' : '要求补充必须填写原因。'
        return
      }

      const endpoint = {
        approve: '/api/fta/reviews/approve',
        reject: '/api/fta/reviews/reject',
        revision: '/api/fta/reviews/revision'
      }[action]
      if (!endpoint) return

      this.reviewBusyRecordId = recordId
      this.workflowError = ''
      try {
        const decision = await this.requestWorkflowJson(endpoint, {
          method: 'POST',
          body: JSON.stringify({
            record_id: recordId,
            reviewer,
            reason: reason || undefined
          })
        })
        item.review = decision
        this.aiSuccessInfo = `已记录审核：${item.record.description || recordId} → ${this.reviewStatusText(decision.status)}。`

        if (this.pendingReviewCount === 0) {
          const allAccepted = this.reviewItems.every(({ review }) => {
            return review && (review.status === 'approved' || review.status === 'not_required')
          })
          if (allAccepted) {
            await this.releaseAndBuild()
          } else {
            this.workflowError = '审核记录已保存，但存在未批准的故障记录，暂不自动建树。'
          }
        }
      } catch (err) {
        this.workflowError = err.message || '审核提交失败'
      } finally {
        this.reviewBusyRecordId = ''
      }
    },

    getAuthToken() {
      try {
        const candidates = [
          localStorage.getItem('token'),
          localStorage.getItem('access_token'),
          localStorage.getItem('auth_token')
        ].filter(Boolean)
        return candidates.length ? String(candidates[0]) : ''
      } catch (e) {
        return ''
      }
    },

    async parseAndRenderViaBackend() {
      this.parseError = ''
      this.dotRenderInfo = ''

      const rawDot = String(this.inputData || '').trim()
      const rawText = String(this.rawSourceText || '').trim()
      const raw = rawDot || rawText
      if (!raw) {
        this.parseError = '请先输入原始文本或 DOT 文本'
        return
      }

      this.dotSyncBusy = true
      try {
        await this.startReviewFirstExtraction(raw)
        this.dotRenderInfo = this.pendingReviewCount
          ? '后端抽取完成，等待审核；审核通过并建树后才会更新画布。'
          : this.dotRenderInfo
      } catch (err) {
        this.parseError = err?.message || '后端请求失败'
      } finally {
        this.dotSyncBusy = false
      }
    },

    treeToDot(tree) {
      if (!tree || typeof tree !== 'object') {
        throw new Error('建树接口未返回有效树结构')
      }

      let sequence = 0
      const lines = [
        'digraph FaultTree {',
        `  rankdir=${this.layoutDirection === 'horizontal' ? 'LR' : 'TB'};`,
        '  node [shape=box];'
      ]
      const nodeId = () => `n${++sequence}`
      const escapeLabel = (value) => String(value ?? '')
        .replace(/\\/g, '\\\\')
        .replace(/"/g, '\\"')
        .replace(/\r?\n/g, '\\n')
      const addNode = (label, shape) => {
        const id = nodeId()
        lines.push(`  ${id} [label="${escapeLabel(label)}", shape=${shape}];`)
        return id
      }
      const addEdge = (from, to) => lines.push(`  ${from} -> ${to};`)
      const labelWithProbability = (node) => {
        const name = String(node?.name || '未命名事件')
        const probability = node?.probability
        return probability === null || probability === undefined
          ? name
          : `${name}\\nP=${probability}`
      }

      const topId = addNode(tree.top || '故障树顶事件', 'doubleoctagon')
      const topGateId = addNode(tree.gate || 'OR', 'diamond')
      addEdge(topId, topGateId)

      const appendEvent = (node) => {
        const children = Array.isArray(node?.children) ? node.children : []
        const eventId = addNode(
          labelWithProbability(node),
          children.length ? 'box' : 'ellipse'
        )
        if (children.length) {
          const gateId = addNode(node.gate || 'OR', 'diamond')
          addEdge(eventId, gateId)
          children.forEach(child => addEdge(gateId, appendEvent(child)))
        }
        return eventId
      }

      const children = Array.isArray(tree.children) ? tree.children : []
      children.forEach(child => addEdge(topGateId, appendEvent(child)))
      lines.push('}')
      return lines.join('\n')
    },

    renderReleasedTree(tree) {
      const dot = this.treeToDot(tree)
      this.inputData = dot
      this.parseAndRender()
      if (this.parseError) {
        throw new Error(this.parseError)
      }
      this.saveHistory()
      const title = String(this.aiTopEvent || this.aiSystem || tree?.top || '故障树').trim() || '故障树'
      this.faultTreeHistory.unshift({
        id: Date.now(),
        title,
        dot,
        time: new Date().toLocaleString('zh-CN')
      })
      if (this.faultTreeHistory.length > 20) this.faultTreeHistory.pop()
      this.dotRenderInfo = '当前渲染来源：已审核放行后的建树结果'
      this.$nextTick(() => {
        const el = this.$refs.threeColArea
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    },

    async releaseAndBuild() {
      if (!this.workflowResultId || !this.reviewItems.length) return
      if (this.pendingReviewCount > 0) {
        this.workflowError = '仍有待审核故障记录，不能放行建树。'
        return
      }

      this.releaseBusy = true
      this.buildBusy = false
      this.workflowError = ''
      this.workflowBlocked = []
      try {
        const released = await this.requestWorkflowJson('/api/fta/release', {
          method: 'POST',
          body: JSON.stringify({ result_id: this.workflowResultId })
        })
        this.workflowReleaseId = String(released.release_id || '')
        this.workflowBlocked = Array.isArray(released.blocked) ? released.blocked : []

        if (this.workflowBlocked.length || !this.workflowReleaseId) {
          this.aiSuccessInfo = '审核结果已保存，但当前放行快照被拦截，暂未建树。'
          return
        }

        this.releaseBusy = false
        this.buildBusy = true
        const topEvent = String(this.aiTopEvent || '').trim() || String(this.aiSystem || '').trim() || '系统故障'
        const attempt = await this.requestWorkflowJson('/api/fta/build_released', {
          method: 'POST',
          body: JSON.stringify({
            release_id: this.workflowReleaseId,
            top_event: topEvent
          })
        })
        this.workflowBuildAttempt = attempt

        if (attempt.status !== 'succeeded' || !attempt.tree) {
          this.workflowError = attempt.reason || '建树被拒绝，已保留本次建树尝试记录。'
          return
        }

        this.renderReleasedTree(attempt.tree)
        this.aiSuccessInfo = `审核、放行和建树完成：${this.nodes.length} 个节点。`
        const chatAdvice = await this.fetchChatAdvice()
        if (chatAdvice) {
          this.aiSuccessInfo += ` 智能建议：${chatAdvice}`
          this.aiChatMessages.push({ role: 'assistant', text: chatAdvice })
          this.$nextTick(() => this.scrollAiChatToBottom())
        }
      } catch (err) {
        this.workflowError = err.message || '放行或建树失败'
      } finally {
        this.releaseBusy = false
        this.buildBusy = false
      }
    },

    toggleAiChatPanel() {
      this.aiChatCollapsed = !this.aiChatCollapsed
      if (!this.aiChatCollapsed) {
        this.$nextTick(() => this.scrollAiChatToBottom())
      }
    },

    async requestAiChatAnswer(question) {
      const treeContext = this.buildTreeContextForChat()
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          top_k: 3,
          use_knowledge_graph: !!this.aiUseKnowledgeGraph,
          system: String(this.aiSystem || '').trim() || undefined,
          tree_context: treeContext || undefined
        })
      })

      const payload = await response.json()
      if (!response.ok || !payload?.success) {
        throw new Error(payload?.detail || '问答请求失败')
      }

      return String(payload.answer || '').trim()
    },

    buildTreeContextForChat() {
      const topEvent = String(this.aiTopEvent || '').trim()
      const nodeCount = Array.isArray(this.nodes) ? this.nodes.length : 0
      const edgeCount = this.parsedData?.edges?.length || 0
      const dot = String(this.inputData || '').trim()
      const direction = this.layoutDirection === 'horizontal' ? '左到右(LR)' : '上到下(TB)'

      const nodeMap = this.parsedData?.nodes || {}
      const edges = Array.isArray(this.parsedData?.edges) ? this.parsedData.edges : []
      const relationLines = edges.slice(0, 60).map((e) => {
        const from = nodeMap[e.from]
        const to = nodeMap[e.to]
        const fromLabel = from?.label || from?.fullLabel || e.from
        const toLabel = to?.label || to?.fullLabel || e.to
        return `${fromLabel} -> ${toLabel}`
      })

      const summary = [
        `系统: ${String(this.aiSystem || '').trim() || '未指定'}`,
        `顶事件: ${topEvent || '未指定'}`,
        `布局方向: ${direction}`,
        `节点数: ${nodeCount}`,
        `连线数: ${edgeCount}`,
      ].join('\n')

      if (!dot) {
        return relationLines.length
          ? `${summary}\n\n当前故障树关系摘要:\n${relationLines.join('\n')}`
          : summary
      }

      const maxDotLen = 3800
      const clipped = dot.length > maxDotLen ? `${dot.slice(0, maxDotLen)}\n...（DOT已截断）` : dot
      const relationPart = relationLines.length ? `\n\n当前故障树关系摘要:\n${relationLines.join('\n')}` : ''
      return `${summary}${relationPart}\n\n当前故障树DOT:\n${clipped}`
    },

    async fetchChatAdvice() {
      const topEvent = String(this.aiTopEvent || '').trim()
      if (!topEvent) return ''

      try {
        const answer = await this.requestAiChatAnswer(`${topEvent} 的可能原因和建议排查步骤是什么？`)
        if (!answer) return ''

        return answer.length > 180 ? `${answer.slice(0, 180)}...` : answer
      } catch (err) {
        return ''
      }
    },

    async sendAiChatMessage() {
      this.aiChatError = ''
      const question = String(this.aiChatInput || '').trim()
      if (!question) return

      this.aiChatCollapsed = false
      this.aiChatMessages.push({ role: 'user', text: question, timestamp: new Date() })
      this.aiChatInput = ''
      this.aiChatBusy = true
      this.$nextTick(() => this.scrollAiDialogToBottom())

      try {
        const answer = await this.requestAiChatAnswer(question)
        this.aiChatMessages.push({ role: 'assistant', text: answer || '未获取到回答，请换个问法重试。', timestamp: new Date() })
        const lastUser = [...this.aiChatMessages].reverse().find(m => m.role === 'user')
        const lastAssist = [...this.aiChatMessages].reverse().find(m => m.role === 'assistant')
        this.chatHistory.unshift({
          id: Date.now(),
          question: lastUser ? lastUser.text : '',
          answer: lastAssist ? lastAssist.text : '',
          time: new Date().toLocaleString('zh-CN')
        })
        if (this.chatHistory.length > 30) this.chatHistory.pop()
      } catch (err) {
        this.aiChatError = err.message || '问答请求失败，请确认后端服务可用'
      } finally {
        this.aiChatBusy = false
        this.$nextTick(() => this.scrollAiDialogToBottom())
      }
    },

    parseDotData(dotText) {
      const nodes = {}
      const edges = []

      let content = dotText.replace(/digraph\s+\w+\s*\{/i, '')
      content = content.replace(/\}\s*$/, '')

      content = content.replace(/\/\/[^\n]*/g, '')
      content = content.replace(/\/\*[\s\S]*?\*\//g, '')

      const statements = content.split(';')
        .map(s => s.trim())
        .filter(s => s && s.length > 0)

      const nodeRegex = /^(\w+)\s*\[([^\]]*)\]/
      const edgeRegex = /^(\w+)\s*->\s*(\w+)/
      const attrRegex = /(\w+)\s*=\s*("([^"]*)"|([^,\s]*))/g

      for (const stmt of statements) {
        // Handle tokens like "} gate -> c1" emitted after "{ rank=same; ... }" blocks.
        const normalizedStmt = stmt
          .replace(/^\{\s*rank\s*=\s*same\s*$/i, '')
          .replace(/^\s*[{}]+\s*/, '')
          .trim()

        if (!normalizedStmt) {
          continue
        }

        if (/^(rankdir|graph|node|edge|rank)\b/.test(normalizedStmt)) {
          continue
        }

        const nodeMatch = normalizedStmt.match(nodeRegex)
        if (nodeMatch) {
          const id = nodeMatch[1]
          const attrStr = nodeMatch[2]
          const attrs = {}

          let attrMatch
          while ((attrMatch = attrRegex.exec(attrStr)) !== null) {
            const key = attrMatch[1]
            const value = attrMatch[3] !== undefined ? attrMatch[3] : attrMatch[4]
            attrs[key] = value
          }

          let label = attrs.label || id
          let probability = null

          const probMatch = label.match(/P=([0-9.]+)/i)
          if (probMatch) {
            probability = parseFloat(probMatch[1])
            label = label.replace(/\\?n?P=[0-9.]+/i, '').trim()
          }

          label = label.replace(/\\n/g, '\n')

          let type = 'intermediate'
          let renderShape = attrs.shape || 'box'

          if (renderShape === 'doubleoctagon') {
            type = 'top'
            renderShape = 'doubleoctagon'
          } else if (renderShape === 'diamond') {
            type = 'gate'
            renderShape = 'gate'
          } else if (renderShape === 'ellipse') {
            type = 'basic'
            renderShape = 'basic'
          } else if (renderShape === 'box') {
            type = 'intermediate'
            renderShape = 'box'
          }

          let gateType = null
          if (type === 'gate') {
            const labelUpper = label.toUpperCase()
            if (labelUpper.includes('AND')) gateType = 'AND'
            else if (labelUpper.includes('XOR')) gateType = 'XOR'
            else if (labelUpper.includes('INHIBIT')) gateType = 'INHIBIT'
            else if (labelUpper.includes('PAND')) gateType = 'PAND'
            else gateType = 'OR'
          }

          if (type !== 'gate' && type !== 'top') {
            const labelLower = label.toLowerCase()
            if (labelLower.includes('未开展') || labelLower.includes('undeveloped')) {
              type = 'undeveloped'
              renderShape = 'undeveloped'
            } else if (labelLower.includes('初始') || labelLower.includes('initial')) {
              type = 'initial'
              renderShape = 'initial'
            } else if (labelLower.includes('条件') || labelLower.includes('conditional')) {
              type = 'conditional'
              renderShape = 'conditional'
            }
          }

          const node = {
            id,
            label: label.split('\n')[0],
            fullLabel: label,
            type,
            shape: renderShape,
            gateType,
            probability,
            parent: null,
            parents: [],
            children: [],
            attrs,
            scale: 1.0
          }

          this.calculateNodeScale(node)
          nodes[id] = node
          continue
        }

        const edgeMatch = normalizedStmt.match(edgeRegex)
        if (edgeMatch) {
          edges.push({
            from: edgeMatch[1],
            to: edgeMatch[2]
          })
        }
      }

      edges.forEach(edge => {
        const parent = nodes[edge.from]
        const child = nodes[edge.to]
        if (parent && child) {
          if (!Array.isArray(parent.children)) parent.children = []
          if (!parent.children.includes(edge.to)) {
            parent.children.push(edge.to)
          }
          if (!Array.isArray(child.parents)) child.parents = []
          if (!child.parents.includes(edge.from)) {
            child.parents.push(edge.from)
          }
          if (!child.parent) child.parent = edge.from
        }
      })

      // 自动检测并修正反向边
      const topNode = Object.values(nodes).find(n => n.type === 'top')
      if (topNode) {
        const hasOutgoing = edges.some(e => e.from === topNode.id)
        const hasIncoming = edges.some(e => e.to === topNode.id)

        if (!hasOutgoing && hasIncoming) {
          Object.values(nodes).forEach(node => {
            node.parent = null
            node.parents = []
            node.children = []
          })

          edges.forEach(edge => {
            const temp = edge.from
            edge.from = edge.to
            edge.to = temp
          })

          edges.forEach(edge => {
            const parent = nodes[edge.from]
            const child = nodes[edge.to]
            if (parent && child) {
              if (!Array.isArray(parent.children)) parent.children = []
              if (!parent.children.includes(edge.to)) {
                parent.children.push(edge.to)
              }
              if (!Array.isArray(child.parents)) child.parents = []
              if (!child.parents.includes(edge.from)) {
                child.parents.push(edge.from)
              }
              if (!child.parent) child.parent = edge.from
            }
          })
        }
      }

      return { nodes, edges }
    },

    exportDot() {
      let dot = 'digraph FaultTree {\n'
      dot += `  rankdir=${this.layoutDirection === 'horizontal' ? 'LR' : 'TB'};\n`
      dot += '  node [shape=box];\n\n'

      Object.values(this.parsedData.nodes).forEach(node => {
        let attrs = [`label="${node.label}${node.probability ? '\\nP=' + node.probability : ''}"`]

        if (node.shape === 'doubleoctagon') attrs.push('shape=doubleoctagon')
        else if (node.shape === 'diamond') attrs.push('shape=diamond')
        else if (node.shape === 'ellipse') attrs.push('shape=ellipse')

        dot += `  ${node.id} [${attrs.join(', ')}];\n`
      })

      dot += '\n'

      this.parsedData.edges.forEach(edge => {
        dot += `  ${edge.from} -> ${edge.to};\n`
      })

      dot += '}'

      navigator.clipboard.writeText(dot).then(() => {
        this.showToast('DOT 代码已复制到剪贴板', 'success')
      }).catch(() => {
        this.inputData = dot
        this.showToast('DOT 代码已显示在左上方面板中', 'info')
      })
    },

    clearCanvas() {
      this.parsedData = { nodes: {}, edges: [] }
      this.nodes = []
      this.edges = []
      this.pathEdges = []
      this.selectedNode = null
      this.selectedNodes = []

      this.saveHistory()
    },

    calculateLayout() {
      const nodes = Object.values(this.parsedData.nodes)
      if (nodes.length === 0) return

      const levelHeight = 160
      const levelWidth = 240
      const nodeSpacing = 100

      const ids = nodes.map(n => n.id)
      const outgoing = {}
      const incoming = {}
      ids.forEach(id => {
        outgoing[id] = []
        incoming[id] = []
      })

      this.parsedData.edges.forEach(edge => {
        if (!this.parsedData.nodes[edge.from] || !this.parsedData.nodes[edge.to]) return
        outgoing[edge.from].push(edge.to)
        incoming[edge.to].push(edge.from)
      })

      const topNode =
        nodes.find(n => n.type === 'top' || n.shape === 'doubleoctagon' || n.id === 'top') ||
        nodes[0]

      const useIncomingAsChildren = topNode
        ? ((incoming[topNode.id] || []).length > 0 && (outgoing[topNode.id] || []).length === 0)
        : false

      const getChildren = (id) => useIncomingAsChildren ? [...incoming[id]] : [...outgoing[id]]

      // BFS 计算层级
      const levelById = {}
      ids.forEach(id => levelById[id] = Infinity)
      if (topNode) {
        const queue = [topNode.id]
        levelById[topNode.id] = 0
        let qi = 0
        while (qi < queue.length) {
          const cur = queue[qi++]
          getChildren(cur).forEach(cid => {
            if (levelById[cid] > levelById[cur] + 1) {
              levelById[cid] = levelById[cur] + 1
              queue.push(cid)
            }
          })
        }
      }

      const fallback = ids.map(id => levelById[id]).filter(v => isFinite(v))
      const fbLv = fallback.length ? Math.max(...fallback) + 1 : 0
      ids.forEach(id => { if (!isFinite(levelById[id])) levelById[id] = fbLv })

      const levels = {}
      ids.forEach(id => {
        const lv = Math.max(0, Math.floor(levelById[id]))
        if (!levels[lv]) levels[lv] = []
        levels[lv].push(id)
      })

      // ========== 改进的树布局：简化版 Reingold-Tilford ==========
      const relX = {}      // 节点在其子树内的相对 x
      const contour = {}   // 子树轮廓 { left, right }
      const childRelPos = {} // 父节点 -> 子节点 -> 相对位置

      const sortedLevels = Object.keys(levels).map(Number).sort((a, b) => b - a)

      sortedLevels.forEach(lv => {
        levels[lv].forEach(id => {
          const children = getChildren(id).filter(cid => levelById[cid] === lv + 1)

          if (children.length === 0) {
            relX[id] = 0
            contour[id] = { left: -nodeSpacing / 2, right: nodeSpacing / 2 }
          } else {
            let currentX = 0
            const positions = {}

            children.forEach((cid, idx) => {
              if (idx === 0) {
                positions[cid] = 0
              } else {
                const prevCid = children[idx - 1]
                const prevRight = positions[prevCid] + contour[prevCid].right
                const currLeft = contour[cid].left
                const gap = nodeSpacing
                currentX = prevRight - currLeft + gap
                positions[cid] = currentX
              }
            })

            // 父节点居中于子节点范围
            const firstPos = positions[children[0]]
            const lastPos = positions[children[children.length - 1]]
            relX[id] = (firstPos + lastPos) / 2

            // 计算子树轮廓
            let leftBound = Infinity
            let rightBound = -Infinity
            children.forEach(cid => {
              leftBound = Math.min(leftBound, positions[cid] + contour[cid].left)
              rightBound = Math.max(rightBound, positions[cid] + contour[cid].right)
            })
            leftBound = Math.min(leftBound, relX[id] - nodeSpacing / 2)
            rightBound = Math.max(rightBound, relX[id] + nodeSpacing / 2)

            contour[id] = { left: leftBound - relX[id], right: rightBound - relX[id] }
            childRelPos[id] = {}
            children.forEach(cid => {
              childRelPos[id][cid] = positions[cid] - relX[id]
            })
          }
        })
      })

      // 前序遍历分配绝对坐标
      const posX = {}
      if (topNode) {
        posX[topNode.id] = 0
        const stack = [topNode.id]
        while (stack.length > 0) {
          const cur = stack.pop()
          const children = getChildren(cur).filter(cid => levelById[cid] === levelById[cur] + 1)
          children.forEach(cid => {
            posX[cid] = posX[cur] + (childRelPos[cur]?.[cid] || 0)
            stack.push(cid)
          })
        }
      }

      // 孤立节点平铺
      ids.filter(id => posX[id] === undefined).forEach((id, idx) => {
        posX[id] = idx * nodeSpacing * 2
      })

      // 计算整体偏移使树居中于原点
      const allX = Object.values(posX)
      const minX = Math.min(...allX)
      const maxX = Math.max(...allX)
      const centerOffset = -(minX + maxX) / 2

      // 应用坐标
      Object.keys(levels).forEach(lvStr => {
        const lv = parseInt(lvStr)
        levels[lv].forEach(id => {
          const node = this.parsedData.nodes[id]
          const cross = (posX[id] ?? 0) + centerOffset
          if (this.layoutDirection === 'horizontal') {
            node.x = lv * levelWidth + 120
            node.y = cross + 300
          } else {
            node.x = cross + 500
            node.y = lv * levelHeight + 100
          }
        })
      })

      this.nodes = nodes
      this.updateEdges()
    },

    // ===== 改进后的 updateEdges：标准故障树连线（鱼骨型） =====
    updateEdges() {
      this.edges = []
      this.pathEdges = []

      const getPort = (node, side) => {
        const s = node.scale || 1
        const x = node.x, y = node.y
        const shape = node.shape || 'ellipse'
        const hw = shape === 'box' || shape === 'doubleoctagon' ? 55 * s : 45 * s
        const hh = shape === 'box' || shape === 'doubleoctagon' ? 40 * s : 35 * s
        const gateHW = 18 * s, gateHH = 18 * s
        const isGate = node.type === 'gate'
        const effHW = isGate ? gateHW : hw
        const effHH = isGate ? gateHH : hh

        if (side === 'right') return { x: x + effHW, y }
        if (side === 'left') return { x: x - effHW, y }
        if (side === 'bottom') return { x, y: y + effHH }
        if (side === 'top') return { x, y: y - effHH }
        return { x, y }
      }

      const r = 10

      this.parsedData.edges.forEach(edge => {
        const fromNode = this.parsedData.nodes[edge.from]
        const toNode = this.parsedData.nodes[edge.to]
        if (!fromNode || !toNode || fromNode.x === undefined || toNode.x === undefined) return

        let path = ''

        if (this.layoutDirection === 'horizontal') {
          const goRight = toNode.x >= fromNode.x
          const start = getPort(fromNode, goRight ? 'right' : 'left')
          const end = getPort(toNode, goRight ? 'left' : 'right')
          const midX = (start.x + end.x) / 2

          if (Math.abs(end.y - start.y) < 6) {
            path = `M ${start.x} ${start.y} L ${end.x} ${end.y}`
          } else {
            const dy = end.y > start.y ? 1 : -1
            path = `M ${start.x} ${start.y} ` +
                   `L ${midX - r * (goRight ? 1 : -1)} ${start.y} ` +
                   `Q ${midX} ${start.y} ${midX} ${start.y + dy * r} ` +
                   `L ${midX} ${end.y - dy * r} ` +
                   `Q ${midX} ${end.y} ${midX + r * (goRight ? 1 : -1)} ${end.y} ` +
                   `L ${end.x} ${end.y}`
          }
        } else {
          const goDown = toNode.y >= fromNode.y
          const start = getPort(fromNode, goDown ? 'bottom' : 'top')
          const end = getPort(toNode, goDown ? 'top' : 'bottom')
          const midY = (start.y + end.y) / 2

          if (Math.abs(end.x - start.x) < 6) {
            path = `M ${start.x} ${start.y} L ${end.x} ${end.y}`
          } else {
            const dx = end.x > start.x ? 1 : -1
            path = `M ${start.x} ${start.y} ` +
                   `L ${start.x} ${midY - r * (goDown ? 1 : -1)} ` +
                   `Q ${start.x} ${midY} ${start.x + dx * r} ${midY} ` +
                   `L ${end.x - dx * r} ${midY} ` +
                   `Q ${end.x} ${midY} ${end.x} ${midY + r * (goDown ? 1 : -1)} ` +
                   `L ${end.x} ${end.y}`
          }
        }

        this.pathEdges.push({
          id: `${edge.from}-${edge.to}`,
          path,
          markerEnd: true,
          markerStart: false
        })
      })
    },

    parseAndRender() {
      this.parseError = ''

      try {
        const { nodes, edges } = this.parseDotData(this.inputData)

        if (Object.keys(nodes).length === 0) {
          this.parseError = '未找到有效节点'
          return
        }

        this.parsedData = { nodes, edges }
        this.calculateLayout()
        this.fitView()

      } catch (err) {
        this.parseError = '解析错误: ' + err.message
        console.error(err)
      }
    },

    autoLayout() {
      this.selectedNodes = []
      this.calculateLayout()
      this.fitView()
      this.saveHistory()
    },

    fitView() {
      if (!Array.isArray(this.nodes) || this.nodes.length === 0) return

      const canvasEl = this.$refs && this.$refs.canvas
      if (!canvasEl || typeof canvasEl.getBoundingClientRect !== 'function') return

      const padding = 80
      const xs = this.nodes.map(n => n.x)
      const ys = this.nodes.map(n => n.y)
      const scales = this.nodes.map(n => n.scale || 1)
      const maxScale = Math.max(...scales)

      const minX = Math.min(...xs) - 100 * maxScale
      const maxX = Math.max(...xs) + 100 * maxScale
      const minY = Math.min(...ys) - 60 * maxScale
      const maxY = Math.max(...ys) + 60 * maxScale

      const contentWidth = maxX - minX
      const contentHeight = maxY - minY

      let canvasRect = null
      try {
        canvasRect = canvasEl.getBoundingClientRect()
      } catch (error) {
        return
      }

      if (!canvasRect || !canvasRect.width || !canvasRect.height) return
      const scaleX = (canvasRect.width - padding * 2) / contentWidth
      const scaleY = (canvasRect.height - padding * 2) / contentHeight

      this.zoom = Math.min(scaleX, scaleY, 1.2)
      this.panX = padding - minX * this.zoom + (canvasRect.width - padding * 2 - contentWidth * this.zoom) / 2
      this.panY = padding - minY * this.zoom + (canvasRect.height - padding * 2 - contentHeight * this.zoom) / 2
    },

    zoomIn() {
      this.zoom = Math.min(3, this.zoom * 1.2)
    },

    zoomOut() {
      this.zoom = Math.max(0.1, this.zoom / 1.2)
    },

    resetZoom() {
      this.zoom = 1
      this.panX = 50
      this.panY = 50
    },

    saveTreeImage() {
      const canvas = this.$refs.canvas
      if (!canvas) {
        alert('故障树画布未找到')
        return
      }

      if (!Array.isArray(this.nodes) || this.nodes.length === 0) {
        alert('当前无可导出的故障树内容')
        return
      }

      // 仅按节点范围导出，避免虚拟超大网格背景导致SVG解码失败。
      let minX = Infinity
      let minY = Infinity
      let maxX = -Infinity
      let maxY = -Infinity
      for (const node of this.nodes) {
        const scale = Number(node?.scale || 1)
        const x = Number(node?.x || 0)
        const y = Number(node?.y || 0)
        const halfW = 70 * scale
        const halfH = 55 * scale
        minX = Math.min(minX, x - halfW)
        minY = Math.min(minY, y - halfH)
        maxX = Math.max(maxX, x + halfW)
        maxY = Math.max(maxY, y + halfH)
      }

      if (!isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)) {
        alert('导出范围计算失败，请重试')
        return
      }

      const padding = 30
      const exportX = minX - padding
      const exportY = minY - padding
      const exportWidth = Math.max(1, maxX - minX + padding * 2)
      const exportHeight = Math.max(1, maxY - minY + padding * 2)
      const fileName = `fault-tree-${Date.now()}.png`

      const fallbackDownload = (blob) => {
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = fileName
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      }

      // 创建一个临时 canvas 元素用于转换
      const tempCanvas = document.createElement('canvas')
      const scale = 2 // 2x 分辨率以获得更好的质量
      tempCanvas.width = Math.round(exportWidth * scale)
      tempCanvas.height = Math.round(exportHeight * scale)

      const ctx = tempCanvas.getContext('2d')
      if (!ctx) {
        alert('图片上下文初始化失败，请重试')
        return
      }
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height)
      ctx.scale(scale, scale)

      // 将 SVG 转换为图像（Blob URL + createImageBitmap 双通道，兼容性更稳定）
      const svgEl = canvas.cloneNode(true)
      if (!svgEl.getAttribute('xmlns')) {
        svgEl.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
      }
      if (!svgEl.getAttribute('xmlns:xlink')) {
        svgEl.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
      }
      svgEl.setAttribute('width', String(exportWidth))
      svgEl.setAttribute('height', String(exportHeight))
      svgEl.setAttribute('viewBox', `${exportX} ${exportY} ${exportWidth} ${exportHeight}`)

      // 移除超大背景层和交互点，减小导出SVG复杂度。
      svgEl.querySelectorAll('rect[x="-50000"]').forEach((el) => el.remove())
      svgEl.querySelectorAll('rect[width="100000"]').forEach((el) => el.remove())
      svgEl.querySelectorAll('.connection-point').forEach((el) => el.remove())

      const svgData = new XMLSerializer().serializeToString(svgEl)
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })

      const renderAndSave = async () => {
        let rendered = false
        let lastError = ''

        if (typeof window.createImageBitmap === 'function') {
          try {
            const bitmap = await window.createImageBitmap(svgBlob)
            ctx.drawImage(bitmap, 0, 0, exportWidth, exportHeight)
            if (typeof bitmap.close === 'function') bitmap.close()
            rendered = true
          } catch (err) {
            lastError = err?.message || String(err)
          }
        }

        if (!rendered) {
          const svgUrl = URL.createObjectURL(svgBlob)
          try {
            await new Promise((resolve, reject) => {
              const img = new Image()
              img.onload = () => {
                ctx.drawImage(img, 0, 0, exportWidth, exportHeight)
                resolve(null)
              }
              img.onerror = (e) => {
                reject(new Error('Image解码失败'))
              }
              img.src = svgUrl
            })
            rendered = true
          } catch (err) {
            lastError = lastError || err?.message || String(err)
          } finally {
            URL.revokeObjectURL(svgUrl)
          }
        }

        if (!rendered) {
          alert(`图片转换失败，请重试\n原因: ${lastError || '未知错误'}`)
          return
        }

        tempCanvas.toBlob(async (blob) => {
          if (!blob) {
            alert('图片转换失败，请重试')
            return
          }

          try {
            if (window.showSaveFilePicker) {
              const handle = await window.showSaveFilePicker({
                suggestedName: fileName,
                types: [
                  {
                    description: 'PNG 图片',
                    accept: { 'image/png': ['.png'] }
                  }
                ]
              })
              const writable = await handle.createWritable()
              await writable.write(blob)
              await writable.close()
              alert('图片保存成功')
            } else {
              fallbackDownload(blob)
            }
          } catch (err) {
            if (err.name === 'AbortError') return
            try {
              fallbackDownload(blob)
            } catch (fallbackErr) {
              console.error('保存失败:', err, fallbackErr)
              alert('保存失败，请重试')
            }
          }
        }, 'image/png')
      }

      renderAndSave().catch((err) => {
        console.error('导出异常:', err)
        alert(`图片转换失败，请重试\n原因: ${err?.message || '未知错误'}`)
      })
    },

    showContextMenu(e, node) {
      const isGate = node.type === 'gate' && ['OR', 'AND', 'XOR'].includes(node.gateType)

      const containerEl = this.$refs.canvasContainer
      const rect = containerEl ? containerEl.getBoundingClientRect() : { left: 0, top: 0 }
      let x = e.clientX - rect.left
      let y = e.clientY - rect.top

      const menuW = 170
      const menuH = 160
      if (x + menuW > rect.width) x = rect.width - menuW - 8
      if (y + menuH > rect.height) y = rect.height - menuH - 8
      if (x < 4) x = 4
      if (y < 4) y = 4

      this.contextMenu = {
        show: true,
        x,
        y,
        node: node,
        isGate: isGate
      }
      this.selectedNode = node
    },

    hideContextMenu() {
      this.contextMenu.show = false
    },

    deleteContextNode() {
      if (this.contextMenu.node) {
        this.deleteNode(this.contextMenu.node)
      }
      this.hideContextMenu()
    },

    duplicateNode() {
      if (!this.contextMenu.node) return

      const original = this.contextMenu.node
      const newId = `${original.id}_copy_${Date.now()}`
      const newNode = {
        ...original,
        id: newId,
        x: original.x + 40,
        y: original.y + 40,
        parent: null,
        children: []
      }

      this.calculateNodeScale(newNode)

      this.parsedData.nodes[newId] = newNode
      this.nodes.push(newNode)
      this.selectedNode = newNode
      this.selectedNodes = [newNode]
      this.hideContextMenu()
      this.saveHistory()
    },

    editNodeLabel() {
      const newLabel = prompt('输入新标签:', this.contextMenu.node.label)
      if (newLabel !== null && newLabel.trim() !== '') {
        this.contextMenu.node.label = newLabel.trim()
        if (this.parsedData.nodes[this.contextMenu.node.id]) {
          this.parsedData.nodes[this.contextMenu.node.id].label = newLabel.trim()
        }
        this.calculateNodeScale(this.contextMenu.node)
        this.updateEdges()
        this.saveHistory()
      }
      this.hideContextMenu()
    },

    connectToParent() {
      this.showToast('请点击目标父节点完成连接', 'info')
      this.connectingFrom = this.contextMenu.node
      this.connectingType = 'input'
      this.hideContextMenu()
    },

    connectToChild() {
      this.showToast('请点击目标子节点完成连接', 'info')
      this.connectingFrom = this.contextMenu.node
      this.connectingType = 'output'
      this.hideContextMenu()
    },

    deleteNode(node) {
      delete this.parsedData.nodes[node.id]

      this.parsedData.edges = this.parsedData.edges.filter(e => e.from !== node.id && e.to !== node.id)

      if (node.parent && this.parsedData.nodes[node.parent]) {
        const parent = this.parsedData.nodes[node.parent]
        parent.children = parent.children.filter(id => id !== node.id)
      }

      if (node.children) {
        node.children.forEach(childId => {
          if (this.parsedData.nodes[childId]) {
            this.parsedData.nodes[childId].parent = null
          }
        })
      }

      this.selectedNodes = this.selectedNodes.filter(n => n.id !== node.id)

      this.calculateLayout()

      if (this.selectedNode && this.selectedNode.id === node.id) {
        this.selectedNode = null
      }

      this.saveHistory()
    },

    deleteSelectedNodes() {
      if (this.selectedNodes.length === 0) return

      this.selectedNodes.forEach(node => {
        delete this.parsedData.nodes[node.id]

        this.parsedData.edges = this.parsedData.edges.filter(e => e.from !== node.id && e.to !== node.id)

        if (node.parent && this.parsedData.nodes[node.parent]) {
          const parent = this.parsedData.nodes[node.parent]
          parent.children = parent.children.filter(id => id !== node.id)
        }

        if (node.children) {
          node.children.forEach(childId => {
            if (this.parsedData.nodes[childId]) {
              this.parsedData.nodes[childId].parent = null
            }
          })
        }
      })

      this.selectedNodes = []
      this.selectedNode = null
      this.calculateLayout()
      this.saveHistory()
    },

    copySelectedNodes() {
      if (this.selectedNodes.length === 0 && this.selectedNode) {
        this.selectedNodes = [this.selectedNode]
      }

      this.clipboard = this.selectedNodes.map(node => ({
        ...node,
        id: `${node.id}_copy_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        x: node.x + 40,
        y: node.y + 40,
        parent: null,
        children: []
      }))

      this.showToast(`已复制 ${this.clipboard.length} 个节点`, 'success')
    },

    pasteNodes() {
      if (this.clipboard.length === 0) return

      const newNodes = []
      this.clipboard.forEach(node => {
        const newNode = { ...node }
        this.calculateNodeScale(newNode)
        this.parsedData.nodes[newNode.id] = newNode
        this.nodes.push(newNode)
        newNodes.push(newNode)
      })

      this.selectedNodes = newNodes
      this.selectedNode = newNodes[0]
      this.saveHistory()
    },

    handleKeyDown(e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

      if (e.key === 'z' && e.ctrlKey) {
        e.preventDefault()
        this.undo()
        return
      }

      if (e.key === 'y' && e.ctrlKey) {
        e.preventDefault()
        this.redo()
        return
      }

      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (this.selectedNodes.length > 0) {
          this.deleteSelectedNodes()
        } else if (this.selectedNode) {
          this.deleteNode(this.selectedNode)
        }
      }

      if (e.key === 'a' && e.ctrlKey) {
        e.preventDefault()
        this.selectedNodes = [...this.nodes]
      }

      if (e.key === 'c' && e.ctrlKey) {
        e.preventDefault()
        this.copySelectedNodes()
      }

      if (e.key === 'v' && e.ctrlKey) {
        e.preventDefault()
        this.pasteNodes()
      }

      if (e.key === 'Escape') {
        this.selectedNodes = []
        this.selectedNode = null
        this.hideContextMenu()
        this.connectingFrom = null
      }
    },

    startBoxSelect(e) {
      if (this.isDraggingNode || this.draggedNode) {
        return
      }

      const rect = this.$refs.canvas.getBoundingClientRect()
      const x = (e.clientX - rect.left - this.panX) / this.zoom
      const y = (e.clientY - rect.top - this.panY) / this.zoom

      this.isBoxSelecting = true
      this.boxSelectStart = { x, y }
      this.boxSelectRect = { x, y, width: 0, height: 0 }
    },

    updateBoxSelect(e) {
      const rect = this.$refs.canvas.getBoundingClientRect()
      const currentX = (e.clientX - rect.left - this.panX) / this.zoom
      const currentY = (e.clientY - rect.top - this.panY) / this.zoom

      const x = Math.min(this.boxSelectStart.x, currentX)
      const y = Math.min(this.boxSelectStart.y, currentY)
      const width = Math.abs(currentX - this.boxSelectStart.x)
      const height = Math.abs(currentY - this.boxSelectStart.y)

      this.boxSelectRect = { x, y, width, height }
    },

    endBoxSelect() {
      if (!this.isBoxSelecting) return

      const selected = this.nodes.filter(node => {
        return node.x >= this.boxSelectRect.x &&
               node.x <= this.boxSelectRect.x + this.boxSelectRect.width &&
               node.y >= this.boxSelectRect.y &&
               node.y <= this.boxSelectRect.y + this.boxSelectRect.height
      })

      if (selected.length > 0) {
        this.selectedNodes = selected
        this.selectedNode = null
      }

      this.isBoxSelecting = false
    },

    startConnect(e, node, type) {
      e.stopPropagation()
      e.preventDefault()

      this.connectingFrom = node
      this.connectingType = type

      const rect = this.$refs.canvas.getBoundingClientRect()
      this.tempLineEnd = {
        x: (e.clientX - rect.left - this.panX) / this.zoom,
        y: (e.clientY - rect.top - this.panY) / this.zoom
      }
    },

    completeConnect(targetNode) {
      if (!this.connectingFrom || this.connectingFrom.id === targetNode.id) {
        this.connectingFrom = null
        this.connectingType = null
        return
      }

      let parentId, childId

      if (this.connectingType === 'output') {
        parentId = this.connectingFrom.id
        childId = targetNode.id
      } else {
        parentId = targetNode.id
        childId = this.connectingFrom.id
      }

      const exists = this.parsedData.edges.some(e =>
        (e.from === parentId && e.to === childId)
      )

      if (exists) {
        this.showToast('连接已存在', 'warn')
        this.connectingFrom = null
        this.connectingType = null
        return
      }

      if (this.wouldCreateCycle(parentId, childId)) {
        this.showToast('不能建立循环连接', 'warn')
        this.connectingFrom = null
        this.connectingType = null
        return
      }

      let parent = this.parsedData.nodes[parentId]
      let child = this.parsedData.nodes[childId]

      if (!parent) {
        parent = this.nodes.find(n => n.id === parentId)
        if (parent) this.parsedData.nodes[parentId] = parent
      }
      if (!child) {
        child = this.nodes.find(n => n.id === childId)
        if (child) this.parsedData.nodes[childId] = child
      }

      if (!parent || !child) {
        this.showToast('连接失败：节点未找到', 'warn')
        this.connectingFrom = null
        this.connectingType = null
        return
      }

      this.parsedData.edges.push({
        from: parentId,
        to: childId
      })

      if (!parent.children) parent.children = []
      parent.children.push(childId)

      if (child.parent && this.parsedData.nodes[child.parent]) {
        const oldParent = this.parsedData.nodes[child.parent]
        oldParent.children = oldParent.children.filter(id => id !== childId)
        this.parsedData.edges = this.parsedData.edges.filter(e =>
          !(e.from === child.parent && e.to === childId)
        )
      }

      child.parent = parentId

      this.updateEdges()
      this.saveHistory()

      this.connectingFrom = null
      this.connectingType = null
    },

    wouldCreateCycle(parentId, childId) {
      const visited = new Set()
      const stack = [childId]

      while (stack.length > 0) {
        const current = stack.pop()
        if (current === parentId) return true
        if (visited.has(current)) continue
        visited.add(current)

        const node = this.parsedData.nodes[current]
        if (node && node.children) {
          stack.push(...node.children)
        }
      }

      return false
    },

    getDescendants(nodeId) {
      const result = []
      const visited = new Set()
      const queue = [nodeId]
      while (queue.length) {
        const cur = queue.shift()
        if (visited.has(cur)) continue
        visited.add(cur)
        this.parsedData.edges.forEach(edge => {
          if (edge.from === cur && !visited.has(edge.to)) {
            result.push(edge.to)
            queue.push(edge.to)
          }
        })
      }
      return result
    },

    getChildren(nodeId) {
      const result = []
      this.parsedData.edges.forEach(edge => {
        if (edge.from === nodeId) {
          result.push(edge.to)
        }
      })
      return result
    },

    startNodeDrag(e, node) {
      e.stopPropagation()
      e.preventDefault()

      this.isBoxSelecting = false

      if (typeof node.x !== 'number') node.x = 0
      if (typeof node.y !== 'number') node.y = 0

      if (this.connectingFrom) {
        if (this.connectingFrom.id !== node.id) {
          this.completeConnect(node)
        }
        return
      }

      if (e.target.classList && e.target.classList.contains('connection-point')) {
        return
      }

      if (e.ctrlKey || e.metaKey) {
        if (!this.selectedNodes.includes(node)) {
          this.selectedNodes.push(node)
        } else {
          this.selectedNodes = this.selectedNodes.filter(n => n.id !== node.id)
        }
        return
      }

      if (!this.selectedNodes.includes(node)) {
        this.selectedNodes = []
      }

      if (this.selectedNodes.length > 0 && this.selectedNodes.includes(node)) {
        this.isMultiDragging = true
        this.isDraggingNode = true
        this.draggedNode = node

        const rect = this.$refs.canvas.getBoundingClientRect()
        this.dragOffsetX = (e.clientX - rect.left - this.panX) / this.zoom - node.x
        this.dragOffsetY = (e.clientY - rect.top - this.panY) / this.zoom - node.y

        this.selectedNodes.forEach(n => {
          n._initialX = n.x
          n._initialY = n.y
        })
      } else {
        this.isDraggingNode = true
        this.draggedNode = node
        this.selectedNode = node

        const rect = this.$refs.canvas.getBoundingClientRect()
        this.dragOffsetX = (e.clientX - rect.left - this.panX) / this.zoom - node.x
        this.dragOffsetY = (e.clientY - rect.top - this.panY) / this.zoom - node.y
      }

      this.hideContextMenu()
    },

    dragStart(e, type, subtype) {
      e.dataTransfer.setData('nodeType', type)
      e.dataTransfer.setData('nodeSubtype', subtype)
    },

    handleDrop(e) {
      const type = e.dataTransfer.getData('nodeType')
      const subtype = e.dataTransfer.getData('nodeSubtype')

      const rect = this.$refs.canvas.getBoundingClientRect()
      const x = (e.clientX - rect.left - this.panX) / this.zoom
      const y = (e.clientY - rect.top - this.panY) / this.zoom

      const snappedX = Math.round(x / this.gridSize) * this.gridSize
      const snappedY = Math.round(y / this.gridSize) * this.gridSize

      this.createNode(type, subtype, snappedX, snappedY)
    },

    createNode(type, subtype, x, y) {
      const id = `manual_${Date.now()}`

      const shapeMap = {
        'top': 'doubleoctagon',
        'intermediate': 'box',
        'basic': 'basic',
        'undeveloped': 'undeveloped',
        'initial': 'initial',
        'conditional': 'conditional',
        'OR': 'gate',
        'AND': 'gate',
        'XOR': 'gate',
        'INHIBIT': 'gate',
        'PAND': 'gate'
      }

      const node = {
        id,
        label: subtype === 'top' ? '新顶事件' :
               subtype === 'intermediate' ? '新中间事件' :
               subtype === 'basic' ? '新基本事件' :
               subtype === 'undeveloped' ? '未开展事件' :
               subtype === 'initial' ? '初始事件' :
               subtype === 'conditional' ? '条件事件' : subtype,
        type: type === 'gate' ? 'gate' : subtype,
        shape: shapeMap[subtype] || 'box',
        gateType: type === 'gate' ? subtype : null,
        x,
        y,
        parent: null,
        children: [],
        scale: 1.0
      }

      this.calculateNodeScale(node)

      this.parsedData.nodes[id] = node
      this.nodes.push(node)
      this.selectedNode = node
      this.selectedNodes = [node]

      this.saveHistory()
    },

    startPan(e) {
      if (this.isDraggingNode || this.draggedNode) {
        return
      }

      if (e.target.tagName === 'svg' || e.target.tagName === 'rect') {
        if (e.ctrlKey || e.metaKey) {
          this.startBoxSelect(e)
          return
        }

        this.isPanning = true
        this.lastMouseX = e.clientX
        this.lastMouseY = e.clientY
        this.hideContextMenu()
        this.selectedNodes = []
        this.selectedNode = null
      }
    },

    handleMouseMove(e) {
      // 已由全局事件处理
    },

    endPan() {
      // 已由全局事件处理
    },

    handleZoom(e) {
      const delta = e.deltaY > 0 ? 0.9 : 1.1
      this.zoom = Math.max(0.1, Math.min(3, this.zoom * delta))
    },

    startVResize(e) {
      this.isVResizing = true
      this.resizeStartX = e.clientX
      this.resizeStartLeft = this.leftWidth
    },

    startHResize(e) {
      this.isHResizing = true
      this.resizeStartY = e.clientY
      this.resizeStartTop = this.topHeight
    },

    showToast(message, type = 'info') {
      const toast = document.createElement('div')
      toast.textContent = message
      toast.style.cssText = `position:fixed;bottom:20px;right:20px;padding:10px 20px;border-radius:4px;z-index:10000;font-size:13px;font-weight:600;`
      if (type === 'success') toast.style.background = '#16a34a'
      else if (type === 'warn') toast.style.background = '#d97706'
      else toast.style.background = '#0D21A5'
      toast.style.color = '#fff'
      document.body.appendChild(toast)
      setTimeout(() => toast.remove(), 2000)
    }
  }
}
</script>

<style scoped src="./Workbench.css"></style>
<style scoped>
/* 全屏时仅保留故障树画布 */
.workbench-wrapper.is-canvas-fullscreen {
  background: #080914;
}

.workbench-wrapper.is-canvas-fullscreen > .workbench-ambient,
.workbench-wrapper.is-canvas-fullscreen > .ai-dialog-container,
.workbench-wrapper.is-canvas-fullscreen .floating-nav,
.workbench-wrapper.is-canvas-fullscreen .mobile-tab-bar,
.workbench-wrapper.is-canvas-fullscreen .content-stage {
  display: none !important;
}

.workbench-wrapper.is-canvas-fullscreen .container,
.workbench-wrapper.is-canvas-fullscreen .main-content {
  width: 100vw !important;
  max-width: none !important;
  height: 100vh !important;
  min-height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
}

.workbench-wrapper.is-canvas-fullscreen .canvas-stage {
  flex: 1 1 auto;
  width: 100vw !important;
  height: 100vh !important;
  min-height: 100vh !important;
  margin: 0 !important;
  border-radius: 0 !important;
}

.workbench-wrapper.is-canvas-fullscreen .panel-content.canvas-container {
  width: 100vw !important;
  height: 100vh !important;
  min-height: 100vh !important;
  border-radius: 0 !important;
  padding: 0 !important;
}

.workbench-wrapper.is-canvas-fullscreen .workspace-headline {
  position: absolute;
  top: 16px;
  left: 16px;
  right: 16px;
  z-index: 30;
  border-radius: 20px;
}

.workbench-wrapper.is-canvas-fullscreen .canvas {
  width: 100% !important;
  height: 100vh !important;
  min-height: 100vh !important;
  display: block;
}

.workbench-wrapper.is-canvas-fullscreen .context-menu {
  z-index: 40;
}

.fullscreen-toolbar-float {
  position: absolute;
  top: 88px;
  left: 16px;
  z-index: 32;
  pointer-events: none;
}

.fullscreen-toolbar-panel {
  width: 220px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  padding: 14px;
  border-radius: 20px;
  background: rgba(12, 18, 34, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(22px) saturate(1.4);
  -webkit-backdrop-filter: blur(22px) saturate(1.4);
  pointer-events: auto;
}

.fullscreen-toolbar-title {
  margin-bottom: 12px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.92);
}

.fullscreen-symbol-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.fullscreen-symbol-item {
  min-width: 0;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}

.fullscreen-symbol-item span {
  color: rgba(255, 255, 255, 0.9);
  font-size: 11px;
}

.fullscreen-symbol-item:hover {
  background: rgba(255, 255, 255, 0.14);
}
</style>
