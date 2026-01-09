# Mini Judge (MVP)

A minimal online judge you can run for tutoring assignments. Students submit **Python 3** code, the server runs it against per-problem testcases, and returns a verdict (**AC/WA/TLE/RE**).  
This MVP uses **FastAPI** (with built-in Swagger UI), **Redis** as a queue, and a **worker** process that executes submissions with basic resource limits.

---

## Description

- **Language**: Python 3 (standard library only)
- **API**: FastAPI + Uvicorn (Swagger UI at `/docs`)
- **Queue/State**: Redis
- **Judge Worker**: runs user code via `python3 -I` and compares stdout with expected outputs
- **Deploy**: OCI (Oracle Cloud Infrastructure) Ubuntu VM + Docker Compose

---

## Project Architecture

### High-level components

- **api** (FastAPI)
  - Accepts submissions
  - Pushes jobs to Redis queue
  - Exposes submission status/result endpoints
- **worker**
  - Pops jobs from Redis queue
  - Executes code with time/memory/file limits
  - Produces verdict and stores result back to Redis
- **redis**
  - Stores job queue and submission status/result

### Repository tree (example)

```
mini-judge/
├── docker-compose.yml
├── app/
│   ├── main.py              # FastAPI endpoints: submit + result query
│   ├── worker.py            # Judge worker: executes code and compares outputs
│   └── requirements.txt     # FastAPI/Redis deps
└── data/
    └── problems/
        └── <problem_id>/
            └── tests/
                ├── 1.in
                ├── 1.out
                ├── 2.in
                ├── 2.out
                └── ...
```

---

## Prerequisites

- Ubuntu 22.04 VM (OCI)
- Docker + Docker Compose installed
- OCI networking configured:
  - Inbound **TCP 22** for SSH
  - Inbound **TCP 80** for HTTP (Swagger/UI access)

> Notes:
> - Even if the service is running correctly on the VM (`curl http://localhost/docs` works), you **must** open TCP 80 in OCI Security List ingress rules to access it from your PC browser.

---

## Deploy

### 1) SSH into the VM

**Windows PowerShell example:**
```powershell
ssh -i "C:\path\to\your_private_key.key" ubuntu@<PUBLIC_IP>
```

**Important**
- Never commit the SSH private key to GitHub (even if you add it to `.gitignore` later).
- If SSH fails with a permissions warning on Windows, ensure the private key file is not publicly readable.

### 2) Fix Docker permission denied (if needed)

If you see:
`permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock`

Run:
```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

Test:
```bash
docker run --rm hello-world
```

### 3) Start the services

From your project directory on the VM:
```bash
cd ~/mini-judge
docker compose up -d --build
docker compose ps
```

### 4) Confirm the API is healthy (inside the VM)

```bash
curl -s http://localhost/health
curl -I http://localhost/docs
```

### 5) Open Swagger UI from your PC

In your browser:
- `http://<PUBLIC_IP>/docs`

### 6) Add a sample problem (testcases)

Problems are identified by the folder name under `data/problems/<problem_id>/tests`.

Example: create a `sum` problem:
```bash
cd ~/mini-judge
mkdir -p data/problems/sum/tests
printf "1 2\n" > data/problems/sum/tests/1.in
printf "3\n"   > data/problems/sum/tests/1.out
```

### 7) Submit and check results (via Swagger)

- Submit endpoint: `POST /problems/{problem_id}/submit`
  - Set `problem_id` to your folder name (e.g., `sum`)
  - Body example:

```json
{
  "code": "a, b = map(int, input().split())\nprint(a + b)\n"
}
```

- Result endpoint: `GET /submissions/{submission_id}`
  - Expect: `status=DONE`, `result=AC`, `detail=All tests passed`

---

## Troubleshooting

### 1) Docker daemon socket permission denied
Symptom:
- `permission denied while trying to connect to the Docker daemon socket ...`

Fix:
```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
docker run --rm hello-world
```

### 2) Works on VM, but not in your browser (most common)
Symptom:
- VM: `curl -I http://localhost/docs` returns `200 OK`
- PC: cannot connect to `http://<PUBLIC_IP>/docs`

Cause:
- OCI inbound rule for port 80 is missing or incorrect.

Fix (OCI Console):
- Subnet **Security List** → **Ingress Rules**
  - Source CIDR: `0.0.0.0/0`
  - Protocol: TCP
  - **Destination Port Range: 80**

Common mistake:
- Setting **Source Port Range = 80** and **Destination = All**  
  This does **not** open the server’s port 80 for browsers.

### 3) Port 80 is not listening
Check on the VM:
```bash
sudo ss -lntp | grep ':80'
docker compose ps
```
Expected:
- `LISTEN` on `0.0.0.0:80`
- `docker compose ps` shows mapping `0.0.0.0:80->8000/tcp`

If not, restart:
```bash
docker compose down
docker compose up -d --build
```

### 4) Swagger submission returns 404 (Problem not found)
Cause:
- `problem_id` does not match an existing folder under `data/problems/`.

Fix:
- Confirm folder names:
```bash
ls data/problems
```
- Use the exact folder name as `problem_id` (e.g., `sum`).

### 5) Submission stuck in QUEUED
Cause:
- Worker container not running.

Fix:
```bash
docker compose ps
docker compose logs -n 100 worker
```
