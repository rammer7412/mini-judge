import { fetchProblems, fetchProblemDetail, submitCode } from './api.js';
import {
  getDom,
  renderEmptyProblem,
  renderProblemList,
  renderProblemInfo,
  renderSubmitting,
  renderSubmitError,
  renderResult,
} from './ui.js';

const dom = getDom();

// ---------------------------------------------------------------------------
// Username (no auth): store locally so user doesn't need to retype each time
// ---------------------------------------------------------------------------
const NAME_KEY = 'mini_judge_user_name';

function getUserName() {
  const v = (dom.userNameInput?.value || '').trim();
  return v;
}

function initUserName() {
  if (!dom.userNameInput) return;
  const saved = localStorage.getItem(NAME_KEY);
  if (saved) dom.userNameInput.value = saved;
  dom.userNameInput.addEventListener('input', () => {
    localStorage.setItem(NAME_KEY, getUserName());
  });
}

function setSubmitEnabled(enabled) {
  dom.submitBtn.disabled = !enabled;
  dom.submitBtn.style.opacity = enabled ? '1' : '0.6';
  dom.submitBtn.style.cursor = enabled ? 'pointer' : 'not-allowed';
  dom.submitBtn.textContent = enabled ? 'Submit' : 'Judging...';
}

async function loadProblems() {
  dom.statusText.textContent = 'Loading problems...';
  try {
    const data = await fetchProblems();
    const problems = data.problems || [];

    if (!problems.length) {
      dom.statusText.textContent = 'No problems found (check /data/problems/<id>/tests)';
      renderEmptyProblem(dom);
      return;
    }

    renderProblemList(dom, problems);
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
  const userName = getUserName();

  if (!pid) {
    alert('문제가 없습니다. 서버의 /data/problems/<id>/tests 를 확인하세요.');
    return;
  }

  if (!userName) {
    alert('이름을 입력해야 제출할 수 있어요.');
    dom.userNameInput?.focus();
    return;
  }

  // ✅ 제출 순간 비활성화
  setSubmitEnabled(false);

  renderSubmitting(dom);

  try {
    // ✅ 폴링 없이: submit 요청이 채점 완료까지 기다린 뒤 최종 결과 JSON을 반환
    const data = await submitCode(pid, lang, dom.codeArea.value, userName);

    // data = {submission_id, status, result, detail, raw_status}
    renderResult(dom, data);
  } catch (e) {
    renderSubmitError(dom, String(e));
  } finally {
    // ✅ 결과가 나오면 다시 활성화
    setSubmitEnabled(true);
  }
}

dom.submitBtn.addEventListener('click', onSubmit);
dom.problemSelect.addEventListener('change', () => loadProblemDetail(dom.problemSelect.value));

loadProblems();

initUserName();
