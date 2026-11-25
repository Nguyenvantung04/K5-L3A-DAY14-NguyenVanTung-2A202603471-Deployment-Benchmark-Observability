# Day 14 Lab — Mission Answers

- **Họ tên:** Nguyễn Văn Tùng
- **Lớp:** K5-L3A
- **MSSV:** 2A202603471

---

## Part 1: Localhost vs Production

### Exercise 1.1: Các vấn đề trong `01-localhost-vs-production/develop/app.py`
1. Hardcode `OPENAI_API_KEY` và `DATABASE_URL` trực tiếp trong file (dòng 17–18), push lên GitHub là lộ ngay.
2. `DEBUG = True` và `MAX_TOKENS = 500` gắn cứng trong code, muốn đổi theo môi trường phải sửa code.
3. Dùng `print()` để log và còn in luôn cả `OPENAI_API_KEY` ra màn hình (dòng 34).
4. Không có route `/health` hay `/ready` để platform kiểm tra app còn sống không.
5. Gắn cứng `host="localhost"`, `port=8000` và `reload=True` (dòng 49–54) nên không chạy được khi deploy lên container/cloud.

### Exercise 1.2: Chạy thử bản develop
*(Chạy `python app.py` trong `01-localhost-vs-production/develop/` và gọi `curl -X POST "http://localhost:8000/ask?question=Hello"` trả về JSON có key `answer`.)*

### Exercise 1.3: So sánh Develop và Production

| Hạng mục | Develop (`develop/app.py`) | Production (`production/app.py`) | Lý do |
| --- | --- | --- | --- |
| Config | Hardcode key, port, debug | Đọc từ `config.py` qua biến môi trường | Đổi cấu hình dev/prod không cần sửa code, tránh lộ key |
| Health check | Không có | Có `/health` và `/ready` | Platform biết lúc nào app lỗi để restart hoặc ngừng gửi request |
| Logging | `print()` | `logging` xuất dạng JSON | Dễ lọc log và không in nhầm secret |
| Shutdown | Tắt ngang | Dùng `lifespan` set `is_ready = False` rồi chờ request chạy xong | Không làm rớt request của user khi deploy bản mới |
| Host / Port | `localhost:8000`, `reload=True` | `0.0.0.0`, đọc `PORT` từ env | Container và cloud cần bind `0.0.0.0` và đúng cổng được cấp |

---

## Part 2: Docker

### Exercise 2.1: Đọc `02-docker/develop/Dockerfile`
1. Base image là `python:3.11` (bản đầy đủ nên nặng).
2. Working directory là `/app`.
3. `COPY requirements.txt` đặt trước `COPY app.py` để tận dụng cache: khi sửa code Python thì Docker không phải cài lại pip từ đầu.
4. `ENTRYPOINT` là lệnh chạy cố định khó ghi đè, còn `CMD` là lệnh/tham số mặc định có thể truyền đè lúc `docker run`.

### Exercise 2.3: Multi-stage build (`02-docker/production/Dockerfile`)
- Stage 1 (`builder`): dùng `python:3.11-slim`, cài `gcc`, `libpq-dev` và pip packages vào `/root/.local`.
- Stage 2 (`runtime`): dùng `python:3.11-slim` mới, tạo user `appuser` (không chạy root), chỉ copy `/root/.local` và code qua nên bỏ được đống build tools ở stage 1, image nhẹ hơn nhiều.

### Exercise 2.4: Docker Compose (`02-docker/production/docker-compose.yml`)
```text
Client -> nginx (80/443) -> agent (8000) -> redis (6379)
                                         -> qdrant (6333)
```
Các container gọi nhau qua mạng `internal` bằng tên service (`redis`, `qdrant`). Chỉ có `nginx` mở port ra ngoài.

---

## Part 3: Cloud Deployment

### Exercise 3.1 / 3.2: Deploy Part 6
- Public URL: *(cập nhật sau khi deploy xong `06-lab-complete/`)*
- So sánh `railway.toml` và `render.yaml`: `railway.toml` gọn hơn, chỉ khai báo builder `DOCKERFILE` và `healthcheckPath = "/health"`, còn env và Redis chỉnh trên web/CLI; `render.yaml` khai báo luôn cả service, `healthCheckPath` lẫn danh sách `envVars` (`generateValue: true` hoặc `sync: false`) trong một file YAML.

### Exercise 3.3: Pipeline Cloud Run (`03-cloud-deployment/production-cloud-run/`)
`cloudbuild.yaml` chạy 4 bước: chạy `pytest` -> build Docker image (tag theo `$COMMIT_SHA` và `latest`) -> push lên Container Registry -> chạy `gcloud run deploy` ở region `asia-southeast1` với `min-instances=1`, `max-instances=10` và lấy secret từ Secret Manager. File `service.yaml` cấu hình Knative tương ứng gồm `containerConcurrency: 80`, `livenessProbe` (`/health`) và `startupProbe` (`/ready`).

---

## Part 4: API Security

### Exercise 4.4: Cost Guard
- Rate limit chỉ chặn số request mỗi phút, nhưng user vẫn có thể gửi prompt dài để đốt nhiều token. Cost guard tính tiền theo `input_tokens` và `output_tokens` sau mỗi lần gọi LLM rồi cộng dồn vào Redis.
- Trước khi gọi LLM sẽ kiểm tra tổng tiền trong Redis, nếu vượt `DAILY_BUDGET_USD` hoặc `MONTHLY_BUDGET_USD` thì trả HTTP `402`.

---

## Part 5: Scaling & Reliability

- **Khác nhau giữa `/health` và `/ready`:** `/health` kiểm tra process còn chạy không (luôn trả `200` dù Redis mất kết nối để tránh bị restart liên tục), còn `/ready` kiểm tra kết nối Redis (`200` nếu ok, `503` nếu lỗi để load balancer tạm ngưng chuyển traffic vào).
- **Vì sao state trong RAM bị lỗi khi scale:** Chạy `--scale agent=3` thì request 1 có thể vào `agent-1`, request 2 vào `agent-2`. Nếu lưu lịch sử chat trong RAM thì `agent-2` không có dữ liệu của `agent-1`. Lưu tập trung ở Redis giúp các instance dùng chung state.

---

## Part 6: Output `check_production_ready.py`

```text
================================================================
  📋 Checklist Deliverable
     ✅ Dockerfile (multi-stage, < 500 MB)
     ✅ docker-compose.yml (agent + redis)
     ✅ .dockerignore
     ✅ Health check endpoint (GET /health)
     ✅ Readiness endpoint (GET /ready)
     ✅ API Key authentication
     ✅ Rate limiting
     ✅ Cost guard
     ✅ Config từ environment variables
     ✅ Structured logging
     ✅ Graceful shutdown
     ✅ Public URL ready (Railway / Render config)
----------------------------------------------------------------
  Result: 12/12 tiêu chí đạt · 43/43 checks passed
  🎉 PASS 12/12 — PRODUCTION READY! Deploy nào!
================================================================
```

Image build ra nặng `273 MB`, `docker stop` thoát với exit code `0` trong `0.5s`.

---

## AI Log
Có dùng AI hỗ trợ rà lỗi cú pháp Dockerfile, Redis Lua script cho rate limiter và hướng dẫn xử lý lỗi quyền Docker trong WSL2 Ubuntu; toàn bộ script chấm `check_production_ready.py` và benchmark đã tự chạy kiểm tra trên máy.
