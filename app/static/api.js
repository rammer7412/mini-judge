export async function fetchProblems() {
  const res = await fetch('/problems');
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function fetchProblemDetail(problemId) {
  const res = await fetch(`/problems/${encodeURIComponent(problemId)}`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function submitCode(problemId, language, code) {
  const res = await fetch(`/problems/${encodeURIComponent(problemId)}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, language }),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json(); // { submission_id: ... }
}

export async function fetchSubmission(submissionId, signal) {
  const res = await fetch(`/submissions/${submissionId}`, { signal });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}
