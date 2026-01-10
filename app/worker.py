import os, json, tempfile, subprocess, resource
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/data")
TIME_LIMIT_SEC = 2.0

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

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

        r.hset(key, mapping={"status": "RUNNING"})
        verdict, detail = judge(sub["problem_id"], sub["code"])
        r.hset(key, mapping={"status": "DONE", "result": verdict, "detail": detail})

if __name__ == "__main__":
    main()
