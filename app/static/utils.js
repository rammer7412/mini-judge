export function escapeHtml(s) {
  return (s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

export function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}


export function renderMarkdown(md) {
  const src = (md ?? '').replaceAll('\r\n', '\n');
  const lines = src.split('\n');

  let html = '';
  let inCode = false;
  let codeBuf = [];
  let para = [];
  let listType = null; // 'ul' | 'ol'
  let listBuf = [];

  function flushPara() {
    const text = para.join(' ').trim();
    para = [];
    if (!text) return;
    html += `<p>${renderInline(text)}</p>`;
  }

  function flushList() {
    if (!listType || !listBuf.length) {
      listType = null;
      listBuf = [];
      return;
    }
    const tag = listType;
    html += `<${tag}>` + listBuf.map(li => `<li>${renderInline(li)}</li>`).join('') + `</${tag}>`;
    listType = null;
    listBuf = [];
  }

  function renderInline(text) {
    // Escape first, then replace inline code `...`
    const esc = escapeHtml(text);
    return esc.replace(/`([^`]+)`/g, '<code>$1</code>');
  }

  for (const lineRaw of lines) {
    const line = lineRaw ?? '';

    // fenced code block
    if (line.trim().startsWith('```')) {
      flushPara();
      flushList();
      if (!inCode) {
        inCode = true;
        codeBuf = [];
      } else {
        html += `<pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre>`;
        inCode = false;
      }
      continue;
    }

    if (inCode) {
      codeBuf.push(line);
      continue;
    }

    const t = line.trim();

    if (!t) {
      flushPara();
      flushList();
      continue;
    }

    // Headings
    if (t.startsWith('### ')) {
      flushPara(); flushList();
      html += `<h3>${renderInline(t.slice(4))}</h3>`;
      continue;
    }
    if (t.startsWith('## ')) {
      flushPara(); flushList();
      html += `<h2>${renderInline(t.slice(3))}</h2>`;
      continue;
    }
    if (t.startsWith('# ')) {
      flushPara(); flushList();
      html += `<h1>${renderInline(t.slice(2))}</h1>`;
      continue;
    }

    // Lists
    const ulMatch = t.match(/^[-*]\s+(.+)$/);
    if (ulMatch) {
      flushPara();
      if (listType && listType !== 'ul') flushList();
      listType = 'ul';
      listBuf.push(ulMatch[1]);
      continue;
    }
    const olMatch = t.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      flushPara();
      if (listType && listType !== 'ol') flushList();
      listType = 'ol';
      listBuf.push(olMatch[1]);
      continue;
    }

    // Normal paragraph line
    para.push(t);
  }

  // flush tail
  flushPara();
  flushList();
  if (inCode) {
    html += `<pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre>`;
  }

  return html;
}
