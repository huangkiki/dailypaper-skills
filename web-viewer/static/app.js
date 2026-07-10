/* ── ObsidianNotes Web Viewer — Frontend Logic ── */

let WIKILINK_INDEX = {};

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
const routes = [];
function route(pattern, handler) {
  const keys = [];
  const re = pattern.replace(/:(\w+)/g, (_, k) => { keys.push(k); return '([^/]+)'; });
  routes.push({ re: new RegExp('^' + re + '$'), keys, handler });
}

function resolve() {
  const hash = (location.hash || '#/').slice(1);
  const [path, qs] = hash.split('?');
  const params = {};
  if (qs) qs.split('&').forEach(p => { const [k,v] = p.split('='); params[k] = decodeURIComponent(v); });

  for (const r of routes) {
    const m = path.match(r.re);
    if (m) {
      const args = {};
      r.keys.forEach((k, i) => args[k] = decodeURIComponent(m[i + 1]));
      Object.assign(args, params);
      r.handler(args);
      updateActiveNav(path);
      return;
    }
  }
  pageDailyList();
}

function updateActiveNav(path) {
  document.querySelectorAll('.nav-item').forEach(el => {
    const r = el.dataset.route;
    const active = (r === 'daily' && (path === '/' || path.startsWith('/daily')))
      || (r === 'trending' && path.startsWith('/trending'))
      || (r === 'notes' && path.startsWith('/notes'))
      || (r === 'concepts' && path.startsWith('/concepts'));
    el.classList.toggle('active', active);
  });
}

window.addEventListener('hashchange', resolve);

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------
async function api(url) {
  const r = await fetch(url);
  return r.json();
}

// ---------------------------------------------------------------------------
// Markdown Rendering
// ---------------------------------------------------------------------------
function initMarked() {
  const latexBlock = {
    name: 'latexBlock',
    level: 'block',
    start(src) { return src.indexOf('$$'); },
    tokenizer(src) {
      const m = src.match(/^\$\$([\s\S]+?)\$\$/);
      if (m) return { type: 'latexBlock', raw: m[0], text: m[1] };
    },
    renderer(token) {
      return '<div class="math-block">$$' + escapeHtml(token.text) + '$$</div>';
    }
  };

  const latexInline = {
    name: 'latexInline',
    level: 'inline',
    start(src) {
      const i = src.indexOf('$');
      return i >= 0 && (i === 0 || src[i-1] !== '$') ? i : -1;
    },
    tokenizer(src) {
      const m = src.match(/^\$([^\$\n]+?)\$/);
      if (m && !m[0].startsWith('$$')) return { type: 'latexInline', raw: m[0], text: m[1] };
    },
    renderer(token) {
      return '<span class="math-inline">$' + escapeHtml(token.text) + '$</span>';
    }
  };

  const wikilink = {
    name: 'wikilink',
    level: 'inline',
    start(src) { return src.indexOf('[['); },
    tokenizer(src) {
      const m = src.match(/^\[\[([^\]]+)\]\]/);
      if (m) {
        const inner = m[1];
        let target, display;
        if (inner.includes('|')) {
          [target, display] = inner.split('|', 2);
        } else {
          target = display = inner;
        }
        return { type: 'wikilink', raw: m[0], target: target.trim(), display: display.trim() };
      }
    },
    renderer(token) {
      const resolved = resolveWikilink(token.target);
      if (resolved) {
        return `<a href="${resolved.href}" class="wikilink ${resolved.cls}">${token.display}</a>`;
      }
      return `<span class="wikilink wikilink-broken">${token.display}</span>`;
    }
  };

  marked.use({ extensions: [latexBlock, latexInline, wikilink] });
}

function resolveWikilink(target) {
  const stem = target.includes('/') ? target.split('/').pop() : target;
  const entry = WIKILINK_INDEX[stem];
  if (!entry) return null;
  switch (entry.type) {
    case 'note':
      return { href: '#/notes/' + stem, cls: 'wikilink-note' };
    case 'concept': {
      const parts = entry.path.split('/');
      return { href: '#/concepts/' + parts[2] + '/' + parts[3], cls: 'wikilink-concept' };
    }
    case 'daily':
      return { href: '#/daily/' + stem, cls: 'wikilink-daily' };
  }
}

function renderMd(raw) {
  let html = marked.parse(raw || '');
  html = processCallouts(html);
  return html;
}

function processCallouts(html) {
  return html.replace(
    /<blockquote>\s*<p>\[!([\w]+)\]\s*(.*?)<\/p>([\s\S]*?)<\/blockquote>/g,
    (_, type, title, body) => {
      const icons = { summary: '📝', note: '📌', warning: '⚠️', tip: '💡', important: '❗', info: 'ℹ️' };
      return `<div class="callout"><div class="callout-title">${icons[type]||''} ${title||type}</div><div class="callout-body">${body}</div></div>`;
    }
  );
}

function renderMath(el) {
  if (typeof renderMathInElement === 'function') {
    renderMathInElement(el, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false }
      ],
      throwOnError: false
    });
  }
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ---------------------------------------------------------------------------
// Badges
// ---------------------------------------------------------------------------
function renderBadges(fm) {
  let h = '';
  if (fm.venue) h += `<span class="badge badge-venue">${fm.venue}</span>`;
  if (fm.year) h += `<span class="badge badge-year">${fm.year}</span>`;
  if (fm.tags && Array.isArray(fm.tags)) fm.tags.forEach(t => h += `<span class="badge badge-tag">${t}</span>`);
  return h;
}

// ---------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------

// ---- Daily Papers List ----
async function pageDailyList() {
  const list = await api('/api/daily-papers');
  const $c = document.getElementById('content');
  $c.innerHTML = `
    <h1 class="page-title">📰 Daily Papers</h1>
    <div class="daily-list">
      ${list.map(p => `
        <a href="#/daily/${p.filename}" class="daily-card">
          <span class="daily-date">${p.date}</span>
          <span class="daily-title">${p.filename.replace(/^\d{4}-\d{2}-\d{2}-/, '')}</span>
          ${p.is_weekly ? '<span class="badge badge-weekly">Weekly</span>' : ''}
          ${p.range ? `<span class="badge badge-tag">${p.range}</span>` : ''}
        </a>
      `).join('')}
    </div>`;
}

// ---- Daily Paper Detail ----
async function pageDailyDetail({ filename }) {
  const data = await api('/api/daily-papers/' + encodeURIComponent(filename));
  if (data.error) { document.getElementById('content').innerHTML = '<p>Not found</p>'; return; }
  const $c = document.getElementById('content');
  $c.innerHTML = `
    <a class="back-btn" href="#/">← Back</a>
    <div style="margin-bottom:12px">${renderBadges(data.frontmatter)}</div>
    ${renderTierCards(data.tiers)}
    <div class="md-body">${renderMd(data.content)}</div>`;
  renderMath($c);
}

// ---- GitHub Trending List ----
async function pageTrendingList() {
  const list = await api('/api/github-trending');
  const $c = document.getElementById('content');
  const periodLabel = { weekly: 'Weekly', daily: 'Daily', monthly: 'Monthly' };
  $c.innerHTML = `
    <h1 class="page-title">🔥 GitHub Trending</h1>
    ${list.length ? `<div class="daily-list">
      ${list.map(p => `
        <a href="#/trending/${encodeURIComponent(p.filename)}" class="daily-card">
          <span class="daily-date">${p.date}</span>
          <span class="daily-title">${p.filename}</span>
          ${p.period ? `<span class="badge badge-weekly">${periodLabel[p.period] || p.period}</span>` : ''}
        </a>
      `).join('')}
    </div>` : '<p style="color:var(--text-muted)">还没有榜单。跟 Claude 说一句「GitHub 周榜」生成第一份。</p>'}`;
}

// ---- GitHub Trending Detail ----
async function pageTrendingDetail({ filename }) {
  const data = await api('/api/github-trending/' + encodeURIComponent(filename));
  if (data.error) { document.getElementById('content').innerHTML = '<p>Not found</p>'; return; }
  const $c = document.getElementById('content');
  $c.innerHTML = `
    <a class="back-btn" href="#/trending">← Back</a>
    <div style="margin-bottom:12px">${renderBadges(data.frontmatter)}</div>
    <div class="md-body">${renderMd(data.content)}</div>`;
  renderMath($c);
}

// ---- Tier Cards ----
function renderTierCards(tiers) {
  if (!tiers || !tiers.length) return '';
  const cfg = {
    '必读': { cls: 'tier-label-must', chip: 'must' },
    '值得看': { cls: 'tier-label-worth', chip: 'worth' },
    '关注': { cls: 'tier-label-watch', chip: 'watch' },
    '可跳过': { cls: 'tier-label-skip', chip: 'skip' },
  };
  return `<div class="tier-section">${tiers.map(t => {
    const c = cfg[t.tier] || { cls: '', chip: '' };
    return `<div class="tier-group">
      <div class="tier-label ${c.cls}">${t.emoji} ${t.tier}</div>
      <div class="tier-papers">${t.papers.map(p => `
        <div class="paper-chip ${c.chip}" onclick="scrollToPaper('${p.name.replace(/'/g,"\\'")}')">
          <span class="paper-chip-name">${p.name}</span>
          ${p.description ? `<span class="paper-chip-desc">${p.description}</span>` : ''}
          ${p.has_note ? `<a href="#/notes/${p.name}" class="paper-chip-note" onclick="event.stopPropagation()">📒 笔记</a>` : ''}
        </div>`).join('')}
      </div>
    </div>`;
  }).join('')}</div>`;
}

function scrollToPaper(name) {
  const headers = document.querySelectorAll('.md-body h3, .md-body h2');
  for (const h of headers) {
    if (h.textContent.includes(name)) {
      h.scrollIntoView({ behavior: 'smooth', block: 'start' });
      h.classList.add('highlight');
      setTimeout(() => h.classList.remove('highlight'), 2500);
      return;
    }
  }
}

// ---- Paper Notes List ----
async function pageNotesList() {
  const notes = await api('/api/paper-notes');
  const $c = document.getElementById('content');
  $c.innerHTML = `
    <h1 class="page-title">📝 Paper Notes</h1>
    <div class="notes-grid">
      ${notes.map(n => `
        <a href="#/notes/${n.filename}" class="note-card">
          <div class="note-method">${n.method_name || n.filename}</div>
          <div class="note-title">${n.title || ''}</div>
          <div class="note-meta">${renderBadges(n)}</div>
        </a>
      `).join('')}
    </div>`;
}

// ---- Paper Note Detail ----
async function pageNoteDetail({ filename }) {
  const data = await api('/api/paper-notes/' + encodeURIComponent(filename));
  if (data.error) { document.getElementById('content').innerHTML = '<p>Not found</p>'; return; }
  const $c = document.getElementById('content');
  $c.innerHTML = `
    <a class="back-btn" href="#/notes">← Back</a>
    <div style="margin-bottom:12px">${renderBadges(data.frontmatter)}</div>
    <div class="md-body">${renderMd(data.content)}</div>`;
  renderMath($c);
}

// ---- Concepts ----
async function pageConceptsList() {
  const cats = await api('/api/concepts');
  const $c = document.getElementById('content');
  $c.innerHTML = `
    <h1 class="page-title">🧠 Concept Wiki</h1>
    <div class="concepts-grid">
      ${cats.map(cat => `
        <div class="concept-category">
          <div class="concept-cat-name">${cat.category_id}</div>
          <div class="concept-cat-count">${cat.concepts.length} concepts</div>
          <div class="concept-tags">
            ${cat.concepts.map(c => `<a href="#/concepts/${cat.category_id}/${c.filename}" class="concept-tag">${c.name}</a>`).join('')}
          </div>
        </div>
      `).join('')}
    </div>`;
}

// ---- Concept Detail ----
async function pageConceptDetail({ category, filename }) {
  const data = await api(`/api/concepts/${encodeURIComponent(category)}/${encodeURIComponent(filename)}`);
  if (data.error) { document.getElementById('content').innerHTML = '<p>Not found</p>'; return; }
  const $c = document.getElementById('content');
  $c.innerHTML = `
    <a class="back-btn" href="#/concepts">← Back</a>
    <div class="md-body">${renderMd(data.content)}</div>`;
  renderMath($c);
}

// ---- Search ----
async function pageSearch(params) {
  const q = params.q || '';
  if (!q) { document.getElementById('content').innerHTML = '<p>Enter a search query</p>'; return; }
  const results = await api('/api/search?q=' + encodeURIComponent(q));
  const $c = document.getElementById('content');
  const typeLinks = { daily: '#/daily/', note: '#/notes/', concept: '#/concepts/' };
  $c.innerHTML = `
    <h1 class="page-title">Search: "${q}"</h1>
    <p style="color:var(--text-muted);margin-bottom:1rem">${results.length} results</p>
    <div class="search-results">
      ${results.map(r => {
        let href;
        if (r.type === 'concept') {
          const resolved = WIKILINK_INDEX[r.filename];
          href = resolved ? '#/concepts/' + resolved.path.split('/')[2] + '/' + resolved.path.split('/')[3] : '#/';
        } else {
          href = (typeLinks[r.type] || '#/') + r.filename;
        }
        return `<a href="${href}" class="search-item">
          <span class="search-item-type">${r.type}</span>
          <span class="search-item-title">${r.title || r.filename}</span>
          ${r.snippet ? `<div class="search-item-snippet">...${r.snippet}...</div>` : ''}
        </a>`;
      }).join('')}
    </div>`;
}

function doSearch() {
  const q = document.getElementById('search-input').value.trim();
  if (q) location.hash = '#/search?q=' + encodeURIComponent(q);
}

// ---------------------------------------------------------------------------
// Claude Chat
// ---------------------------------------------------------------------------
function toggleClaude() {
  document.getElementById('claude-panel').classList.toggle('collapsed');
}

function handleClaudeKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendClaude(); }
}

async function sendClaude() {
  const input = document.getElementById('claude-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  const msgs = document.getElementById('claude-messages');
  msgs.innerHTML += `<div class="chat-msg user">${escapeHtml(msg)}</div>`;
  const assistantDiv = document.createElement('div');
  assistantDiv.className = 'chat-msg assistant';
  assistantDiv.innerHTML = '<div class="claude-status"><span class="spinner"></span> Thinking...</div>';
  msgs.appendChild(assistantDiv);
  msgs.scrollTop = msgs.scrollHeight;

  const startTime = Date.now();
  let timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const timerEl = assistantDiv.querySelector('.claude-timer');
    if (timerEl) timerEl.textContent = `${elapsed}s`;
  }, 1000);

  try {
    const resp = await fetch('/api/claude', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';
    let toolLog = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) {
              clearInterval(timerInterval);
              assistantDiv.innerHTML = `<span style="color:#e74c3c">Error: ${data.error}</span>`;
            } else if (data.type === 'tool') {
              const detail = data.detail ? `: ${data.detail}` : '';
              toolLog.push(`${data.tool}${detail}`);
              const toolHtml = `<div class="claude-status"><span class="spinner"></span> 🔧 ${data.tool}${detail ? `<span class="tool-detail">${detail}</span>` : ''}<span class="claude-timer">${Math.floor((Date.now()-startTime)/1000)}s</span></div>`;
              assistantDiv.innerHTML = (fullText ? `<div class="md-body">${renderMd(fullText)}</div>` : '') + toolHtml;
            } else if (data.type === 'heartbeat') {
              const timerEl = assistantDiv.querySelector('.claude-timer');
              if (timerEl) timerEl.textContent = `${Math.floor((Date.now()-startTime)/1000)}s`;
            } else if (data.type === 'result' && data.text) {
              clearInterval(timerInterval);
              fullText = data.text;
              const elapsed = data.duration_ms ? `${(data.duration_ms/1000).toFixed(1)}s` : `${Math.floor((Date.now()-startTime)/1000)}s`;
              const costInfo = data.cost_usd ? ` · $${data.cost_usd.toFixed(4)}` : '';
              const toolSummary = toolLog.length ? `<div class="claude-tool-log">${toolLog.map(t=>`<span class="tool-tag">🔧 ${t.split(':')[0]}</span>`).join('')}</div>` : '';
              assistantDiv.innerHTML = `${toolSummary}<div class="md-body">${renderMd(fullText)}</div><div class="claude-meta">${elapsed}${costInfo}</div>`;
              renderMath(assistantDiv);
            } else if (data.type === 'text' && data.text) {
              fullText += data.text;
              const statusHtml = toolLog.length ? `<div class="claude-status"><span class="spinner"></span> Processing...<span class="claude-timer">${Math.floor((Date.now()-startTime)/1000)}s</span></div>` : '';
              assistantDiv.innerHTML = `<div class="md-body">${renderMd(fullText)}</div>` + statusHtml;
              renderMath(assistantDiv);
            }
          } catch (_) {}
        }
      }
    }
    clearInterval(timerInterval);
    if (!fullText) assistantDiv.innerHTML = '<span style="color:var(--text-muted)">No response</span>';
  } catch (err) {
    clearInterval(timerInterval);
    assistantDiv.innerHTML = `<span style="color:#e74c3c">Error: ${err.message}</span>`;
  }
  msgs.scrollTop = msgs.scrollHeight;
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
route('/', pageDailyList);
route('/daily/:filename', pageDailyDetail);
route('/trending', pageTrendingList);
route('/trending/:filename', pageTrendingDetail);
route('/notes', pageNotesList);
route('/notes/:filename', pageNoteDetail);
route('/concepts', pageConceptsList);
route('/concepts/:category/:filename', pageConceptDetail);
route('/search', pageSearch);

(async function init() {
  initMarked();
  WIKILINK_INDEX = await api('/api/wikilink-index');
  resolve();
})();
