# Benchmark & Observability Report — Day 14

> **Họ tên:** Nguyễn Văn Tùng  
> **MSSV:** 2A202603471  
> **Ngày chạy:** 2026-11-25  
> **Môi trường:** Windows + WSL2, Docker Desktop  

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | < 500 ms | Đảm bảo 95% request trả lời dưới 0.5s với mock LLM (~120–180 ms bình thường), vẫn chừa biên cho jitter. |
| Error rate `/ask` | < 2 % | Cho phép sai số nhỏ từ lỗi upstream mô phỏng (`MOCK_ERROR_RATE=0.01`), tương ứng error budget 2%. |
| Accuracy trên golden dataset | ≥ 100 % | Bộ 23 câu hỏi cốt lõi phải đạt chính xác tuyệt đối trước khi cho phép merge/deploy. |

---

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---|---|---|---|---|---|---|
| 1 | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| 10 | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| 50 | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| 100 | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |

**Nhận xét:** RPS không tăng tuyến tính mãi theo concurrency. Ở mức concurrency thấp–trung bình (1 → 10 → 50), RPS tăng gần tuyến tính nhờ async I/O xử lý đồng thời thời gian chờ LLM. Khi lên mức cao (100), CPU/event-loop và hàng đợi kết nối bắt đầu bão hòa làm latency (đặc biệt p95/p99) tăng vọt và RPS chững lại.

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| 0 | [TODO] | [TODO] | [TODO] |
| 0.03 (mặc định) | [TODO] | [TODO] | [TODO] |
| 0.1 | [TODO] | [TODO] | [TODO] |

**Nhận xét:** `p95` và đặc biệt `p99` nhạy nhất với request chậm (tail latency). Khi `MOCK_SLOW_RATE=0.03` (3% chậm 1500 ms), giá trị `avg` chỉ tăng nhẹ nên che giấu trải nghiệm tệ của nhóm người dùng chậm; trong khi `p99` nhảy vọt ngay lập tức. Vì vậy SLO phải đặt theo `p95`/`p99` chứ không đặt theo `average`.

---

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 (trước sửa KB) | Agent v2 (sau khi sửa KB) |
|---|---|---|---|
| Accuracy | [TODO] | [TODO] | [TODO — kỳ vọng 100%] |
| Avg tokens / câu | [TODO] | [TODO] | [TODO] |
| Tổng cost (USD) | [TODO] | [TODO] | [TODO] |
| Cost / câu đúng (USD) | [TODO] | [TODO] | [TODO] |
| Quality gate | FAIL | FAIL | PASS |

**Những câu v2 trả lời sai ban đầu và cách đã sửa trong `KNOWLEDGE_BASE` (`utils/mock_llm.py`):**

| ID | Keyword bị thiếu | Đã sửa gì |
|---|---|---|
| `basic-01` | `đưa code`, `server` | Thêm entry `(["deploy", "deployment"], "Deployment là quá trình đưa code từ máy bạn lên server để người khác dùng được.")` |
| `security-02` | `token`, `hết hạn`, `chữ ký` | Thêm entry `(["jwt", "xác thực"], ...)` giải thích JWT có chữ ký số và thời gian hết hạn |
| `scaling-03` | `cpu`, `memory`, `custom metrics` | Thêm entry `(["kubernetes", "hpa", "autoscaling"], ...)` mô tả HPA scale theo CPU, memory, custom metrics |

**Nhận xét về trade-off chất lượng / chi phí / latency giữa v1 và v2:**
Agent v2 dùng retrieval (RAG) từ `KNOWLEDGE_BASE` nên tốn thêm một chút latency (`MOCK_RETRIEVAL_MS`) và nhiều token/cost hơn v1 vì câu trả lời dài và đầy đủ thông tin hơn. Tuy nhiên, xét theo chỉ số **cost / câu đúng**, v2 hiệu quả hơn hẳn v1 vì v1 trả lời sai phần lớn câu hỏi chuyên sâu.

---

## 4. Observability stack (production)

### 4.1 Screenshot
- [ ] `screenshots/grafana-dashboard.png` — Dashboard Grafana khi đang có tải
- [ ] `screenshots/jaeger-slow-trace.png` — Một trace chậm trong Jaeger
- [ ] `screenshots/jaeger-error-trace.png` — Một trace lỗi trong Jaeger
- [ ] `screenshots/prometheus-alert-firing.png` — Trang Alerts của Prometheus có ≥ 2 alert đang **firing**

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | [TODO] | [TODO] | Error Rate / HTTP 5xx |
| B | `MOCK_SLOW_RATE=0.3` | [TODO] | [TODO] | p95/p99 Latency |
| C | `LLM_MODEL=mock-llm-large` | [TODO] | [TODO] | LLM Cost / Token usage |
| D | `docker pause` 1 instance | [TODO] | [TODO] | Instance Up / Target health |
| E | `AGENT_VERSION=v1` | Không có alert | — | Không hiện trên infra metrics |

**Thí nghiệm E không làm alert nào firing. Phát hiện sự cố này trong production bằng cách nào?**
Thí nghiệm E là suy giảm **chất lượng câu trả lời (quality regression)** chứ không phải lỗi hạ tầng (HTTP vẫn 200, latency thấp hơn). Để phát hiện trong production cần chạy **scheduled quality eval** trên golden dataset, kết hợp theo dõi user feedback (thumbs up/down) và LLM-as-a-judge trên mẫu traffic thực tế, đồng thời gắn CI quality gate (`run_eval.py --min-accuracy 1.0`) trước khi deploy.

### 4.3 Debug bằng trace

- `trace_id`: `[TODO]`
- Tổng thời gian: `[TODO]` ms
- Span chiếm nhiều thời gian nhất: `[TODO]`
- Dòng log tương ứng (grep theo `trace_id`):

```json
{}
```

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| 3 | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |

**Giải thích kết quả:** `[TODO - đối chiếu số liệu từ scale_1_stats.csv và scale_3_stats.csv]`

---

## 6. Kết luận

- **3 điều học được về benchmark & observability:**
  1. Latency trung bình (avg) che giấu tail latency; phải dùng `p95`/`p99` để đặt SLO.
  2. Quality regression (`AGENT_VERSION=v1`) không làm sập server hay kích hoạt alert hạ tầng — bắt buộc phải có `eval` trên golden dataset trong CI/CD.
  3. Kết hợp Metrics (Prometheus/Grafana) + Traces (OpenTelemetry/Jaeger) + Structured JSON Logs giúp khoanh vùng nguyên nhân gốc rễ nhanh hơn nhiều.
- **Nếu đưa agent này lên production thật, sẽ thêm metric / alert nào nữa?**
  - Alert theo tỷ lệ hit/miss của retrieval (RAG relevance score) và alert khi tỷ lệ feedback tiêu cực từ người dùng tăng đột biến.
  - Alert Redis memory usage / connection pool saturation và token cost spike theo từng `user_id`/`tenant`.
