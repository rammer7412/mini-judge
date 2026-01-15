# Mini Judge (MVP)

A minimal online judge for tutoring assignments.

Students enter a **User Name** and submit **Python 3** code in the web UI. The server runs the code against per-problem testcases and returns a verdict such as **AC/WA/TLE/RE**.

- **Language**: Python 3 (standard library only)
- **API**: FastAPI + Uvicorn (Swagger UI at `/docs`)
- **Queue/State**: Redis
- **Judge Worker**: executes submissions and compares stdout with expected outputs
- **Logs**: per-problem **JSONL** submission log files
- **Deploy**: OCI (Oracle Cloud Infrastructure) Ubuntu VM + Docker Compose

> ⚠️ Note: This is an MVP for learning/tutoring. If you plan to expose it publicly, you should harden security (sandboxing, network isolation, rate limiting, etc.).

---

## Features

### Web UI
- Select a problem → write code → submit → view result
- **User Name is required** (submission is blocked if empty)
- `statement.md` is rendered as **Markdown** (not raw `#` text)
- Result view is simplified:
  - **Problem**
  - **User Name**
  - **Result** (AC/WA/TLE/RE/…)
  - plus a small legend explaining verdict codes

### Problem format

Problems live under `data/problems/<problem_id>/`:

```
data/problems/<problem_id>/
├── meta.json
├── statement.md
└── tests/
    ├── 1.in
    ├── 1.out
    ├── 2.in
    ├── 2.out
    └── ...
```

- `problem_id` is typically a **5-digit string** (e.g., `00001`).
- Testcases are paired by index: `k.in` and `k.out`.

### Submission logging (JSONL)

Every finished submission is appended to a JSONL file per problem:

- `data/submissions/problem_<problem_id>.jsonl`

Each line is one JSON object (easy to parse later).  
Timestamps include **KST (Asia/Seoul)** human-readable fields.

---

## Project Architecture

### High-level components

- **api** (FastAPI)
  - serves the Web UI (static files)
  - lists problems and problem details
  - accepts submissions and enqueues jobs in Redis
  - returns final verdict/result
- **worker**
  - pops jobs from Redis
  - executes user code with basic time limits
  - compares output with expected answers
  - writes verdict back to Redis
  - appends a JSONL log record on completion
- **redis**
  - job queue + submission status/result store

### Repository tree (example)

```
mini-judge/
├── docker-compose.yml
├── app/
│   ├── main.py
│   ├── worker.py
│   ├── requirements.txt
│   └── static/
│       ├── index.html
│       ├── style.css
│       ├── ui.js
│       └── utils.js
└── data/
    ├── problems/
    │   └── 00001/
    │       ├── meta.json
    │       ├── statement.md
    │       └── tests/
    │           ├── 1.in
    │           ├── 1.out
    │           └── ...
    └── submissions/
        └── problem_00001.jsonl
```

---

## Prerequisites

- Ubuntu 22.04 VM (OCI)
- Docker + Docker Compose installed
- OCI networking rules:
  - Inbound **TCP 22** for SSH
  - Inbound **TCP 80** for HTTP (Web UI / Swagger)

> Even if `curl http://localhost/docs` works on the VM, you must open inbound TCP **80** in OCI security rules to access it from your local PC.

---

## Deploy (OCI)

### 1) SSH into the VM

PowerShell example:

```powershell
ssh -i "C:\path\to\your_private_key.key" ubuntu@<PUBLIC_IP>
```

**Important**
- Never commit your SSH private key to GitHub (even temporarily).
- If SSH fails with a permissions warning on Windows, ensure the private key file is not publicly readable.

### 2) Fix Docker permission denied (if needed)

If you see:

`permission denied while trying to connect to the Docker daemon socket ...`

Run:

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
docker run --rm hello-world
```

### 3) Start services

```bash
cd ~/mini-judge
docker compose up -d --build
docker compose ps
```

### 4) Health check (inside the VM)

```bash
curl -s http://localhost/health
curl -I http://localhost/docs
```

### 5) Open UI/Swagger from your PC

- Web UI: `http://<PUBLIC_IP>/`
- Swagger: `http://<PUBLIC_IP>/docs`

---

## Add a sample problem

Example: create problem `00001`:

```bash
cd ~/mini-judge
mkdir -p data/problems/00001/tests

cat > data/problems/00001/meta.json << 'EOF'
{
  "id": "00001",
  "title": "A+B",
  "time_limit_ms": 1000,
  "memory_limit_mb": 256,
  "languages": ["python3"],
  "default_language": "python3",
  "sample_count": 3
}
EOF

cat > data/problems/00001/statement.md << 'EOF'
# A+B

Given two integers A and B, print A+B.

## Input
A and B are given in one line, separated by a space.

## Output
Print A+B.
EOF

printf "1 2\n" > data/problems/00001/tests/1.in
printf "3\n"   > data/problems/00001/tests/1.out
```

---

## Logs: view or download JSONL

### View on the server

```bash
tail -n 50 data/submissions/problem_00001.jsonl
```

### Download to your local PC (Windows)

If you have an SSH config alias (example: `Host mini-judge`), you can use:

```powershell
scp mini-judge:~/mini-judge/data/submissions/problem_00001.jsonl .
```

(You can also automate this using a `.bat` script.)

---

## Troubleshooting

### 1) Works on VM, but not in your browser (most common)

**Symptom**
- VM: `curl -I http://localhost/docs` returns `200 OK`
- PC: cannot connect to `http://<PUBLIC_IP>/docs`

**Cause**
- OCI inbound rule for port 80 is missing or incorrect.

**Fix (OCI Console)**
- Subnet **Security List** → **Ingress Rules**
  - Source CIDR: `0.0.0.0/0`
  - Protocol: TCP
  - **Destination Port Range: 80**

Common mistake:
- Setting **Source Port Range = 80** and **Destination = All**  
  This does **not** open the server’s port 80 for browsers.

### 2) Port 80 is not listening

Check on the VM:

```bash
sudo ss -lntp | grep ':80'
docker compose ps
```

### 3) Swagger returns 404 (Problem not found)

Cause:
- `problem_id` does not match a folder under `data/problems/`.

Fix:

```bash
ls data/problems
```

Use the exact folder name as `problem_id`.

### 4) Submission stuck in QUEUED

Cause:
- worker container not running.

Fix:

```bash
docker compose ps
docker compose logs -n 100 worker
```

---

## Security Notes (MVP)

This system executes user-submitted code. For public exposure, you should consider:
- running submissions in a stricter sandbox (separate container/VM)
- disabling outbound network for user code
- enforcing strict CPU/memory/time limits
- adding rate limiting and authentication if needed
