import { escapeHtml, renderMarkdown } from './utils.js';

export const STATUS_TO_UI = {
  QUEUED: { label: 'Queued', cls: 'muted', done: false },
  RUNNING: { label: 'Running', cls: 'muted', done: false },

  ACCEPTED: { label: 'Correct', cls: 'ok', done: true },
  WRONG_ANSWER: { label: 'Wrong', cls: 'danger', done: true },
  TIME_LIMIT_EXCEEDED: { label: 'Timeout', cls: 'danger', done: true },
  MEMORY_LIMIT_EXCEEDED: { label: 'Memory Limit', cls: 'danger', done: true },
  RUNTIME_ERROR: { label: 'Error', cls: 'danger', done: true },
  COMPILATION_ERROR: { label: 'Compile Error', cls: 'danger', done: true },
  INTERNAL_ERROR: { label: 'Error', cls: 'danger', done: true },
};

export function getDom() {
  return {
    problemSelect: document.getElementById('problemSelect'),
    langSelect: document.getElementById('langSelect'),
    userNameInput: document.getElementById('userNameInput'),
    submitBtn: document.getElementById('submitBtn'),
    codeArea: document.getElementById('codeArea'),
    statusText: document.getElementById('statusText'),

    problemTitle: document.getElementById('problemTitle'),
    problemId: document.getElementById('problemId'),
    timeLimitPill: document.getElementById('timeLimitPill'),
    memLimitPill: document.getElementById('memLimitPill'),
    sampleCountPill: document.getElementById('sampleCountPill'),

    statementBox: document.getElementById('statementBox'),
    samplesBox: document.getElementById('samplesBox'),

    resultHint: document.getElementById('resultHint'),
    resultBox: document.getElementById('resultBox'),
    lastSid: document.getElementById('lastSid'),
  };
}

export function renderEmptyProblem(dom) {
  dom.problemTitle.textContent = '(no problem)';
  dom.problemId.textContent = '';
  dom.timeLimitPill.textContent = 'Time: -';
  dom.memLimitPill.textContent = 'Memory: -';
  if (dom.sampleCountPill) dom.sampleCountPill.textContent = 'Samples: -';
  dom.statementBox.textContent = '(no statement)';
  dom.samplesBox.innerHTML = '<span class="muted">(no samples)</span>';
  dom.langSelect.innerHTML = '';
}

export function renderProblemList(dom, problems) {
  dom.problemSelect.innerHTML = '';
  for (const p of problems) {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = `${p.id}. ${p.title}`;
    dom.problemSelect.appendChild(opt);
  }
}

export function renderProblemInfo(dom, info) {
  dom.problemTitle.textContent = info.title || info.id;
  dom.problemId.textContent = `(${info.id})`;

  dom.timeLimitPill.textContent = `Time: ${info.time_limit_ms ?? '-'} ms`;
  dom.memLimitPill.textContent = `Memory: ${info.memory_limit_mb ?? '-'} MB`;
  if (dom.sampleCountPill) dom.sampleCountPill.textContent = `Samples: ${info.sample_count ?? '-'} shown`;

  dom.statementBox.innerHTML = renderMarkdown(info.statement || '(no statement)');

  const samples = info.samples || [];
  if (!samples.length) {
    dom.samplesBox.innerHTML = '<span class="muted">(no samples)</span>';
  } else {
    let html = '';
    for (const s of samples) {
      html += `
        <div class="sample-title">Sample ${escapeHtml(s.name)}</div>
        <div class="two">
          <div>
            <div class="muted small" style="margin:0 0 6px;">Input</div>
            <pre>${escapeHtml(s.input)}</pre>
          </div>
          <div>
            <div class="muted small" style="margin:0 0 6px;">Output</div>
            <pre>${escapeHtml(s.output)}</pre>
          </div>
        </div>
      `;
    }
    dom.samplesBox.innerHTML = html;
  }

  const langs = info.languages || ['python3'];
  dom.langSelect.innerHTML = '';
  for (const l of langs) {
    const opt = document.createElement('option');
    opt.value = l;
    opt.textContent = l;
    dom.langSelect.appendChild(opt);
  }
  if (info.default_language && langs.includes(info.default_language)) {
    dom.langSelect.value = info.default_language;
  }
}

export function renderSubmitting(dom) {
  dom.statusText.textContent = 'Submitting...';
  dom.resultHint.textContent = '제출 중...';
  dom.resultHint.className = 'muted';
  dom.resultBox.textContent = '(submitting...)';
  dom.lastSid.textContent = '';
}

export function renderSubmitError(dom, errText) {
  dom.statusText.textContent = 'Submit failed';
  dom.resultHint.textContent = '제출 실패';
  dom.resultHint.className = 'muted danger';
  dom.resultBox.textContent = errText;
}

export function renderSubmitted(dom, sid) {
  dom.lastSid.textContent = sid ? `submission_id: ${sid}` : '';
  dom.statusText.textContent = 'Submitted';
  dom.resultHint.textContent = '결과 대기 중...';
  dom.resultHint.className = 'muted';
}

export function renderPollingError(dom, errText) {
  dom.statusText.textContent = 'Status: ERROR';
  dom.resultHint.textContent = 'Result: Error';
  dom.resultHint.className = 'muted danger';
  dom.resultBox.textContent = errText;
}

export function renderResult(dom, data) {
  const stRaw = (data?.status || '').toUpperCase();
  const ui = STATUS_TO_UI[stRaw] || { label: stRaw || '(unknown)', cls: 'muted', done: false };

  dom.resultHint.textContent = `Result: ${ui.label}`;
  dom.resultHint.className = `muted ${ui.cls === 'muted' ? '' : ui.cls}`.trim();

  if (data?.submission_id) dom.lastSid.textContent = `submission_id: ${data.submission_id}`;
  dom.statusText.textContent = stRaw ? `Status: ${stRaw}` : 'Status: (unknown)';

  const lines = [];
  lines.push(`status: ${stRaw || '(unknown)'}`);

  const userName = (data?.user_name || '').trim();
  if (userName) lines.push(`user_name: ${userName}`);

  const result = data?.result ?? '';
  const detail = data?.detail ?? '';

  if (result) {
    lines.push('');
    lines.push('[result]');
    lines.push(String(result));
  }
  if (detail) {
    lines.push('');
    lines.push('[detail]');
    lines.push(String(detail));
  }
  if (!result && !detail) {
    lines.push('');
    lines.push('[raw]');
    lines.push(JSON.stringify(data, null, 2));
  }

  dom.resultBox.textContent = lines.join('\n');
  return ui.done;
}