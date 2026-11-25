# Benchmark & Observability Report — Day 14

- **Họ tên:** Nguyễn Văn Tùng
- **MSSV:** 2A202603471
- **Ngày chạy:** 25/11/2026
- **Môi trường:** Windows + WSL2 Ubuntu, Docker Desktop

---

## 1. SLO của agent

| SLI | SLO | Lý do |
|---|---|---|
| p95 latency `/ask` | < 500 ms | Request bình thường khoảng 150–250ms, đặt 500ms để chừa khoảng cho jitter |
| Error rate `/ask` | < 2 % | Mock LLM có tỷ lệ lỗi giả lập 1% (`MOCK_ERROR_RATE=0.01`) |
| Accuracy trên golden dataset | ≥ 100 % | Đảm bảo 23 câu hỏi cơ bản trong bộ test không bị trả lời sai khi sửa code |

---

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---|---|---|---|---|---|---|
| 1 | 4.0 | 192.8 | 222.8 | 1710.9 | 0.33% | PASS |
| 10 | 40.54 | 187.6 | 221.7 | 1688.4 | 1.67% | PASS |
| 50 | 105.57 | 197.5 | 250.9 | 1702.6 | 1.33% | PASS |
| 100 | 65.82 | 332.4 | 2968.5 | 3255.4 | 1.00% | FAIL |

**Nhận xét:** RPS chỉ tăng gần tuyến tính từ 1 lên 50 (4.0 -> 40.54 -> 105.57 req/s). Khi tăng lên 100 thì server bị nghẽn, RPS tụt xuống 65.82 và p95 vọt lên 2968.5ms (vượt SLO 500ms).

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| 0 | 190.8 | 217.6 | 231.9 |
| 0.03 (mặc định) | 250.9 | 226.8 | 1703.9 |
| 0.1 | 315.9 | 1683.3 | 1712.0 |

**Nhận xét:** `p99` và `p95` nhạy nhất khi có request chậm. Ở mức 0.03, `avg` chỉ là 250.9ms nhưng `p99` đã lên tới 1703.9ms, nên đặt SLO theo `avg` sẽ không phát hiện được nhóm user bị chậm.

---

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 (sau khi sửa KB) |
|---|---|---|
| Accuracy | 4.35% (1/23) | 100.0% (23/23) |
| Avg tokens / câu | 56.3 | 113.7 |
| Tổng cost (USD) | $0.000394 | $0.000787 |
| Cost / câu đúng (USD) | $0.00039375 | $0.00003420 |
| Quality gate | FAIL | PASS |

**Các câu đã bổ sung vào `KNOWLEDGE_BASE` (`utils/mock_llm.py`):**

| ID | Keyword bị thiếu | Đã sửa |
|---|---|---|
| `basic-01` | `đưa code`, `server` | Thêm entry về `deploy` / `deployment` |
| `security-02` | `token`, `hết hạn`, `chữ ký` | Thêm entry giải thích JWT có chữ ký số và thời hạn |
| `scaling-03` | `cpu`, `memory`, `custom metrics` | Thêm entry về Kubernetes HPA |

**Nhận xét:** v2 tốn gần gấp đôi token và cost tổng so với v1 vì có thêm bước retrieval, nhưng tính trên mỗi câu trả lời đúng thì v2 rẻ hơn rất nhiều ($0.0000342 so với $0.00039375) và đạt 100% accuracy.

---

## 4. Kết luận
1. Không dùng latency trung bình để đánh giá hiệu năng vì nó che mất tail latency (`p95`/`p99`).
2. Cần chạy eval trên golden dataset trước khi deploy để tránh lỗi giảm chất lượng câu trả lời mà metric hạ tầng không bắt được.
3. Kết hợp log JSON, Prometheus metrics và trace giúp tìm nguyên nhân chậm/lỗi nhanh hơn.
