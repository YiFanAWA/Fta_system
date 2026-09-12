<template>
  <div class="page-wrapper">
    <!-- 视频背景 -->
    <div class="video-background">
      <video autoplay muted loop playsinline class="bg-video">
        <source :src="bgVideoSrc" type="video/mp4">
      </video>
      <div class="video-overlay"></div>
    </div>
    <!-- 全页面固定环境光 - 简化版 -->
    <div class="page-ambient">
      <div class="pa-blob pa1"></div>
      <div class="pa-blob pa2"></div>
    </div>
    <nav class="navbar">
      <div class="navbar-brand">
        <svg viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"></path></svg>
        AI FTA System
      </div>
      <ul class="navbar-menu">
        <li @click="scrollToFeatures">功能特性</li>
        <li @click="scrollToHowto">使用流程</li>
        <li @click="scrollToCases">具体案例</li>
        <li @click="$emit('go-workbench')" class="nav-cta">立即开始</li>
      </ul>
    </nav>

    <div class="scroll-wrapper">
      <!-- HERO -->
      <div class="hero-container">
        <!-- 流动背景层 - 保留网格和纹理 -->
        <div class="hero-bg">
          <div class="hero-mesh-grid"></div>
          <div class="hero-noise"></div>
        </div>

        <!-- 左侧亚克力蒙版 - 位于视频上方、文字下方 -->
        <div class="hero-acrylic-panel"></div>

        <!-- 内容层 -->
        <div class="hero-inner">
          <!-- Left: Text -->
          <div class="hero-left">
            <h1 class="title">
              <span class="title-line">智能化</span>
              <span class="title-line title-accent">故障树</span>
              <span class="title-line">分析系统</span>
            </h1>
            <p class="subtitle">通过AI模型辅助优化故障树构建流程，从自然语言到结构化故障树，几秒内即可完成。</p>
            <div class="hero-actions">
              <button class="btn-start" @click="$emit('go-workbench')">
                <span class="btn-shimmer"></span>
                开始分析
                <svg viewBox="0 0 20 20" fill="none"><path d="M4 10h12M12 6l4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
              <button class="btn-ghost" @click="scrollToFeatures">了解更多</button>
            </div>
          </div>
        </div>

        <!-- Scroll indicator -->
        <div class="hero-scroll-hint">
          <div class="scroll-mouse"><div class="scroll-wheel"></div></div>
          <span>向下滚动探索</span>
        </div>
      </div>

      <!-- COLOR TRANSITION BRIDGE -->
      <div class="color-bridge">
        <div class="cb-glow cb-g1"></div>
        <div class="cb-glow cb-g2"></div>
        <div class="cb-glow cb-g3"></div>
      </div>

      <!-- PREVIEW SECTION -->
      <div class="preview-panel">
        <div class="preview-inner">
          <span class="section-eyebrow">实时演示</span>
          <h2 class="section-title">同步编辑，一键更改</h2>
          <p class="section-subtitle">跨多个框架与组件批量选中匹配图层，一次操作即可全部更新。</p>
          <div class="editor-mock">
            <div class="editor-topbar">
              <div class="dot dot-red"></div>
              <div class="dot dot-yellow"></div>
              <div class="dot dot-green"></div>
            </div>
            <div class="editor-body">
              <div class="editor-sidebar">
                <div class="sidebar-item active"><span class="s-dot"></span> Frame A</div>
                <div class="sidebar-item"><span class="s-dot"></span> Frame B</div>
                <div class="sidebar-item"><span class="s-dot"></span> Frame C</div>
                <div class="sidebar-item"><span class="s-dot"></span> Component Set</div>
                <div class="sidebar-item"><span class="s-dot"></span> Variant Group</div>
              </div>
              <div class="editor-canvas">
                <div class="multi-select-row">
                  <div class="frame-box selected">
                    <span class="edit-badge">EDITING</span>
                    <div class="frame-label">Frame A / Button</div>
                    <div class="ph" style="height:10px;width:60%"></div>
                    <div class="ph" style="height:28px"></div>
                    <div class="ph" style="height:10px;width:40%"></div>
                  </div>
                  <div class="frame-box selected">
                    <div class="frame-label">Frame B / Button</div>
                    <div class="ph" style="height:10px;width:60%"></div>
                    <div class="ph" style="height:28px"></div>
                    <div class="ph" style="height:10px;width:40%"></div>
                  </div>
                  <div class="frame-box selected">
                    <div class="frame-label">Frame C / Button</div>
                    <div class="ph" style="height:10px;width:60%"></div>
                    <div class="ph" style="height:28px"></div>
                    <div class="ph" style="height:10px;width:40%"></div>
                  </div>
                </div>
                <div class="multi-select-row">
                  <div class="frame-box"><div class="frame-label">Frame A / Card</div><div class="ph" style="height:48px"></div><div class="ph" style="height:10px;width:70%"></div></div>
                  <div class="frame-box"><div class="frame-label">Frame B / Card</div><div class="ph" style="height:48px"></div><div class="ph" style="height:10px;width:70%"></div></div>
                  <div class="frame-box"><div class="frame-label">Frame C / Card</div><div class="ph" style="height:48px"></div><div class="ph" style="height:10px;width:70%"></div></div>
                </div>
              </div>
            </div>
            <div class="toolbar-row">
              <button class="tb-btn active">多选编辑 开启</button>
              <button class="tb-btn">填充</button>
              <button class="tb-btn">描边</button>
              <button class="tb-btn">字体</button>
              <button class="tb-btn">间距</button>
            </div>
          </div>
        </div>
      </div>

      <!-- FEATURES -->
      <div id="features-section" class="features-section">
<span class="section-eyebrow">功能特性</span>
        <h2 class="section-title">专为大规模故障分析而生</h2>
        <p class="section-subtitle">构建、分析与理解故障树所需的一切，由AI全面驱动。</p>
        <div class="features-grid">
          <div class="feature-card" v-for="feature in features" :key="feature.title">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" v-html="feature.icon"></svg>
            </div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.desc }}</p>
          </div>
        </div>
      </div>


      <!-- 具体案例 - 椭圆无限滚动轮播图 -->
      <div id="cases-section" class="cases-section">
        <div class="cases-header">
          <span class="section-eyebrow">具体案例</span>
          <h2 class="section-title">案例展示</h2>
          <p class="section-subtitle">通过真实故障案例，展示 AI 故障树分析的强大能力。</p>
        </div>
        <div id="banner">
          <div class="img-list img-wrapper" ref="imgList" id="imgList">
            <div class="img-box" data-index="0">
              <div class="info"><h3>设备故障诊断</h3></div>
              <img :src="carouselItems[0].image" alt="设备故障诊断">
            </div>
            <div class="img-box" data-index="1">
              <div class="info"><h3>系统安全评估</h3></div>
              <img :src="carouselItems[1].image" alt="系统安全评估">
            </div>
            <div class="img-box" data-index="2">
              <div class="info"><h3>故障模式分析</h3></div>
              <img :src="carouselItems[2].image" alt="故障模式分析">
            </div>
            <div class="img-box" data-index="3">
              <div class="info"><h3>风险评估报告</h3></div>
              <img :src="carouselItems[3].image" alt="风险评估报告">
            </div>
            <div class="img-box" data-index="4">
              <div class="info"><h3>知识图谱构建</h3></div>
              <img :src="carouselItems[4].image" alt="知识图谱构建">
            </div>
            <div class="img-box" id="last-img-box" data-index="5">
              <div class="info"><h3>预测性维护</h3></div>
              <img :src="carouselItems[5].image" alt="预测性维护">
            </div>
          </div>
        </div>
        <div class="btn-group" ref="btnGroup" id="btnGroup">
          <button class="last btn" id="lastBtn">
            <svg t="1686471404424" class="icon left" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2373" width="128" height="128">
              <path d="M862.485 481.154H234.126l203.3-203.3c12.497-12.497 12.497-32.758 0-45.255s-32.758-12.497-45.255 0L135.397 489.373c-12.497 12.497-12.497 32.758 0 45.254l256.774 256.775c6.249 6.248 14.438 9.372 22.627 9.372s16.379-3.124 22.627-9.372c12.497-12.497 12.497-32.759 0-45.255l-203.3-203.301h628.36c17.036 0 30.846-13.81 30.846-30.846s-13.81-30.846-30.846-30.846z" fill="" p-id="2374"></path>
            </svg>
          </button>
          <button class="next btn" id="nextBtn">
            <svg t="1686471404424" class="icon right" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2373" width="128" height="128">
              <path d="M862.485 481.154H234.126l203.3-203.3c12.497-12.497 12.497-32.758 0-45.255s-32.758-12.497-45.255 0L135.397 489.373c-12.497 12.497-12.497 32.758 0 45.254l256.774 256.775c6.249 6.248 14.438 9.372 22.627 9.372s16.379-3.124 22.627-9.372c12.497-12.497 12.497-32.759 0-45.255l-203.3-203.301h628.36c17.036 0 30.846-13.81 30.846-30.846s-13.81-30.846-30.846-30.846z" fill="" p-id="2374"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- HOW IT WORKS -->
      <div id="howto-section" class="howto-section">
        <div class="howto-inner">
          <div class="howto-header">
            <span class="section-eyebrow">使用流程</span>
            <h2 class="section-title">三步完成故障树分析</h2>
            <p class="section-subtitle">无需复杂配置，粘贴文本、AI 生成、在线编辑，即刻输出专业故障树。</p>
          </div>
          <div class="howto-timeline">
            <div class="htl-step" v-for="step in steps" :key="step.num">
              <div class="htl-num">{{ step.num }}</div>
              <div class="htl-connector"></div>
              <div class="htl-content">
                <h4 class="htl-title">{{ step.title }}</h4>
                <p class="htl-desc">{{ step.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CTA -->
      <div class="cta-section">
        <span class="section-eyebrow">立即体验</span>
        <h2 class="cta-title">让 AI 替你构建故障树</h2>
        <p class="cta-desc">无论是设备维修手册、工程报告还是原始故障描述，粘贴文本即可一键生成专业故障树，告别繁琐的手动建模。</p>
        <div class="cta-buttons">
          <a href="#" class="btn-primary" @click.prevent="$emit('go-workbench')">立即开始分析 &rarr;</a>
          <a href="#" class="btn-secondary">查看使用流程</a>
        </div>
      </div>

      <!-- FOOTER -->
      <footer class="footer">
        <div class="footer-brand">
          <svg viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"></path></svg>
          AI FTA System
        </div>
        <ul class="footer-links">
          <li>功能特性</li>
          <li>文档</li>
          <li>博客</li>
          <li>隐私政策</li>
        </ul>
        <span class="footer-copy">&copy; 2026 AI FTA System. 保留所有权利。</span>
      </footer>

        </div>
      </div>

</template>

<script>
import bgVideoSrc from '@/assets/93aadaa25f6026d923c1b5b6f5e2bd72_raw.mp4'
import caseImg1 from '@/assets/1c8d785d848f43b480680c760b72157f.jpg'
import caseImg2 from '@/assets/2437a1ea920965281edb98745f7faf23.jpg'
import caseImg3 from '@/assets/2a007e56a71a5557c2405b7a3f2206e7.png'
import caseImg4 from '@/assets/e91105d17bd581b3297378b08e101868.png'

export default {
  name: 'IndexLight',
  emits: ['start', 'go-workbench'],

  data() {
    return {
      bgVideoSrc,
      // ===== Landing page data =====
      carouselItems: [
        { id: 0, title: '设备故障诊断', image: caseImg1 },
        { id: 1, title: '系统安全评估', image: caseImg2 },
        { id: 2, title: '故障模式分析', image: caseImg3 },
        { id: 3, title: '风险评估报告', image: caseImg4 },
        { id: 4, title: '知识图谱构建', image: caseImg2 },
        { id: 5, title: '预测性维护', image: caseImg3 }
      ],
      // ===== Landing page data =====
      features: [
        {
          title: 'AI 一键抽取',
          desc: '粘贴原始故障手册或维修文本，AI 自动识别故障模式、原因与影响，直接生成结构化故障树，无需手动整理。',
          icon: '<circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/>'
        },
        {
          title: '可视化故障树编辑',
          desc: '拖拽逻辑门与事件节点，在画布上直接搭建或修改故障树结构，支持与门、或门、异或门、禁止门等全部 IEC 标准符号。',
          icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>'
        },
        {
          title: 'DOT 格式导入 / 导出',
          desc: '完整支持 Graphviz DOT 格式的解析与导出，方便与现有工具链集成，也可将分析结果存档留存。',
          icon: '<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
        },
        {
          title: '知识图谱持久化',
          desc: '抽取的故障节点与关联关系可一键写入 Neo4j 知识图谱，沉淀组织知识，支持跨项目复用与深度查询。',
          icon: '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>'
        },
        {
          title: '多布局自动排列',
          desc: '内置层级、水平等多种自动布局算法，大型故障树一键整理，节点不再杂乱重叠，结构一目了然。',
          icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'
        },
        {
          title: '完整历史记录',
          desc: '每一步编辑操作均可撤销 / 重做，支持多级历史回溯，放心探索分析方案，随时还原到任意状态。',
          icon: '<path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/>'
        }
      ],
      steps: [
        {
          num: 1,
          title: '输入原始文本',
          desc: '将故障手册、维修报告或任意描述性文本粘贴到「生产输入」区域，填写系统名称与顶事件，一键触发 AI 抽取。'
        },
        {
          num: 2,
          title: 'AI 自动生成故障树',
          desc: 'AI 模型自动识别故障模式、原因与逻辑关系，生成标准 DOT 格式故障树并即时渲染到可视化画布，无需任何手动建模。'
        },
        {
          num: 3,
          title: '编辑、导出与沉淀知识',
          desc: '在画布上拖拽节点、调整逻辑门、自动排版，完成后导出 DOT 文件存档，或一键写入 Neo4j 知识图谱供后续复用。'
        }
      ],
    }

  },

  mounted() {
    // 初始化轮播图 - 纯JavaScript实现
    this.initCarouselJS()
  },

  methods: {
    // ===== Carousel methods - 纯JS实现无限滚动 =====

    initCarouselJS() {
      const imgListOne = document.getElementById('imgList')
      const btnGroup = document.getElementById('btnGroup')
      const lastBtn = document.getElementById('lastBtn')
      const nextBtn = document.getElementById('nextBtn')

      if (!imgListOne || !lastBtn || !nextBtn) return

      // 防止重复初始化
      if (imgListOne.dataset.initialized === 'true') return
      imgListOne.dataset.initialized = 'true'

      // 获取图片类数组，并将其转化为数组
      let imgBoxList = Array.prototype.slice.call(imgListOne.querySelectorAll('.img-box'))
      const imgBoxCount = imgBoxList.length
      const lastImgBox = document.getElementById('last-img-box')

      // 获取post-spacing和post-size的值
      const postSpacing = 1.78
      const postSize = 25

      // 根据图片的数量动态获取img-box的宽度
      const imgBoxLength = postSize + postSpacing

      let index = 0
      let timer = null
      let animationTime = 0.5

      // 初始化数组中元素的顺序，将最后一张图片放在第一位与html部分图片展示位置一致
      imgBoxList.unshift(imgBoxList.pop())

      // 设置imgListOne动画时间
      imgListOne.style.transition = animationTime + 's ease'

      // 设置按钮出现时间
      setTimeout(function() {
        if (btnGroup) {
          btnGroup.style.opacity = '1'
          btnGroup.style.bottom = '5%'
        }
      }, animationTime * 1000)

      // 点击事件
      function cilckFun(flag) {
        // 下一页 next
        if (flag == 'next') {
          index--
          // 因为右边没有显示的图片比较多，所以可以直接先整体向左移动
          imgListOne.style.left = imgBoxLength * index + 'vw'

          setTimeout(function() {
            imgListOne.style.transition = 'none'

            // 当点击下一个累计达到图片数量时，相当于要回到原点，则重置变量和位置
            if (Math.abs(index) == imgBoxCount) {
              index = 0
              imgListOne.style.left = 0
              imgBoxList.forEach(item => {
                if (item.id == 'last-img-box') {
                  item.style.transform = 'translateX(-160.68vw)'
                } else {
                  item.style.transform = 'none'
                }
              })
            } else {
              // 当第一张图片为last-img-box时，说明已经跑完了一轮，则将其放在最后的位置，初始状态其在-160.68vw
              if (imgBoxList[0].id == 'last-img-box') {
                lastImgBox.style.transition = 'none'
                lastImgBox.style.transform = 'translateX(0px)'
              } else if (index >= 0) {
                /*
                  这种情况是为了解决在点击完last，再点击next时造成的bug问题，其实就是回退，在点击last之前
                  没有加transform属性，点击last以后则添加了transform属性，再次点击next按钮后应该不加transform
                */
                imgBoxList[0].style.transform = 'none'
              } else {
                // 正常情况下，点击next，则将最左侧的图片移到最右侧
                imgBoxList[0].style.transform = 'translateX(160.68vw)'
              }
            }

            // 模拟移动情况，将最左侧的图片（元素）移动到最右侧
            imgBoxList.push(imgBoxList.shift())

            // 恢复动画
            imgListOne.style.transition = animationTime + 's ease'
          }, animationTime * 1000)

        } else {
          // 上一页 last
          index++

          // 模拟移动情况，把最右侧的图片（元素）移动到最左侧
          imgBoxList.unshift(imgBoxList.pop())

          // 因为左侧图片只会有一张，所以需要先移动图片到左侧，再进行imgListOne的移动
          if (imgBoxList[0].id == 'last-img-box' && index != 0) {
            // 当第一张图片为last-img-box时，说明已经跑完了一轮，此时相对于一开始的位置-321.36vw
            imgBoxList[0].style.transform = 'translateX(-321.36vw)'
          } else if (index < 0) {
            // 这种情况与点击next按钮出现的回退现象一样
            imgBoxList[0].style.transform = 'none'
          } else {
            // 正常情况下，点击last，则将最右侧的图片移到最左侧
            imgBoxList[0].style.transform = 'translateX(-160.68vw)'
          }

          imgListOne.style.left = imgBoxLength * index + 'vw'
          if (lastImgBox) lastImgBox.style.transition = 'none'

          // 当点击下一个累计达到图片数量时，相当于要回到原点，则重置变量和位置
          if (Math.abs(index) == imgBoxCount) {
            index = 0
            setTimeout(function() {
              imgListOne.style.transition = 'none'
              imgListOne.style.left = 0
              imgBoxList.forEach(item => {
                if (item.id == 'last-img-box') {
                  item.style.transform = 'translateX(-160.68vw)'
                } else {
                  item.style.transform = 'none'
                }
              })
              imgListOne.style.transition = animationTime + 's ease'
            }, animationTime * 1000)
          }
        }
      }

      // 节流函数
      function throttle(fn, delay) {
        return function() {
          if (timer) {
            return
          }
          fn.apply(this, arguments)
          timer = setTimeout(() => {
            timer = null
          }, delay)
        }
      }

      nextBtn.onclick = throttle(() => cilckFun('next'), animationTime * 1000)
      lastBtn.onclick = throttle(() => cilckFun('last'), animationTime * 1000)
    },

    scrollToFeatures() {
      const el = document.getElementById('features-section')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },

    scrollToHowto() {
      const el = document.getElementById('howto-section')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },

    scrollToCases() {
      const el = document.getElementById('cases-section')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },


    showToast(msg, type = 'info') {
      const colors = {
        info: 'rgba(107,140,0,0.92)',
        warn: 'rgba(200,80,0,0.92)',
        success: 'rgba(30,140,80,0.92)'
      }
      const toast = document.createElement('div')
      toast.textContent = msg
      toast.style.cssText = `position:fixed;top:88px;left:50%;transform:translateX(-50%) translateY(-8px);opacity:0;background:${colors[type] || colors.info};color:#fff;padding:10px 22px;border-radius:8px;z-index:99999;font-size:14px;font-weight:600;letter-spacing:0.02em;box-shadow:0 4px 20px rgba(0,0,0,0.18);backdrop-filter:blur(8px);transition:opacity 0.2s,transform 0.2s;pointer-events:none;`
      document.body.appendChild(toast)
      requestAnimationFrame(() => {
        toast.style.opacity = '1'
        toast.style.transform = 'translateX(-50%) translateY(0)'
      })
      setTimeout(() => {
        toast.style.opacity = '0'
        toast.style.transform = 'translateX(-50%) translateY(-8px)'
        setTimeout(() => toast.remove(), 220)
      }, 2200)
    },


  }
}
</script>


<style scoped>
/* CSS Variables & Base — Video Background Edition · Dark Cinematic Theme */
.page-wrapper {
  --bg: #0a0a0f;
  --bg-alt: #12121a;
  --bg-card: rgba(255,255,255,0.08);
  --bg-glass: rgba(20,20,35,0.60);
  --bg-glass-dark: rgba(5,5,10,0.80);
  --border: rgba(255,255,255,0.08);
  --border-acc: rgba(255,255,255,0.15);
  --border-glass: rgba(255,255,255,0.20);
  --text: #ffffff;
  --text-muted: rgba(255,255,255,0.75);
  --text-light: rgba(255,255,255,0.50);
  --acc: #6366f1;
  --acc-light: #818cf8;
  --acc-bg: rgba(99,102,241,0.20);
  --acc-hover: #a5b4fc;
  --neon: #22d3ee;
  --neon-bright: #67e8f9;
  --neon-soft: #a5f3fc;
  --neon-dark: #0891b2;
  --azure: #6366f1;
  --azure-light: #818cf8;
  --azure-pale: rgba(99,102,241,0.30);
  --azure-ultra: #a5b4fc;
  --azure-glow: rgba(99,102,241,0.40);
  --frost: rgba(255,255,255,0.05);
  --glass: rgba(255,255,255,0.08);
  --glass-azure: rgba(99,102,241,0.15);
  --glass-border: rgba(255,255,255,0.15);
  --glass-shine: rgba(255,255,255,0.30);
  --glass-inner: inset 0 1px 0 rgba(255,255,255,0.15), inset 0 -1px 0 rgba(0,0,0,0.20);
  --shadow-sm: 0 2px 20px rgba(0,0,0,0.30), 0 1px 4px rgba(0,0,0,0.20);
  --shadow-md: 0 8px 52px rgba(0,0,0,0.40), 0 2px 12px rgba(0,0,0,0.30);
  --shadow-lg: 0 32px 100px rgba(0,0,0,0.50), 0 8px 28px rgba(0,0,0,0.40);
  --shadow-glass: 0 14px 60px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.15);
  --shadow-neon: 0 6px 36px rgba(34,211,238,0.35);
  --shadow-azure: 0 8px 44px rgba(99,102,241,0.40);
  --radius-sm: 16px;
  --radius-md: 24px;
  --radius-lg: 34px;
  --radius-xl: 48px;
  background: #0a0a0f;
  color: var(--text);
  font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans GB', -apple-system, sans-serif;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  position: relative;
  isolation: isolate;
}

/* ===== VIDEO BACKGROUND ===== */
.video-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}
.bg-video {
  position: absolute;
  top: 50%;
  left: 50%;
  min-width: 100%;
  min-height: 100%;
  width: auto;
  height: auto;
  transform: translate(-50%, -50%);
  object-fit: cover;
}
.video-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(10,10,15,0.3) 0%,
    rgba(10,10,15,0.1) 40%,
    rgba(10,10,15,0.2) 60%,
    rgba(10,10,15,0.5) 100%
  );
  backdrop-filter: blur(0px);
}


/* ===== FULL-PAGE AMBIENT LIGHT SYSTEM - Video Edition ===== */
.page-ambient {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  overflow: hidden;
}
.pa-blob {
  position: absolute;
  border-radius: 50%;
  will-change: transform;
  animation-fill-mode: both;
}
/* Cyan glow — top-left, drifts slowly */
.pa1 {
  width: 600px; height: 600px;
  background: radial-gradient(ellipse, rgba(34,211,238,0.25) 0%, transparent 65%);
  top: -10%; left: -10%;
  filter: blur(80px);
  animation: pa-drift1 22s ease-in-out infinite;
}
/* Indigo glow — bottom-right */
.pa2 {
  width: 500px; height: 500px;
  background: radial-gradient(ellipse, rgba(99,102,241,0.20) 0%, transparent 65%);
  bottom: -5%; right: -5%;
  filter: blur(100px);
  animation: pa-drift2 28s ease-in-out infinite;
  animation-delay: -8s;
}
@keyframes pa-drift1 {
  0%,100% { transform: translate(0,0) scale(1); }
  30%     { transform: translate(80px, 120px) scale(1.08); }
  60%     { transform: translate(-40px, 200px) scale(0.94); }
}
@keyframes pa-drift2 {
  0%,100% { transform: translate(0,0) scale(1); }
  35%     { transform: translate(-120px, 80px) scale(1.10); }
  70%     { transform: translate(-60px, 160px) scale(0.92); }
}

/* NAV - Dark Glass Style */
.navbar {
  position: fixed;
  top: 20px; left: 50%; right: auto;
  transform: translateX(-50%);
  width: calc(100% - 64px);
  max-width: 1160px;
  height: 58px;
  background: rgba(20,20,30,0.60);
  backdrop-filter: blur(20px) saturate(1.8);
  -webkit-backdrop-filter: blur(20px) saturate(1.8);
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow:
    0 8px 48px rgba(0,0,0,0.30),
    0 2px 10px rgba(0,0,0,0.20),
    inset 0 1px 0 rgba(255,255,255,0.15),
    inset 0 -1px 0 rgba(0,0,0,0.20);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 28px;
  z-index: 1000;
  border-radius: 26px;
  transition: all 0.3s ease;
}
.navbar-brand {
  display: flex; align-items: center; gap: 10px;
  font-size: 16px; color: #ffffff; font-weight: 800; cursor: pointer; letter-spacing: -0.3px;
}
.navbar-brand svg { width:22px; height:22px; stroke:#22d3ee; stroke-width:2; fill:none; }
.navbar-menu { display:flex; gap:2px; list-style:none; align-items:center; }
.navbar-menu li { color:rgba(255,255,255,0.70); cursor:pointer; font-size:14px; font-weight:600; padding:7px 16px; border-radius:12px; transition:all 0.20s; letter-spacing:-0.1px; }
.navbar-menu li:hover { color:#22d3ee; background: rgba(34,211,238,0.12); }
.navbar-menu li.nav-cta:hover { background: #6366f1; color: #ffffff; }
.navbar-menu .nav-cta {
  position: relative;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  padding: 8px 20px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: -0.1px;
  box-shadow: 0 4px 16px rgba(99,102,241,0.40), inset 0 1px 0 rgba(255,255,255,0.25);
  transition: all 0.22s cubic-bezier(.4,0,.2,1);
  overflow: hidden;
  border: none;
}
.navbar-menu .nav-cta::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 35%, rgba(255,255,255,0.25) 50%, transparent 65%);
  background-size: 250% auto;
  background-position: 200% center;
  transition: background-position 0.5s ease;
  border-radius: inherit;
}
.navbar-menu .nav-cta:hover {
  background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
  box-shadow: 0 6px 24px rgba(99,102,241,0.55);
  transform: translateY(-1px);
  color: #ffffff;
}
.navbar-menu .nav-cta:hover::before {
  background-position: -20% center;
}
.navbar-menu .nav-cta:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(99,102,241,0.40);
}
.scroll-wrapper { padding-top: 0; position: relative; z-index: 2; }
.scroll-wrapper > *:not(.hero-container) { position: relative; z-index: 2; }

/* HERO - Full screen immersive with video */
.hero-container {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  background: transparent;
}
.hero-container::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 220px;
  background: linear-gradient(to bottom, transparent 0%, rgba(10,10,15,0.4) 60%, rgba(10,10,15,0.95) 100%);
  pointer-events: none;
  z-index: 3;
}

/* Animated background - Video edition (simplified) */
.hero-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  isolation: isolate;
  overflow: hidden;
}

/* Subtle dot-grid overlay - Dark theme */
.hero-mesh-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 100% 100% at 50% 50%, black 30%, transparent 100%);
  -webkit-mask-image: radial-gradient(ellipse 100% 100% at 50% 50%, black 30%, transparent 100%);
  pointer-events: none;
  animation: grid-drift 20s ease-in-out infinite alternate;
}
@keyframes grid-drift {
  from { transform: translate(0,0); }
  to   { transform: translate(16px, 12px); }
}

/* Noise texture overlay */
.hero-noise {
  position: absolute;
  inset: 0;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-size: 200px 200px;
  pointer-events: none;
}

/* Hero inner layout */
.hero-inner {
  position: relative;
  z-index: 3;
  width: 100%; max-width: 1300px;
  margin: 0 auto; padding: 0 60px;
  display: flex; align-items: center;
  justify-content: space-between; gap: 60px;
}
.hero-left {
  width: 38.2%; /* 黄金分割比例 */
  max-width: 520px;
  animation: hero-fade-in 1s cubic-bezier(.4,0,.2,1) both;
  padding: 48px 42px;
}

/* 左侧亚克力蒙版 - 类似导航栏玻璃质感 */
.hero-acrylic-panel {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 42%;
  max-width: 580px;
  z-index: 2;
  pointer-events: none;
  background: rgba(20,20,30,0.45);
  backdrop-filter: blur(24px) saturate(1.6) brightness(1.05);
  -webkit-backdrop-filter: blur(24px) saturate(1.6) brightness(1.05);
  border-right: 1px solid rgba(255,255,255,0.10);
  box-shadow:
    20px 0 80px rgba(0,0,0,0.30),
    inset 0 1px 0 rgba(255,255,255,0.08),
    inset 0 -1px 0 rgba(0,0,0,0.15);
  mask-image: linear-gradient(to right, black 70%, transparent 100%);
  -webkit-mask-image: linear-gradient(to right, black 70%, transparent 100%);
}

.badge-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #22d3ee; box-shadow: 0 0 10px rgba(34,211,238,0.90);
  animation: badge-pulse 2s ease-in-out infinite;
}
@keyframes badge-pulse {
  0%,100% { opacity:1; box-shadow:0 0 6px rgba(34,211,238,0.85); }
  50%     { opacity:0.65; box-shadow:0 0 20px rgba(34,211,238,1.00); }
}

.title {
  font-size: 76px; font-weight: 900; line-height: 1.05;
  margin-bottom: 24px; letter-spacing: -1px;
  color: #ffffff;
  display: flex; flex-direction: column; gap: 4px;
  font-family: 'Noto Serif SC', 'Source Han Serif CN', 'STSong', serif;
  text-shadow: 0 2px 40px rgba(0,0,0,0.30);
}
.title-line {
  display: block;
  animation: line-reveal 0.9s cubic-bezier(.4,0,.2,1) both;
}
.title-line:nth-child(2) { animation-delay: 0.12s; }
.title-line:nth-child(3) { animation-delay: 0.24s; }
@keyframes line-reveal {
  from { opacity:0; transform:translateY(20px); }
  to   { opacity:1; transform:translateY(0); }
}
.title-accent {
  background: linear-gradient(118deg, #6366f1 0%, #8b5cf6 18%, #a78bfa 36%, #22d3ee 55%, #67e8f9 70%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  background-size: 300% auto;
  animation: shimmer-text 7s linear infinite;
}
@keyframes shimmer-text {
  0%   { background-position: 0% center; }
  100% { background-position: 300% center; }
}

.subtitle {
  font-size: 17px; line-height: 1.75;
  color: rgba(255,255,255,0.70);
  margin-bottom: 40px; font-weight: 400; letter-spacing: 0;
  animation: hero-fade-in 1s 0.3s cubic-bezier(.4,0,.2,1) both;
}
.hero-actions {
  display: flex; gap: 12px; align-items: center;
  margin-bottom: 48px;
  animation: hero-fade-in 1s 0.4s cubic-bezier(.4,0,.2,1) both;
}

.btn-start {
  position: relative; overflow: hidden;
  display: inline-flex; align-items: center; gap: 8px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #FFFFFF; padding: 15px 30px;
  border: 1px solid rgba(255,255,255,0.20);
  border-radius: 18px;
  font-size: 15px; font-weight: 700; cursor: pointer;
  transition: all 0.24s ease; text-decoration: none;
  box-shadow: 0 10px 32px rgba(99,102,241,0.45), inset 0 1.5px 0 rgba(255,255,255,0.25), inset 0 -1px 0 rgba(0,0,0,0.10);
  letter-spacing: -0.1px;
}
.btn-start svg { width:16px; height:16px; transition:transform 0.22s; }
.btn-start:hover { transform:translateY(-2px); box-shadow:0 16px 44px rgba(99,102,241,0.55), inset 0 1.5px 0 rgba(255,255,255,0.30); background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%); }
.btn-start:hover svg { transform:translateX(3px); }
.btn-shimmer {
  position: absolute; top:0; left:-100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
  animation: shimmer-btn 3s ease-in-out infinite;
  pointer-events: none;
}
@keyframes shimmer-btn {
  0%  { left:-100%; }
  60% { left:150%; }
  100%{ left:150%; }
}
.btn-ghost {
  display: inline-flex; align-items: center;
  padding: 15px 30px; border-radius: 18px;
  font-size: 15px; font-weight: 600; cursor: pointer;
  text-decoration: none; color: #ffffff;
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.20);
  backdrop-filter: blur(16px) saturate(1.8);
  -webkit-backdrop-filter: blur(16px) saturate(1.8);
  transition: all 0.24s;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15), inset 0 2px 0 rgba(255,255,255,0.12), inset 0 -1px 0 rgba(0,0,0,0.20);
}
.btn-ghost:hover {
  color: #ffffff; background: rgba(255,255,255,0.18);
  transform: translateY(-2px);
  box-shadow: 0 10px 32px rgba(0,0,0,0.25), inset 0 2px 0 rgba(255,255,255,0.18);
}

/* Trust bar */
.hero-trust { animation: hero-fade-in 1s 0.55s cubic-bezier(.4,0,.2,1) both; }
.hero-trust-label { display:block; font-size:11px; color:rgba(255,255,255,0.50); letter-spacing:1px; text-transform:uppercase; margin-bottom:10px; font-weight:600; }
.hero-trust-tags { display:flex; gap:8px; flex-wrap:wrap; }
.trust-tag {
  padding:5px 14px; border-radius:100px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.85); font-size:12px; font-weight:600;
  transition:all 0.2s;
  backdrop-filter: blur(12px);
  box-shadow: 0 2px 10px rgba(0,0,0,0.15), inset 0 1.5px 0 rgba(255,255,255,0.10);
}
.trust-tag:hover { background: rgba(255,255,255,0.15); color:#ffffff; box-shadow: 0 4px 16px rgba(0,0,0,0.25), inset 0 1.5px 0 rgba(255,255,255,0.15); }

/* Right column */
.hero-right {
  flex: 1; position: relative;
  height: 480px; min-width: 420px;
  animation: hero-fade-in 1s 0.2s cubic-bezier(.4,0,.2,1) both;
}
.hero-card {
  background: rgba(20,20,30,0.50);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 28px;
  backdrop-filter: blur(28px) saturate(1.8) brightness(1.04);
  -webkit-backdrop-filter: blur(28px) saturate(1.8) brightness(1.04);
  box-shadow:
    0 20px 60px rgba(0,0,0,0.40),
    0 4px 16px rgba(0,0,0,0.25),
    inset 0 2px 0 rgba(255,255,255,0.12),
    inset 0 -1px 0 rgba(0,0,0,0.25);
}
.hc-main {
  position: absolute; top:0; left:0; right:0;
  animation: card-float 6s ease-in-out infinite;
}
@keyframes card-float {
  0%,100% { transform:translateY(0px) rotate(0deg); }
  50%     { transform:translateY(-10px) rotate(0.4deg); }
}
.hc-topbar { display:flex; align-items:center; gap:6px; padding:12px 16px; border-bottom:1px solid rgba(255,255,255,0.10); background:rgba(255,255,255,0.05); border-radius:20px 20px 0 0; }
.hc-dot { width:10px; height:10px; border-radius:50%; }
.hc-dot.r { background:#f87171; } .hc-dot.y { background:#fbbf24; } .hc-dot.g { background:#34d399; }
.hc-title { margin-left:8px; font-size:12px; color:rgba(255,255,255,0.50); font-weight:600; letter-spacing:0.5px; }
.hc-body { padding:20px; }
.hc-tree { display:flex; flex-direction:column; align-items:center; gap:8px; }
.hc-row { display:flex; gap:12px; justify-content:center; align-items:center; }
.hc-node { padding:6px 14px; border-radius:10px; font-size:11px; font-weight:700; white-space:nowrap; }
.hcn-root { background:rgba(99,102,241,0.25); border:1px solid rgba(99,102,241,0.40); color:#a5b4fc; }
.hcn-mid { background:rgba(34,211,238,0.15); border:1px solid rgba(34,211,238,0.30); color:#67e8f9; }
.hcn-leaf { background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); color:rgba(255,255,255,0.85); }
.hcn-acc { background:rgba(139,92,246,0.25); border:1px solid rgba(139,92,246,0.40); color:#c4b5fd; animation:node-pulse 2.5s ease-in-out infinite; }
@keyframes node-pulse {
  0%,100% { box-shadow:0 0 0 rgba(139,92,246,0); }
  50%     { box-shadow:0 0 14px rgba(139,92,246,0.45); }
}
.hc-gate { padding:4px 12px; border-radius:100px; font-size:10px; font-weight:700; letter-spacing:0.5px; background:rgba(99,102,241,0.20); border:1px solid rgba(99,102,241,0.35); color:#a5b4fc; }
.hc-mini { position:absolute; display:flex; align-items:center; gap:10px; padding:12px 16px; border-radius:16px; white-space:nowrap; }
.hc-mini-1 { bottom:60px; left:-30px; animation:card-float 7s 1s ease-in-out infinite; }
.hc-mini-2 { bottom:0; right:-20px; animation:card-float 5s 0.5s ease-in-out infinite; }
.hc-mini-3 { top:50%; right:-35px; transform:translateY(-50%); animation:card-float 8s 2s ease-in-out infinite; }
.hcm-icon { font-size:18px; }
.hcm-val { display:block; font-size:16px; font-weight:800; color:#ffffff; line-height:1; }
.hcm-label { display:block; font-size:10px; color:rgba(255,255,255,0.50); margin-top:2px; letter-spacing:0.3px; }
.hcm-live { color:#22d3ee !important; }
.hcm-live::before { content:''; display:inline-block; width:6px; height:6px; border-radius:50%; background:#22d3ee; margin-right:5px; animation:badge-pulse 1.5s infinite; }

/* Scroll hint */
.hero-scroll-hint { position:absolute; bottom:32px; left:50%; transform:translateX(-50%); display:flex; flex-direction:column; align-items:center; gap:8px; color:rgba(255,255,255,0.45); font-size:11px; letter-spacing:1px; text-transform:uppercase; z-index:5; animation:hero-fade-in 2s 1s both; font-weight:600; }
.scroll-mouse { width:22px; height:34px; border:1.5px solid rgba(255,255,255,0.20); border-radius:11px; display:flex; justify-content:center; padding-top:5px; }
.scroll-wheel { width:3px; height:6px; background:#22d3ee; border-radius:2px; animation:scroll-anim 2s ease-in-out infinite; }
@keyframes scroll-anim { 0% { transform:translateY(0); opacity:1; } 100% { transform:translateY(8px); opacity:0; } }
@keyframes hero-fade-in { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }

/* PREVIEW */
.preview-panel {
  position:relative; width:100%; padding:100px 100px;
  background: rgba(15,15,25,0.60);
  overflow:hidden;
  border-top: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(28px) saturate(1.8);
  -webkit-backdrop-filter: blur(28px) saturate(1.8);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.10), inset 0 -1px 0 rgba(0,0,0,0.20);
}
.preview-panel::before { content:''; position:absolute; top:-200px; left:50%; transform:translateX(-50%); width:800px; height:350px; border-radius:50%; background: radial-gradient(ellipse, rgba(99,102,241,0.20) 0%, rgba(34,211,238,0.08) 50%, transparent 70%); pointer-events:none; }
.preview-panel::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg, transparent 0%, rgba(99,102,241,0.60) 25%, rgba(34,211,238,0.50) 50%, rgba(139,92,246,0.45) 75%, transparent 100%); }
.preview-inner { max-width:1200px; margin:0 auto; position:relative; z-index:1; }

/* COLOR BRIDGE hidden — full dark theme */
.color-bridge { display:none; }

/* ===== COLOR TRANSITION BRIDGE ===== */
.color-bridge {
  position: relative;
  width: 100%;
  height: 300px;
  margin-top: -1px;
  background: linear-gradient(180deg,
    #06080a 0%,
    #0d120a 15%,
    #16200f 30%,
    #233318 46%,
    #3d5425 60%,
    #8aaa60 74%,
    #c8d4a8 86%,
    #e2e8d4 93%,
    #f2f3ee 100%);
  overflow: hidden;
  z-index: 1;
}
.cb-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  pointer-events: none;
  will-change: transform, opacity;
}
.cb-g1 {
  width: 520px; height: 280px;
  background: radial-gradient(ellipse, rgba(0,200,190,0.30) 0%, transparent 70%);
  top: 5%; left: -5%;
  animation: cbglow1 11s ease-in-out infinite;
}
.cb-g2 {
  width: 440px; height: 240px;
  background: radial-gradient(ellipse, rgba(120,50,255,0.22) 0%, transparent 70%);
  top: 8%; right: 8%;
  animation: cbglow2 14s ease-in-out infinite;
}
.cb-g3 {
  width: 400px; height: 220px;
  background: radial-gradient(ellipse, rgba(140,210,0,0.25) 0%, transparent 70%);
  top: 35%; left: 36%;
  animation: cbglow3 9s ease-in-out infinite;
}
@keyframes cbglow1 {
  0%,100% { transform: translate(0,0) scale(1); opacity:0.9; }
  50%     { transform: translate(60px,30px) scale(1.12); opacity:1; }
}
@keyframes cbglow2 {
  0%,100% { transform: translate(0,0) scale(1); opacity:0.8; }
  50%     { transform: translate(-50px,20px) scale(1.10); opacity:1; }
}
@keyframes cbglow3 {
  0%,100% { transform: translate(0,0) scale(1); opacity:0.85; }
  50%     { transform: translate(30px,-20px) scale(1.15); opacity:1; }
}
.section-eyebrow {
  font-size:11px; letter-spacing:2.5px; text-transform:uppercase;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 55%, #22d3ee 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom:14px; font-weight:800; display:block;
}
.section-title { font-size:42px; font-weight:900; line-height:1.08; margin-bottom:14px; letter-spacing:-1px; color:#ffffff; font-family:'Noto Serif SC', serif; }
.section-subtitle { font-size:16px; color:rgba(255,255,255,0.60); line-height:1.75; max-width:520px; margin-bottom:48px; font-weight:400; }
.editor-mock {
  background: rgba(20,20,30,0.50);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.10);
  backdrop-filter: blur(16px);
}
.editor-topbar { display:flex; align-items:center; gap:8px; padding:14px 20px; background:rgba(255,255,255,0.06); border-bottom:1px solid rgba(255,255,255,0.10); border-radius:20px 20px 0 0; }
.dot { width:12px; height:12px; border-radius:50%; }
.dot-red { background:#f87171; } .dot-yellow { background:#fbbf24; } .dot-green { background:#34d399; }
.editor-body { display:grid; grid-template-columns:190px 1fr; min-height:320px; }
.editor-sidebar { background:rgba(255,255,255,0.04); border-right:1px solid rgba(255,255,255,0.10); padding:16px 0; }
.sidebar-item { display:flex; align-items:center; gap:10px; padding:9px 18px; font-size:13px; color:rgba(255,255,255,0.45); cursor:pointer; font-weight:500; }
.sidebar-item.active { background:rgba(99,102,241,0.15); color:#a5b4fc; font-weight:700; border-right:2px solid #6366f1; }
.sidebar-item:hover:not(.active) { background:rgba(255,255,255,0.08); color:#ffffff; }
.s-dot { width:7px; height:7px; border-radius:50%; background:currentColor; flex-shrink:0; }
.editor-canvas { padding:24px; display:flex; flex-direction:column; gap:12px; background:rgba(0,0,0,0.15); }
.multi-select-row { display:flex; gap:12px; align-items:stretch; }
.frame-box { position:relative; border:1px solid rgba(255,255,255,0.12); border-radius:12px; padding:14px; flex:1; background:rgba(255,255,255,0.05); }
.frame-box.selected { border-color:rgba(99,102,241,0.40); background:rgba(99,102,241,0.12); box-shadow:0 0 0 2px rgba(99,102,241,0.15); }
.frame-box.selected::after { content:''; position:absolute; inset:-5px; border:1.5px dashed rgba(99,102,241,0.30); border-radius:16px; pointer-events:none; }
.frame-label { font-size:10px; color:rgba(255,255,255,0.35); margin-bottom:8px; font-family:monospace; font-weight:600; }
.frame-box.selected .frame-label { color:rgba(165,180,252,0.80); }
.ph { border-radius:6px; background:rgba(255,255,255,0.10); margin-bottom:6px; }
.frame-box.selected .ph { background:rgba(99,102,241,0.20); }
.edit-badge { position:absolute; top:-10px; right:10px; background:linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color:#FFFFFF; font-size:10px; font-weight:700; padding:2px 10px; border-radius:100px; }
.toolbar-row { display:flex; gap:8px; padding:10px 18px; border-top:1px solid rgba(255,255,255,0.10); background:rgba(255,255,255,0.04); }
.tb-btn { padding:5px 14px; border-radius:8px; font-size:12px; background:rgba(255,255,255,0.08); color:rgba(255,255,255,0.60); border:1px solid rgba(255,255,255,0.12); cursor:pointer; font-weight:600; transition:all 0.15s; }
.tb-btn:hover { background:rgba(255,255,255,0.15); color:#ffffff; }
.tb-btn.active { background:linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color:#FFFFFF; font-weight:700; border-color:transparent; }

/* FEATURES */
.features-section { padding:100px 100px; max-width:1400px; margin:0 auto; position:relative; background: transparent; }
.features-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-top:52px; }
.feature-card {
  background: rgba(20,20,30,0.45);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 28px;
  padding: 36px 30px;
  transition: all 0.28s cubic-bezier(.4,0,.2,1);
  backdrop-filter: blur(24px) saturate(1.8) brightness(1.04);
  -webkit-backdrop-filter: blur(24px) saturate(1.8) brightness(1.04);
  box-shadow:
    0 10px 40px rgba(0,0,0,0.25),
    0 2px 8px rgba(0,0,0,0.15),
    inset 0 2px 0 rgba(255,255,255,0.10),
    inset 0 -1px 0 rgba(0,0,0,0.20);
  position: relative;
  overflow: hidden;
}
.feature-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 45%, #22d3ee 100%);
  border-radius: 28px 28px 0 0;
  pointer-events: none;
  opacity: 0.75;
  transition: opacity 0.28s;
}
.feature-card::after {
  content: '';
  position: absolute;
  top: 0; left: -50%; width: 200%; height: 100%;
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.10) 50%, transparent 60%);
  pointer-events: none;
  transition: left 0.6s ease;
  opacity: 0;
}
.feature-card:hover {
  border-color: rgba(255,255,255,0.18);
  transform: translateY(-7px) scale(1.01);
  box-shadow:
    0 28px 72px rgba(0,0,0,0.35),
    0 8px 24px rgba(0,0,0,0.20),
    inset 0 2px 0 rgba(255,255,255,0.15);
  background: rgba(30,30,45,0.55);
}
.feature-card:hover::before { opacity: 1; }
.feature-card:hover::after { left: 50%; opacity: 1; }
.feature-icon { width:44px; height:44px; background:rgba(99,102,241,0.15); border-radius:14px; display:flex; align-items:center; justify-content:center; margin-bottom:18px; border:1px solid rgba(99,102,241,0.25); box-shadow: inset 0 1px 0 rgba(255,255,255,0.10); }
.feature-icon svg { width:20px; height:20px; stroke:#a5b4fc; stroke-width:2; fill:none; }
.feature-card h3 { font-size:16px; font-weight:700; margin-bottom:10px; letter-spacing:-0.2px; color:#ffffff; }
.feature-card p { font-size:14px; color:rgba(255,255,255,0.60); line-height:1.70; }

/* HOW IT WORKS */
.howto-section {
  padding: 120px 100px;
  background: rgba(15,15,25,0.50);
  position: relative;
  border-top: 1px solid rgba(255,255,255,0.10);
  border-bottom: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(24px) saturate(1.6);
  -webkit-backdrop-filter: blur(24px) saturate(1.6);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), inset 0 -1px 0 rgba(0,0,0,0.20);
}
.howto-section::before {
  content:''; position:absolute; top:0; left:0; right:0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, #6366f1 20%, #22d3ee 50%, #8b5cf6 80%, transparent 100%);
  opacity: 0.6;
}
.howto-section::after { display:none; }
.howto-inner { max-width:1000px; margin:0 auto; }
.howto-header { text-align:center; margin-bottom:70px; }

/* Horizontal timeline layout */
.howto-timeline {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 0;
  max-width: 900px;
  margin: 0 auto;
}
.htl-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}
/* Horizontal connector line between steps */
.htl-step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 22px;
  left: 50%;
  width: 100%;
  height: 1.5px;
  background: linear-gradient(90deg, rgba(13,33,165,0.30) 0%, rgba(209,208,103,0.40) 50%, rgba(185,199,248,0.20) 100%);
  z-index: 0;
}
.htl-num {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.08);
  color: #a5b4fc;
  font-size: 17px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 6px 24px rgba(0,0,0,0.25),
    inset 0 2px 0 rgba(255,255,255,0.12),
    inset 0 -1px 0 rgba(0,0,0,0.20);
  position: relative;
  z-index: 1;
  margin-bottom: 22px;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  transition: all 0.25s;
}
.htl-step:hover .htl-num {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #FFFFFF;
  transform: scale(1.10);
  box-shadow: 0 10px 32px rgba(99,102,241,0.45), inset 0 2px 0 rgba(255,255,255,0.25);
}
.htl-connector { display: none; }
.htl-content {
  text-align: center;
  padding: 0 16px;
}
.htl-title {
  font-size: 15px;
  font-weight: 700;
  color: rgba(255,255,255,0.60);
  margin-bottom: 8px;
  letter-spacing: -0.2px;
}
.htl-desc {
  font-size: 13px;
  color: rgba(255,255,255,0.60);
  line-height: 1.70;
}

/* CTA */
.cta-section {
  padding: 140px 100px; text-align:center; position:relative; overflow:hidden;
  background:
    radial-gradient(ellipse 70% 60% at 50% 50%, rgba(99,102,241,0.20) 0%, transparent 65%),
    radial-gradient(ellipse 40% 35% at 20% 80%, rgba(34,211,238,0.12) 0%, transparent 55%),
    rgba(15,15,25,0.55);
  border-top: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(24px) saturate(1.6);
  -webkit-backdrop-filter: blur(24px) saturate(1.6);
}
.cta-section::before {
  content:'';
  position:absolute; bottom:0; left:0; right:0;
  height:2px;
  background: linear-gradient(90deg, transparent, #6366f1 25%, #22d3ee 50%, #8b5cf6 75%, transparent);
  opacity: 0.7;
  pointer-events:none;
}
.cta-section::after {
  content:'';
  position:absolute; top:0; left:0; right:0;
  height:2px;
  background: linear-gradient(90deg, transparent, #6366f1 25%, #a5b4fc 50%, #22d3ee 75%, transparent);
  opacity: 0.6;
}
.cta-title { font-size:52px; font-weight:900; line-height:1.08; margin:12px auto 16px; max-width:680px; letter-spacing:-1px; color:#ffffff; font-family:'Noto Serif SC', serif; }
.cta-desc { font-size:16px; color:rgba(255,255,255,0.60); line-height:1.75; max-width:440px; margin:0 auto 44px; }
.cta-buttons { display:flex; gap:14px; justify-content:center; align-items:center; }
.btn-primary {
  display:inline-flex; align-items:center; gap:8px;
  background:linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color:#FFFFFF; padding:15px 32px;
  border:1px solid rgba(255,255,255,0.20);
  border-radius:16px; font-size:15px; font-weight:700; cursor:pointer;
  transition:all 0.22s; text-decoration:none;
  box-shadow:0 8px 28px rgba(99,102,241,0.40), inset 0 1px 0 rgba(255,255,255,0.25);
  letter-spacing:-0.1px;
}
.btn-primary:hover { transform:translateY(-2px); box-shadow:0 14px 40px rgba(99,102,241,0.55); background:linear-gradient(135deg, #818cf8 0%, #a78bfa 100%); }
.btn-secondary {
  display:inline-flex; align-items:center; padding:15px 32px;
  border-radius:16px; font-size:15px; font-weight:600; cursor:pointer;
  text-decoration:none; color:#ffffff;
  background:rgba(255,255,255,0.10);
  border:1px solid rgba(255,255,255,0.20);
  backdrop-filter:blur(12px);
  box-shadow:0 4px 16px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.12);
  transition:all 0.22s;
}
.btn-secondary:hover { color:#ffffff; background:rgba(255,255,255,0.18); transform:translateY(-1px); }

/* FOOTER */
.footer {
  padding: 48px 100px;
  border-top: 1px solid rgba(255,255,255,0.10);
  display:flex; justify-content:space-between;
  background: rgba(10,10,15,0.65);
  backdrop-filter: blur(32px) saturate(1.8);
  -webkit-backdrop-filter: blur(32px) saturate(1.8);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 -4px 24px rgba(0,0,0,0.25);
  align-items:center; position:relative;
}
.footer::before { display:none; }
.footer::after { display:none; }
.footer-brand { display:flex; align-items:center; gap:8px; font-size:14px; font-weight:700; letter-spacing:-0.2px; color:#ffffff; }
.footer-brand svg { width:18px; height:18px; stroke:#22d3ee; stroke-width:2; fill:none; }
.footer-links { display:flex; gap:28px; list-style:none; }
.footer-links li { font-size:13px; color:rgba(255,255,255,0.50); cursor:pointer; transition:color 0.2s; font-weight:500; }
.footer-links li:hover { color:#22d3ee; }
.footer-copy { font-size:13px; color:rgba(255,255,255,0.35); font-weight:400; }

/* ===== CASES SECTION - 椭圆无限滚动轮播图（原版样式） ===== */
.cases-section {
  padding: 100px 0;
  position: relative;
  background:
    radial-gradient(ellipse 80% 50% at 50% 50%, rgba(99,102,241,0.08) 0%, transparent 60%),
    rgba(10,10,15,0.40);
  border-top: 1px solid rgba(255,255,255,0.08);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  overflow: hidden;
  --post-spacing: 1.78vw;
  --post-size: 25vw;
  --mask-size: 100vw;
}
.cases-section::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(99,102,241,0.4) 30%, rgba(34,211,238,0.3) 70%, transparent 100%);
}
.cases-header {
  text-align: center;
  margin-bottom: 40px;
  padding: 0 20px;
}

/* 轮播图容器 - 原版样式 */
#banner {
  overflow: hidden;
  position: relative;
  width: 100vw;
  height: calc(var(--post-size) / 0.72);
  -webkit-mask: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNDQwIiBoZWlnaHQ9IjUwMCIgdmlld0JveD0iMCAwIDE0NDAgNTAwIiBpZD0iaiI+CiAgPHBhdGggZmlsbD0icmdiKDIwMCwyMDAsMjAwKSIgZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNMCAwczI3NS4wNCAxMDAgNzIwIDEwMFMxNDQwIDAgMTQ0MCAwdjUwMHMtMjc1LjA0LTEwMC03MjAtMTAwUzAgNTAwIDAgNTAwVjB6Ii8+Cjwvc3ZnPgo=);
          mask: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNDQwIiBoZWlnaHQ9IjUwMCIgdmlld0JveD0iMCAwIDE0NDAgNTAwIiBpZD0iaiI+CiAgPHBhdGggZmlsbD0icmdiKDIwMCwyMDAsMjAwKSIgZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNMCAwczI3NS4wNCAxMDAgNzIwIDEwMFMxNDQwIDAgMTQ0MCAwdjUwMHMtMjc1LjA0LTEwMC03MjAtMTAwUzAgNTAwIDAgNTAwVjB6Ii8+Cjwvc3ZnPgo=);
  -webkit-mask-repeat: no-repeat;
          mask-repeat: no-repeat;
  -webkit-mask-position: center;
          mask-position: center;
  -webkit-mask-size: var(--mask-size);
          mask-size: var(--mask-size);
  margin: 20px 0;
}

.img-wrapper {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  position: absolute;
  width: 100%;
  float: left;
  height: calc(var(--post-size) / 0.72);
  -webkit-transform: translate(13.39vw, 0);
          transform: translate(13.39vw, 0);
  -webkit-animation: admission 1.5s;
          animation: admission 1.5s;
}

.img-box {
  height: 100%;
  display: inline-block;
  margin-right: var(--post-spacing);
  position: relative;
  cursor: pointer;
}

.img-box .info {
  position: absolute;
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
      -ms-flex-direction: column;
          flex-direction: column;
  -webkit-box-pack: center;
      -ms-flex-pack: center;
          justify-content: center;
  left: 0;
  top: 0;
  height: 100%;
  width: 100%;
  background: rgba(23, 23, 23, 0.5);
  text-align: center;
  color: #fff9f1;
  font-size: 4rem;
  opacity: 0;
  -webkit-transition: opacity 0.3s ease;
  transition: opacity 0.3s ease;
}

.img-box:hover .info {
  opacity: 1;
}

.img-box .info h3 {
  font-size: 2.4rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 10px rgba(0,0,0,0.5);
  margin: 0;
  padding: 0 20px;
}

.img-box img {
  width: var(--post-size);
  height: 100%;
  -o-object-position: center;
     object-position: center;
  -o-object-fit: cover;
     object-fit: cover;
  border-radius: 12px;
  -webkit-transition: -webkit-transform 0.5s ease;
  transition: -webkit-transform 0.5s ease;
  transition: transform 0.5s ease;
  transition: transform 0.5s ease, -webkit-transform 0.5s ease;
}

.img-box:hover img {
  -webkit-transform: scale(1.15);
          transform: scale(1.15);
}

.img-box:last-child {
  -webkit-transform: translateX(-160.68vw);
          transform: translateX(-160.68vw);
}

/* 按钮组 - 原版样式 */
.btn-group {
  height: 15vh;
  position: absolute;
  left: 50%;
  bottom: 0%;
  -webkit-transform: translate(-50%, -50%);
          transform: translate(-50%, -50%);
  -webkit-transition: 1s;
  transition: 1s;
  opacity: 0;
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  gap: 20px;
  z-index: 10;
}

.btn-group .btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.20);
  background-color: rgba(20,20,30,0.80);
  -webkit-backdrop-filter: blur(16px);
          backdrop-filter: blur(16px);
  margin: 10px;
  cursor: pointer;
  -webkit-transition: 0.4s;
  transition: 0.4s;
  -webkit-box-sizing: border-box;
          box-sizing: border-box;
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-align: center;
      -ms-flex-align: center;
          align-items: center;
  -webkit-box-pack: center;
      -ms-flex-pack: center;
          justify-content: center;
  -webkit-box-shadow: 0 8px 32px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.10);
          box-shadow: 0 8px 32px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.10);
}

.btn-group .btn:hover {
  -webkit-transform: scale(1.2);
          transform: scale(1.2);
  background: -webkit-linear-gradient(315deg, #6366f1 0%, #8b5cf6 100%);
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-color: transparent;
}

.btn-group .btn:hover .icon {
  fill: #fff;
}

.btn-group .btn .icon {
  width: 30px;
  height: 30px;
  fill: rgba(255,255,255,0.90);
  transition: fill 0.3s ease;
}

.btn-group .btn .right {
  -webkit-transform: rotate(180deg);
          transform: rotate(180deg);
}

.img-list {
  position: relative;
  left: 0;
}

@-webkit-keyframes admission {
  0% {
    -webkit-transform: translate(140vw, 0);
            transform: translate(140vw, 0);
  }
  100% {
    -webkit-transform: translate(13.39vw, 0);
            transform: translate(13.39vw, 0);
  }
}

@keyframes admission {
  0% {
    -webkit-transform: translate(140vw, 0);
            transform: translate(140vw, 0);
  }
  100% {
    -webkit-transform: translate(13.39vw, 0);
            transform: translate(13.39vw, 0);
  }
}

/* 响应式调整 */
@media(max-width: 1024px) {
  .cases-section {
    --post-size: 35vw;
  }
  #banner {
    height: calc(var(--post-size) / 0.72);
  }
  .img-box img {
    border-radius: 8px;
  }
}

@media(max-width: 768px) {
  .cases-section {
    padding: 60px 0;
    --post-size: 45vw;
  }
  #banner {
    height: calc(var(--post-size) / 0.72);
    mask-size: 150vw;
  }
  .img-wrapper {
    transform: translate(5vw, 0);
  }
  .img-box .info h3 {
    font-size: 1.8rem;
  }
  .btn-group .btn {
    width: 50px;
    height: 50px;
  }
  .btn-group .btn .icon {
    width: 24px;
    height: 24px;
  }
}

/* RESPONSIVE */
@media(max-width:1200px) {
  .hero-inner { padding: 0 40px; gap: 40px; }
  .hero-right { min-width: 360px; }
  .title { font-size: 60px; }
}
@media(max-width:1024px) {
  .navbar, .features-section, .cta-section, .howto-section, .footer { padding-left:40px; padding-right:40px; }
  .preview-panel { padding:60px 40px; }
  .hero-inner { padding: 0 40px; gap: 32px; }
  .hero-acrylic-panel { width: 48%; z-index: 2; }
  .hero-left { width: 45%; padding: 36px 32px; }
  .title { font-size: 52px; letter-spacing: -2px; }
  .hero-right { min-width: 320px; height: 400px; }
}
@media(max-width:768px) {
  .navbar { padding:0 20px; }
  .navbar-menu { display:none; }
  .hero-inner { flex-direction:column; padding: 40px 24px; gap: 40px; }
  .hero-acrylic-panel { display: none; }
  .hero-left { width: 100%; max-width: 100%; text-align: center; padding: 0; }
  .hero-inner { z-index: 3; }
  .hero-trust-tags { justify-content: center; }
  .hero-actions { justify-content: center; }
  .hero-right { min-width: unset; width: 100%; height: 340px; }
  .hc-mini-1 { left: 0; }
  .hc-mini-3 { right: 0; }
  .title { font-size:40px; letter-spacing:-1.5px; }
  .hero-scroll-hint { display: none; }
  .features-grid { grid-template-columns:1fr; }
  .howto-timeline { max-width: 100%; }
  .steps::before { display:none; }
  .cta-title { font-size:36px; }
  .footer { flex-direction:column; gap:20px; text-align:center; padding:36px 24px; }
  .features-section, .cta-section { padding:60px 24px; }
  .howto-section { padding:60px 24px; }
  .preview-panel { padding:50px 24px; }
  .editor-body { grid-template-columns:1fr; }
  .editor-sidebar { display:none; }
}

</style>
