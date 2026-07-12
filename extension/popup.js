// ClipSnap Chrome Extension — Popup Script
const API_BASE = 'http://localhost:8710';

// ── 状态 ────────────────────────────────────
let selectedTag = '';

// ── DOM ──────────────────────────────────────
const $status = document.getElementById('status');
const $preview = document.getElementById('preview');
const $apiStatus = document.getElementById('apiStatus');
const $btnClip = document.getElementById('btnClip');
const $btnDashboard = document.getElementById('btnOpenDashboard');

// ── 标签选择 ─────────────────────────────────
document.getElementById('tagList').addEventListener('click', (e) => {
  if (e.target.classList.contains('tag')) {
    document.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
    e.target.classList.add('active');
    selectedTag = e.target.dataset.tag;
  }
});

// ── API 检测 ─────────────────────────────────
async function checkAPI() {
  try {
    const resp = await fetch(`${API_BASE}/api/health`);
    const data = await resp.json();
    if (data.status === 'ok') {
      $apiStatus.textContent = `🟢 API 在线 · ${data.clips_count} 条收藏`;
      $apiStatus.className = 'api-status online';
      return true;
    }
  } catch {}
  $apiStatus.textContent = '🔴 API 未连接 · 请启动后端';
  $apiStatus.className = 'api-status offline';
  return false;
}

// ── 抓取逻辑 ─────────────────────────────────
$btnClip.addEventListener('click', async () => {
  const online = await checkAPI();
  if (!online) {
    showStatus('error', '❌ 后端服务未启动，请先运行 backend/main.py');
    return;
  }

  showStatus('loading', '⏳ 正在抓取...');
  $preview.style.display = 'none';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // 获取页面 HTML
    const [{ result: html }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML,
    });

    // 发送到后端
    const tags = [];
    if (selectedTag) tags.push(selectedTag);
    const customTag = document.getElementById('customTag').value.trim();
    if (customTag) tags.push(customTag);

    const resp = await fetch(`${API_BASE}/api/clip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: tab.url, html, tags }),
    });

    const data = await resp.json();
    if (data.ok) {
      showStatus('success', `✅ 已保存！${data.clip.word_count} 字`);
      $preview.textContent = data.clip.content_md;
      $preview.style.display = 'block';
      // 刷新计数
      checkAPI();
    } else {
      showStatus('error', '❌ 保存失败');
    }
  } catch (err) {
    showStatus('error', `❌ 抓取失败: ${err.message}`);
  }
});

// ── 打开管理面板 ──────────────────────────────
$btnDashboard.addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:8710' });
});

// ── 辅助 ──────────────────────────────────────
function showStatus(type, msg) {
  $status.textContent = msg;
  $status.className = `status ${type}`;
}

// ── 初始化 ────────────────────────────────────
checkAPI();
