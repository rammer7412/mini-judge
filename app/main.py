import os, uuid, json, time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/data")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="Mini Judge (MVP)")

class SubmitReq(BaseModel):
    code: str

def problem_dir(problem_id: str) -> str:
    return os.path.join(DATA_DIR, "problems", problem_id)

# -----------------------
# Student Web UI (MVP)
# -----------------------
INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Mini Judge</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 980px; margin: 24px auto; padding: 0 16px; }
    h1 { margin-bottom: 6px; }
    .muted { color: #666; margin-top: 0; }
    .row { margin: 12px 0; }
    label { font-weight: 600; display: block; margin-bottom: 6px; }
    input { padding: 10px; width: 260px; border: 1px solid #ccc; border-radius: 8px; }
    textarea { width: 100%; height: 420px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 14px; border: 1px solid #ccc; border-radius: 8px; padding: 12px; }
    button { padding: 10px 16px; border: none; border-radius: 10px; cursor: pointer; font-weight: 700; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    .badge { display:inline-block; padding: 4px 10px; border-radius: 999px; background: #f1f3f5; font-size: 13px; }
    pre { background:#f6f8fa; padding: 12px; border-radius: 10px; overflow:auto; border: 1px solid #eee; }
    .grid { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  </style>
</head>
<body>
  <h1>Mini Judge</h1>
  <p class="muted">Submit Python 3 code → run testcases → get AC/WA/TLE/RE</p>

  <div class="row grid">
    <div>
      <label>Problem ID</label>
      <input id="problemId" value="sum" />
    </div>
    <div>
      <label>Status</label>
      <span id="status" class="badge">idle</span>
    </div>
    <div style="flex:1"></div>
    <div>
      <button id="submitBtn">Submit</button>
    </div>
  </div>

  <div class="row">
    <label>Python Code</label>
    <textarea id="code">a, b = map(int, input().split())
print(a + b)
</textarea>
  </div>

  <div class="row">
    <label>Result</label>
    <pre id="result">(empty)</pre>
  </div>

<script>
const $ = (id) => document.getElementById(id);

async function sleep(ms){ return new Promise(r => setTimeout(r, ms)); }

function setBusy(busy){
  $("submitBtn").disabled = busy;
}

async function pollResult(sid) {
  while(true){
    const res = await fetch(`/submissions/${sid}`);
    const data = await res.json();
    $("status").innerText = data.status || "UNKNOWN";
    $("result").innerText = JSON.stringify(data, null, 2);

    if (data.status === "DONE") break;
    await sleep(400);
  }
}

$("submitBtn").addEventListener("click", async () => {
  setBusy(true);
  $("status").innerText = "submitting...";
  $("result").innerText = "";

  const problemId = $("problemId").value.trim();
  const code = $("code").value;

  const res = await fetch(`/problems/${encodeURIComponent(problemId)}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code })
  });

  if(!res.ok){
    const t = await res.text();
    $("status").innerText = "error";
    $("result").innerText = t;
    setBusy(false);
    return;
  }

  const obj = await res.json();
  const sid = obj.submission_id;
  $("status").innerText = "QUEUED";
  $("result").innerText = JSON.stringify(obj, null, 2);

  await pollResult(sid);
  setBusy(false);
});
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML

# -----------------------
# API
# -----------------------
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/problems/{problem_id}/submit")
def submit(problem_id: str, req: SubmitReq):
    pdir = problem_dir(problem_id)
    tdir = os.path.join(pdir, "tests")
    if not os.path.isdir(tdir):
        raise HTTPException(404, f"Problem '{problem_id}' not found (missing tests folder).")

    sid = str(uuid.uuid4())
    payload = {"id": sid, "problem_id": problem_id, "code": req.code, "ts": time.time()}
    r.hset(f"sub:{sid}", mapping={"status": "QUEUED", "result": "", "detail": ""})
    r.rpush("queue:submissions", json.dumps(payload))
    return {"submission_id": sid}

@app.get("/submissions/{sid}")
def get_result(sid: str):
    key = f"sub:{sid}"
    if not r.exists(key):
        raise HTTPException(404, "submission not found")
    data = r.hgetall(key)
    return {"submission_id": sid, **data}
