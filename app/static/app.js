import { fetchProblems, fetchProblemDetail, submitCode } from './api.js';
import {
  getDom,
  renderEmptyProblem,
  renderProblemList,
  renderProblemInfo,
  renderSubmitting,
  renderSubmitError,
  renderSubmitted,
} from './ui.js';
import { pollUntilDone, cancelPolling } from './poller.js';

const dom = getDom();
let problemsCache = [];

async function loadProblems() {
  dom.statusText.textContent = 'Loading problems...';
  try {
    const data = await fetchProblems();
    problemsCache = data.problems || [];

    if (!problemsCache.length) {
      dom.statusText.textContent = 'No problems found (check /data/problems/<id>/tests)';
      renderEmptyProblem(dom);
      return;
    }

    renderProblemList(dom, problemsCache);
    dom.statusText.textContent = 'Ready';
    await loadProblemDetail(dom.problemSelect.value);
  } catch (e) {
    dom.statusText.textContent = 'Failed to load problems';
    renderEmptyProblem(dom);
    dom.resultBox.textContent = String(e);
  }
}

async function loadProblemDetail(problemId) {
  if (!problemId) return;
  dom.statusText.textContent = 'Loading problem detail...';
  try {
    const info = await fetchProblemDetail(problemId);
    renderProblemInfo(dom, info);
    dom.statusText.textContent = 'Ready';
  } catch (e) {
    dom.statusText.textContent = 'Failed to load problem detail';
    dom.resultBox.textContent = String(e);
  }
}

async function onSubmit() {
  const pid = dom.problemSelect.value;
  const lang = dom.langSelect.value;

  if (!pid) {
    alert('문제가 없습니다. 서버의 /data/problems/<id>/tests 를 확인하세요.');
    return;
  }

  // (중요) 재제출하면 이전 폴링 끊기
  cancelPolling();

  renderSubmitting(dom);

  try {
    const data = await submitCode(pid, lang, dom.codeArea.value);
    const sid = data.submission_id;

    renderSubmitted(dom, sid);
    await pollUntilDone(dom, sid);
  } catch (e) {
    renderSubmitError(dom, String(e));
  }
}

dom.submitBtn.addEventListener('click', onSubmit);
dom.problemSelect.addEventListener('change', () => loadProblemDetail(dom.problemSelect.value));

loadProblems();
