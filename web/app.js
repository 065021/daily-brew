/**
 * 日知录 — 前端应用
 * 纯静态、零依赖（除 marked.js CDN）
 */
(function () {
  "use strict";

  // ============================================================
  // 状态
  // ============================================================
  let posts = [];
  let currentPost = null;

  // ============================================================
  // DOM 引用
  // ============================================================
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const homeView = $("#home-view");
  const postView = $("#post-view");
  const aboutView = $("#about-view");
  const postsGrid = $("#posts-grid");
  const postMeta = $("#post-meta");
  const postContent = $("#post-content");
  const themeToggle = $("#themeToggle");

  // ============================================================
  // 路由
  // ============================================================
  function route() {
    const hash = location.hash;

    if (hash.startsWith("#post/")) {
      const slug = hash.slice(6);
      showPost(slug);
    } else if (hash === "#about") {
      showAbout();
    } else {
      showHome();
    }
  }

  function navigateTo(view) {
    homeView.style.display = "none";
    postView.style.display = "none";
    aboutView.style.display = "none";
    if (view) view.style.display = "";
    window.scrollTo(0, 0);
  }

  function showHome() {
    navigateTo(homeView);
    renderCards();
  }

  function showAbout() {
    navigateTo(aboutView);
  }

  async function showPost(slug) {
    navigateTo(postView);

    // 从已加载的索引中找元数据
    const meta = posts.find((p) => p.slug === slug);
    if (!meta) {
      postContent.innerHTML = "<p>文章未找到</p>";
      return;
    }

    currentPost = meta;

    // 渲染元数据
    postMeta.innerHTML = `
      <h1>${escapeHtml(meta.title)}</h1>
      <div class="post-meta-info">
        <span>${meta.date}</span>
        <span class="post-meta-category">${escapeHtml(meta.category)}</span>
      </div>
    `;

    // 加载并渲染 Markdown
    try {
      postContent.innerHTML = '<p class="loading">加载中...</p>';
      const resp = await fetch(meta.path);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      let md = await resp.text();

      // 去掉 YAML frontmatter
      md = md.replace(/^---[\s\S]*?---\n*/, "");

      // 渲染
      postContent.innerHTML = marked.parse(md);
    } catch (err) {
      postContent.innerHTML = `<p>加载失败：${escapeHtml(err.message)}</p>`;
    }
  }

  // ============================================================
  // 卡片渲染
  // ============================================================
  function renderCards() {
    if (!posts.length) {
      postsGrid.innerHTML = '<p class="loading">还没有文章，等待第一篇...</p>';
      return;
    }

    postsGrid.innerHTML = posts
      .map(
        (p) => `
      <a href="#post/${p.slug}" class="post-card">
        <div class="post-card-header">
          <span class="post-card-date">${p.date}</span>
          <span class="post-card-category">${escapeHtml(p.category)}</span>
        </div>
        <h2>${escapeHtml(p.title)}</h2>
        <p class="post-card-summary">${escapeHtml(p.summary)}</p>
      </a>
    `
      )
      .join("");
  }

  // ============================================================
  // 深色模式
  // ============================================================
  function initTheme() {
    const saved = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const theme = saved || (prefersDark ? "dark" : "light");
    applyTheme(theme);
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    themeToggle.textContent = theme === "dark" ? "☀️" : "🌙";
    localStorage.setItem("theme", theme);
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme");
    applyTheme(current === "dark" ? "light" : "dark");
  }

  // ============================================================
  // 事件绑定
  // ============================================================
  function bindEvents() {
    // 主题切换
    themeToggle.addEventListener("click", toggleTheme);

    // 导航链接
    document.addEventListener("click", (e) => {
      const nav = e.target.closest("[data-nav]");
      if (nav) {
        e.preventDefault();
        const target = nav.dataset.nav;
        if (target === "home") location.hash = "";
        else if (target === "about") location.hash = "about";
      }
    });

    // hash 变化
    window.addEventListener("hashchange", route);
  }

  // ============================================================
  // 加载索引
  // ============================================================
  async function loadIndex() {
    try {
      const resp = await fetch("posts.json");
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      posts = await resp.json();
    } catch (err) {
      console.error("加载 posts.json 失败:", err);
      posts = [];
    }
  }

  // ============================================================
  // 工具函数
  // ============================================================
  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ============================================================
  // 启动
  // ============================================================
  async function init() {
    initTheme();
    bindEvents();
    await loadIndex();
    route();
  }

  init();
})();
