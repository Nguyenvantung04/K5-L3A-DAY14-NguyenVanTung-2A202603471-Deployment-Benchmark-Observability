# Day 14 Lab — Mission Answers

> **Họ và tên:** Nguyễn Văn Tùng  
> **Lớp:** K5-L3A  
> **MSSV:** 2A202603471  

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns trong `01-localhost-vs-production/develop/app.py`
1. **Hardcode secrets trong source code** (dòng 17–18): `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` và `DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"`. Nếu push lên GitHub, bí mật bị lộ ngay lập tức.
2. **Không có config management qua biến môi trường** (dòng 21–22): `DEBUG = True`, `MAX_TOKENS = 500` được gán cứng trong code, không thể thay đổi giữa staging/production mà không sửa code.
3. **Dùng `print()` thay cho structured logging và log cả secret** (dòng 33–34): `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` vừa khó parse trên hệ thống log tập trung (Loki/Datadog), vừa làm lộ API key ra log.
4. **Thiếu endpoint health check (`/health`, `/ready`)**: Khi app bị treo hoặc crash, nền tảng cloud / load balancer không biết để kiểm tra và tự khởi động lại.
5. **Bind cứng `host="localhost"`, `port=8000` và bật `reload=True`** (dòng 49–54): `localhost` không nhận kết nối từ bên ngoài container; `port=8000` không đọc biến `PORT` do Railway/Render cấp; `reload=True` gây tốn tài nguyên và mất an toàn trong production.

### Exercise 1.2: Chạy bản develop
> *(Chạy `python app.py` trong `01-localhost-vs-production/develop/` rồi test `curl -X POST "http://localhost:8000/ask?question=Hello"` và dán output vào đây.)*

### Exercise 1.3: Bảng so sánh Develop vs Production

| Feature | Develop (`develop/app.py`) | Production (`production/app.py`) | Tại sao quan trọng? |
| :--- | :--- | :--- | :--- |
| **Config** | Hardcode `OPENAI_API_KEY`, `DEBUG = True`, `port=8000` | Đọc từ `settings` (`config.py`) qua biến môi trường (`os.getenv`) | Tuân thủ 12-Factor App: đổi cấu hình theo môi trường (dev/staging/prod) mà không cần sửa code, tránh lộ secret. |
| **Health check** | Không có | Có `/health` (liveness) và `/ready` (readiness) | Load balancer và cloud platform dùng để định tuyến traffic và tự động restart container khi gặp sự cố. |
| **Logging** | `print("[DEBUG] ...")`, in cả API key | `logging` với format JSON (`{"time":..., "level":..., "msg":...}`), không log secret | Dễ tìm kiếm, lọc và dựng dashboard/alert trên hệ thống log tập trung; bảo vệ dữ liệu nhạy cảm. |
| **Shutdown** | Thoát đột ngột khi nhận tín hiệu tắt | Dùng `lifespan` trong FastAPI để set `is_ready = False`, đợi request đang chạy hoàn tất | Tránh cắt ngang request của người dùng khi deploy phiên bản mới (zero-downtime deployment). |
| **Network binding** | `host="localhost"`, `reload=True` | `0.0.0.0`, port lấy từ `PORT` env var, tắt reload | Container/cloud yêu cầu bind `0.0.0.0` và lắng nghe đúng cổng platform cấp mới nhận được traffic ngoài. |

---

## Part 2: Docker

### Exercise 2.1: Phân tích `02-docker/develop/Dockerfile`
1. **Base image:** `python:3.11` (bản đầy đủ của Python 3.11, kích thước lớn ~1 GB vì kèm nhiều công cụ hệ thống).
2. **Working directory:** `/app` (`WORKDIR /app`).
3. **Tại sao `COPY requirements.txt` trước `COPY app.py`?** Để tận dụng **Docker layer cache**. `requirements.txt` ít thay đổi hơn source code; khi chỉ sửa `app.py`, Docker tái sử dụng lại layer `pip install` đã cache thay vì cài lại toàn bộ thư viện.
4. **Khác nhau giữa `CMD` và `ENTRYPOINT`:** `ENTRYPOINT` định nghĩa lệnh chính cố định của container (khó bị ghi đè), còn `CMD` cung cấp lệnh/tham số mặc định và dễ dàng bị ghi đè khi truyền tham số lúc `docker run`.

### Exercise 2.2: Build và run bản develop
> *(Dán output lệnh `docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .` và `curl -X POST "http://localhost:8000/ask?question=What%20is%20Docker?"`.)*

### Exercise 2.3: So sánh kích thước image Multi-stage (`02-docker/production/Dockerfile`)
- **Stage 1 (`builder`):** Dùng `python:3.11-slim`, cài `gcc`, `libpq-dev` và chạy `pip install --user -r requirements.txt` vào `/root/.local`.
- **Stage 2 (`runtime`):** Dùng `python:3.11-slim` sạch, tạo non-root user `appuser`, chỉ `COPY --from=builder /root/.local` và code cần chạy, bỏ lại toàn bộ `gcc`/build tools và cache ở stage 1 nên image nhỏ và an toàn hơn nhiều.
- **Kích thước đo bằng `docker images`:**
  - `my-agent:develop`: `[TODO - điền số MB thực tế]` MB
  - `my-agent:advanced`: `[TODO - điền số MB thực tế]` MB
  - Chênh lệch giảm: `[TODO]%`

### Exercise 2.4: Docker Compose stack (`02-docker/production/docker-compose.yml`)
**Sơ đồ kiến trúc:**
```text
Client ──▶ nginx (port 80/443) ──▶ agent (port 8000, internal network)
                                     ├──▶ redis:7-alpine (port 6379, session & rate limit)
                                     └──▶ qdrant:v1.9.0 (port 6333, vector DB)
```
- Các service giao tiếp qua mạng nội bộ `internal` bằng tên service (`redis`, `qdrant`, `agent`). Chỉ `nginx` mở port ra ngoài host.
> *(Dán kết quả test qua Nginx `curl http://localhost/health` vào đây.)*

---

## Part 3: Cloud Deployment

### Exercise 3.1 / 3.2: Deploy Agent Part 6 lên Cloud
- **Public URL:** `[TODO - điền URL Railway/Render sau khi deploy 06-lab-complete/]`
- **So sánh `railway.toml` vs `render.yaml`:**
  - `railway.toml`: Cấu hình ngắn gọn theo định dạng TOML (`[build] builder = "DOCKERFILE"`, `[deploy] healthcheckPath = "/health"`), biến môi trường và Redis service cấu hình trực tiếp trên Railway Dashboard/CLI.
  - `render.yaml`: Dùng Blueprint YAML (`Infrastructure as Code`) khai báo đầy đủ service (`type: web`, `runtime: docker`, `healthCheckPath: /health`) lẫn `envVars` (`generateValue: true` cho secret, `sync: false` cho biến nhập tay) và có thể khai báo kèm Redis trong cùng một file.
- **Screenshots:** `screenshots/dashboard.png`, `screenshots/running.png`, `screenshots/test.png` (xem chi tiết tại `DEPLOYMENT.md`).

### Exercise 3.3: Mô tả pipeline Google Cloud Run (`03-cloud-deployment/production-cloud-run/`)
`cloudbuild.yaml` định nghĩa pipeline CI/CD 4 bước tự động khi push code: (1) chạy `pytest` trong container `python:3.11-slim` để kiểm tra unit test; (2) build Docker image gắn tag `$COMMIT_SHA` và `latest` có dùng `--cache-from`; (3) push image lên Container Registry (`gcr.io/$PROJECT_ID/ai-agent`); (4) chạy `gcloud run deploy` lên region `asia-southeast1` với `min-instances=1`, `max-instances=10`, memory `512Mi` và lấy secret từ Secret Manager. File `service.yaml` (Knative) mô tả cấu hình chạy declarative tương ứng gồm `containerConcurrency: 80`, `livenessProbe` (`/health`) và `startupProbe` (`/ready`).

---

## Part 4: API Security

### Exercise 4.1–4.3: Authentication, JWT & Rate Limiting
> *(Chạy trên máy với `04-api-gateway/` và dán output `curl -i` cho các mã `401`, `200`, `429` — nhớ che JWT token trước khi dán.)*

### Exercise 4.4: Cách làm Cost Guard
- **Tại sao cần cả Rate Limit và Cost Guard?** Rate limit giới hạn **tốc độ** (số request/phút) để chống spam/DDoS, nhưng một người dùng gửi các prompt rất dài vẫn có thể tiêu tốn nhiều token và làm đội chi phí. Cost Guard giới hạn **tổng tiền chi tiêu** (theo ngày/tháng) bằng cách tính chi phí dựa trên `input_tokens` và `output_tokens` sau mỗi lần gọi LLM rồi cộng dồn vào Redis.
- Trước khi gọi LLM (`check_budget()`): đọc tổng chi phí hiện tại trong Redis, nếu `>= DAILY_BUDGET_USD` (hoặc `MONTHLY_BUDGET_USD`) thì trả HTTP **`402 Payment Required`** để chặn phát sinh thêm chi phí.

---

## Part 5: Scaling & Reliability

### Exercise 5.1–5.5: Health Check, Graceful Shutdown & Stateless Scaling
- **Phân biệt Liveness (`/health`) và Readiness (`/ready`):**
  - `GET /health` kiểm tra process ứng dụng còn sống hay không → luôn trả `200` khi server còn chạy (kể cả khi Redis tạm mất kết nối, để platform không restart oan container).
  - `GET /ready` kiểm tra ứng dụng đã sẵn sàng nhận traffic chưa (ping Redis thành công → `200`; mất kết nối Redis → `503`) để Load Balancer tạm ngừng gửi request mới tới instance đó.
- **Tại sao state trong RAM bị hỏng khi scale nhiều instance?** Khi chạy 3 instance sau Nginx Load Balancer (`--scale agent=3`), request 1 có thể vào `agent-1` (lưu hội thoại vào RAM của `agent-1`), nhưng request 2 lại được điều phối sang `agent-2` (RAM không có dữ liệu của request 1). Lưu state tập trung ở **Redis** giúp mọi instance đọc/ghi chung một nguồn dữ liệu, đảm bảo stateless và giữ nguyên lịch sử hội thoại.
- **Kết quả chạy `python test_stateless.py` với `--scale agent=3`:**
> *(Dán output chạy `docker compose -p k5-day14-scaling up -d --build --scale agent=3` và `python test_stateless.py` vào đây.)*

---

## Part 6: Output `check_production_ready.py`

> *(Chạy trong WSL2 tại `06-lab-complete/`: `python check_production_ready.py` và dán phần `📋 Checklist Deliverable` đạt `PASS 12/12` vào đây.)*

---

## AI Log
- **Công cụ sử dụng:** Antigravity AI Assistant.
- **Mục đích sử dụng:** Hướng dẫn lộ trình lab theo `CHECKPOINTS.md`, hỗ trợ hoàn thiện code khung `06-lab-complete/` (FastAPI, Redis rate limiter/cost guard, multi-stage Dockerfile, Docker Compose, Railway/Render config), chạy kiểm tra tĩnh, và cấu trúc tài liệu `MISSION_ANSWERS.md` / `BENCHMARK_REPORT.md`.
- **Kiểm chứng:** Tự chạy lại các lệnh kiểm tra (`check_production_ready.py`, `load_test.py`, `run_eval.py`, `docker compose`) trên máy cá nhân để xác nhận toàn bộ số liệu và kết quả thực tế.
