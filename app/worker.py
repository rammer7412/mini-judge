import os, json, tempfile, subprocess, resource, time, re
from pathlib import Path
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/data")
TIME_LIMIT_SEC = 2.0

SUBMISSION_LOG_DIR = os.getenv("SUBMISSION_LOG_DIR", "/data/submissions")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def _safe_pid(pid: str) -> str:
    pid = str(pid or "unknown")
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", pid)


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def set_limits():
    cpu = int(TIME_LIMIT_SEC) + 1
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    mem = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    fsz = 16 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsz, fsz))

def run_one(code_path, inp_path, timeout):
    with open(inp_path, "rb") as f:
        inp = f.read()
    proc = subprocess.run(
        ["python3", "-I", code_path],
        input=inp,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        preexec_fn=set_limits
    )
    return proc.returncode, proc.stdout, proc.stderr

def normalize(b: bytes) -> bytes:
    return b.strip().replace(b"\r\n", b"\n")

def judge(problem_id, code: str):
    tests_dir = os.path.join(DATA_DIR, "problems", problem_id, "tests")
    ins = sorted([f for f in os.listdir(tests_dir) if f.endswith(".in")])
    if not ins:
        return ("RE", "No testcases found")

    with tempfile.TemporaryDirectory() as td:
        code_path = os.path.join(td, "main.py")
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)

        for inf in ins:
            base = inf[:-3]
            in_path = os.path.join(tests_dir, inf)
            out_path = os.path.join(tests_dir, base + ".out")
            if not os.path.exists(out_path):
                return ("RE", f"Missing output for {inf}")

            try:
                rc, out, err = run_one(code_path, in_path, TIME_LIMIT_SEC)
            except subprocess.TimeoutExpired:
                return ("TLE", f"Time limit exceeded on {inf}")

            if rc != 0:
                return ("RE", f"Runtime error on {inf}")

            with open(out_path, "rb") as f:
                ans = f.read()

            if normalize(out) != normalize(ans):
                return ("WA", f"Wrong answer on {inf}")

        return ("AC", "All tests passed")

def main():
    while True:
        item = r.blpop("queue:submissions", timeout=30)
        if not item:
            continue
        _, raw = item
        sub = json.loads(raw)
        sid = sub["id"]
        key = f"sub:{sid}"

        problem_id = str(sub.get("problem_id") or "")
        language = str(sub.get("language") or "")
        user_name = str(sub.get("user_name") or "").strip()
        submitted_at = float(sub.get("ts") or time.time())

        r.hset(key, mapping={"status": "RUNNING"})

        verdict, detail = judge(problem_id, sub.get("code") or "")
        finished_at = time.time()

        # Redis 기록
        r.hset(
            key,
            mapping={
                "status": "DONE",
                "result": verdict,
                "detail": detail,
                "finished_at": str(finished_at),
            },
        )

        # JSONL 기록 (문제별)
        verdict_map = {
            "AC": "ACCEPTED",
            "WA": "WRONG_ANSWER",
            "TLE": "TIME_LIMIT_EXCEEDED",
            "MLE": "MEMORY_LIMIT_EXCEEDED",
            "RE": "RUNTIME_ERROR",
            "CE": "COMPILATION_ERROR",
            "IE": "INTERNAL_ERROR",
        }
        status_canon = verdict_map.get(str(verdict).upper(), str(verdict).upper())

        record = {
            "submission_id": sid,
            "problem_id": problem_id,
            "language": language,
            "user_name": user_name,
            "submitted_at": submitted_at,
            "finished_at": finished_at,
            "verdict": str(verdict),
            "status": status_canon,
            "detail": detail,
            "code": sub.get("code") or "",
        }

        log_path = Path(SUBMISSION_LOG_DIR) / f"problem_{_safe_pid(problem_id)}.jsonl"
        append_jsonl(log_path, record)

if __name__ == "__main__":
    main()
