import { escapeHtml, renderMarkdown } from './utils.js';

export const STATUS_TO_SHORT = {
  QUEUED: 'QUEUED',
  RUNNING: 'RUNNING',
  ACCEPTED: 'AC',
  WRONG_ANSWER: 'WA',
  TIME_LIMIT_EXCEEDED: 'TLE',
  MEMORY_LIMIT_EXCEEDED: 'MLE',
  RUNTIME_ERROR: 'RE',
  COMPILATION_ERROR: 'CE',
  INTERNAL_ERROR: 'IE',
};

const STATUS_TO_UI = {
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

    resultProblem: document.getElementById('resultProblem'),
    resultUser: document.getElementById('resultUser'),
    resultCode: document.getElementById('resultCode'),
    resultDesc: document.getElementById('resultDesc'),
    resultDetailWrap: document.getElementById('resultDetailWrap'),
    resultDetail: document.getElementById('resultDetail'),
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

  if (dom.resultProblem) dom.resultProblem.textContent = dom.problemSelect?.value || '-';
  if (dom.resultUser) dom.resultUser.textContent = (dom.userNameInput?.value || '').trim() || '-';

  if (dom.resultCode) {
    dom.resultCode.textContent = '...';
    dom.resultCode.className = 'result-code muted';
  }

  if (dom.resultDetailWrap) dom.resultDetailWrap.style.display = 'none';
}

export function renderSubmitError(dom, errText) {
  dom.statusText.textContent = 'Submit failed';

  if (dom.resultCode) {
    dom.resultCode.textContent = 'ERR';
    dom.resultCode.className = 'result-code danger';
  }

  if (dom.resultDetailWrap && dom.resultDetail) {
    dom.resultDetailWrap.style.display = 'block';
    dom.resultDetail.textContent = String(errText || '(no detail)');
  }
}

export function renderSubmitted(dom, sid) {
  dom.statusText.textContent = 'Judging...';

  if (dom.resultProblem) dom.resultProblem.textContent = dom.problemSelect?.value || '-';
  if (dom.resultUser) dom.resultUser.textContent = (dom.userNameInput?.value || '').trim() || '-';

  if (dom.resultCode) {
    dom.resultCode.textContent = '...';
    dom.resultCode.className = 'result-code muted';
  }

  // sid/details are hidden by default
  if (dom.resultDetailWrap) dom.resultDetailWrap.style.display = 'none';
  if (dom.resultDetail) dom.resultDetail.textContent = '';
}

export function renderPollingError(dom, errText) {
  dom.statusText.textContent = 'Status: ERROR';

  if (dom.resultCode) {
    dom.resultCode.textContent = 'ERR';
    dom.resultCode.className = 'result-code danger';
  }

  if (dom.resultDetailWrap && dom.resultDetail) {
    dom.resultDetailWrap.style.display = 'block';
    dom.resultDetail.textContent = String(errText || '(no detail)');
  }
}

export function renderResult(dom, data) {
  const stRaw = (data?.status || '').toUpperCase();
  const ui = STATUS_TO_UI[stRaw] || { label: stRaw || '(unknown)', cls: 'muted', done: false };
  const short = STATUS_TO_SHORT[stRaw] || (stRaw || '(unknown)');

  if (dom.resultProblem) dom.resultProblem.textContent = (data?.problem_id || dom.problemSelect?.value || '-');
  if (dom.resultUser) dom.resultUser.textContent = (data?.user_name || '').trim() || (dom.userNameInput?.value || '').trim() || '-';

  if (dom.resultCode) {
    dom.resultCode.textContent = short;
    dom.resultCode.className = `result-code ${ui.cls === 'muted' ? 'muted' : ui.cls}`.trim();
  }

  dom.statusText.textContent = stRaw ? `Status: ${stRaw}` : 'Status: (unknown)';

  const result = data?.result ?? '';
  const detail = data?.detail ?? '';

  const showDetail = Boolean(result || detail || data?.submission_id);
  if (dom.resultDetailWrap && dom.resultDetail) {
    if (!showDetail) {
      dom.resultDetailWrap.style.display = 'none';
    } else {
      dom.resultDetailWrap.style.display = 'block';
      const lines = [];
      if (data?.submission_id) lines.push(`submission_id: ${data.submission_id}`);
      lines.push(`status: ${stRaw || '(unknown)'}`);
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
      dom.resultDetail.textContent = lines.join('\n');
    }
  }

  return ui.done;
}

