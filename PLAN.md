# 📋 PLAN.md — Lab #28: Full Platform Integration Sprint

> **Cập nhật lần cuối:** 2026-05-18 10:53  
> **Trạng thái tổng thể:** 🟡 ~75% hoàn thành (Phase 1-4 xong, cần Kaggle + Screenshots)

---

## ✅ PHASE 1 — Chuẩn bị & Sửa lỗi code

| # | Công việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Tạo file `.env` | ✅ Xong | `/Users/AI_ThucChien/Day28-Lab-Assignment/.env` |
| 1.2 | Sửa `api-gateway/main.py` | ✅ Xong | Error handling, validation 422, circuit breaker, logging |
| 1.3 | Sửa `api-gateway/Dockerfile` | ✅ Xong | Dùng `requirements.txt` đúng cách |
| 1.4 | Sửa `api-gateway/requirements.txt` | ✅ Xong | Fix conflict fastapi + prometheus-fastapi-instrumentator |
| 1.5 | Sửa `docker-compose.yml` | ✅ Xong | Healthchecks, restart policies, Grafana provisioning |
| 1.6 | Fix Prefect command | ✅ Xong | `prefect server start` + `prefect agent start -q default` |
| 1.7 | Tạo `monitoring/alert_rules.yml` | ✅ Xong | **[BONUS]** 3 alert rules |
| 1.8 | Tạo Grafana dashboard JSON | ✅ Xong | **[BONUS]** 5 panels, auto-provision |
| 1.9 | Tạo `scripts/load_test.py` | ✅ Xong | **[BONUS]** async p50/p95/p99 |
| 1.10 | Tạo `kaggle/kaggle_notebook.py` | ✅ Xong | 9 cells đầy đủ |

---

## ✅ PHASE 2 — Dựng Infrastructure Local (Docker Compose)

| # | Công việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | `docker compose up -d --build` | ✅ Xong | 9/9 containers Up |
| 2.2 | Zookeeper (port 2181) | ✅ Up | |
| 2.3 | Kafka (port 9092) | ✅ Up | topic `data.raw` đã tạo |
| 2.4 | Prefect Orion (port 4200) | ✅ Up | http://localhost:4200 |
| 2.5 | Prefect Agent | ✅ Up | `prefect agent start -q default` |
| 2.6 | Qdrant (port 6333) | ✅ Up | collection `documents` đã tạo (5 vectors) |
| 2.7 | Redis (port 6379) | ✅ Up (healthy) | 2 features stored |
| 2.8 | Prometheus (port 9090) | ✅ Up | metrics flowing |
| 2.9 | Grafana (port 3000) | ✅ Up | dashboard auto-provisioned |
| 2.10 | API Gateway (port 8000) | ✅ Up | `/health` trả `{"status":"ok"}` |
| 2.11 | 📸 Screenshot prefect_ui.png | ❌ Chưa | Cần chụp http://localhost:4200 |
| 2.12 | 📸 Screenshot grafana_dashboard.png | ❌ Chưa | Cần chụp http://localhost:3000 |

---

## 🟡 PHASE 3 — Setup Kaggle GPU & Tunnel

| # | Công việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Viết code `kaggle/kaggle_notebook.py` | ✅ Xong | 9 cells đầy đủ |
| 3.2 | Tạo Kaggle Notebook mới | ❌ Chưa | Vào kaggle.com → New Notebook |
| 3.3 | Bật GPU T4 x2 trên Kaggle | ❌ Chưa | Settings → Accelerator → GPU T4 x2 |
| 3.4 | Copy code vào Kaggle (Cell 1-9) | ❌ Chưa | Copy từ `kaggle/kaggle_notebook.py` |
| 3.5 | Điền ngrok token vào Cell 2 | ❌ Chưa | Lấy tại ngrok.com/your-authtoken |
| 3.6 | Chạy Cell 1: Install deps | ❌ Chưa | ~3 phút |
| 3.7 | Chạy Cell 2: Setup ngrok | ❌ Chưa | |
| 3.8 | Chạy Cell 3: Start vLLM | ❌ Chưa | Chờ ~60s load model |
| 3.9 | Chạy Cell 4: Lấy VLLM_URL | ❌ Chưa | Copy URL vào `.env` |
| 3.10 | Chạy Cell 5: Start Embedding | ❌ Chưa | |
| 3.11 | Chạy Cell 6: Lấy EMBED_URL | ❌ Chưa | Copy URL vào `.env` |
| 3.12 | Chạy Cell 7: MLflow tracking | ❌ Chưa | Integration 6+7 |
| 3.13 | Chạy Cell 8: Test pipeline | ❌ Chưa | Verify vLLM + Embedding |
| 3.14 | Cập nhật `.env` với URL thực | ❌ Chưa | `VLLM_NGROK_URL=https://xxx.ngrok-free.app` |
| 3.15 | Restart API Gateway | ❌ Chưa | `docker compose up -d api-gateway` |

---

## ✅ PHASE 4 — Integration Points

| # | Integration | Script | Trạng thái | Kết quả |
|---|---|---|---|---|
| 4.1 | **Int 1:** Data → Kafka | `scripts/01_ingest_to_kafka.py` | ✅ Xong | `doc_001`, `doc_002` sent |
| 4.2 | **Int 2:** Kafka → Prefect → Delta | `prefect/flows/kafka_to_delta.py` | ⚠️ Partial | Cần chạy thủ công sau khi có Prefect flow |
| 4.3 | **Int 3+4:** Delta → Feast (Redis) | `scripts/03_delta_to_feast.py` | ✅ Xong | 2 features in Redis |
| 4.4 | **Int 5:** Embed → Qdrant | `scripts/05_embed_to_qdrant.py` | ✅ Xong | 5 vectors in Qdrant |
| 4.5 | **Int 6+7:** MLflow → Registry | Kaggle Cell 7 | ❌ Chưa | Cần Kaggle notebook |
| 4.6 | **Int 8:** vLLM → API Gateway | `curl POST /api/v1/chat` | ❌ Chưa | Cần VLLM_URL thực |
| 4.7 | **Int 9:** Prometheus Metrics | `scripts/09_verify_observability.py` | ✅ Xong | Metrics flowing |
| 4.8 | **Int 10:** LangSmith Traces | `scripts/09_verify_observability.py` | ❌ Chưa | Cần `LANGCHAIN_API_KEY` thực |

---

## ✅ PHASE 5 — Testing & Validation

| # | Công việc | Trạng thái | Kết quả |
|---|---|---|---|
| 5.1 | Smoke tests (không cần vLLM) | ✅ Xong | **6/6 PASSED** |
| 5.2 | `test_full_inference_returns_200` | ❌ Cần Kaggle | Cần vLLM URL |
| 5.3 | `test_kafka_ingest_and_qdrant_store` | ⚠️ Partial | Cần Prefect flow chạy |
| 5.4 | Production Readiness Check | ✅ Xong | **10/10 = 100%** |
| 5.5 | 📸 Screenshot smoke_tests_results.png | ❌ Chưa | Cần chụp |
| 5.6 | 📸 Screenshot production_readiness.png | ❌ Chưa | Cần chụp |

---

## ❌ PHASE 6 — Documentation & Submission

| # | Công việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 6.1 | Tạo thư mục `screenshots/` | ✅ Xong | Thư mục rỗng |
| 6.2 | Screenshot prefect_ui.png | ❌ Chưa | http://localhost:4200 |
| 6.3 | Screenshot api_gateway.png | ❌ Chưa | curl /api/v1/chat với vLLM URL |
| 6.4 | Screenshot grafana_dashboard.png | ❌ Chưa | http://localhost:3000 |
| 6.5 | Screenshot smoke_tests_results.png | ❌ Chưa | pytest output |
| 6.6 | Screenshot production_readiness.png | ❌ Chưa | readiness script output |
| 6.7 | Trả lời 5 câu hỏi SUBMISSION.md | ❌ Chưa | Xem gợi ý bên dưới |
| 6.8 | Push GitHub | ✅ Xong | `main → 9c93bf8` |

---

## 🔲 VIỆC CÒN LẠI (Theo thứ tự ưu tiên)

### Bước 1 — Setup Kaggle (30 phút)
```
1. Mở https://kaggle.com → New Notebook
2. Settings → Accelerator → GPU T4 x2, Internet → ON
3. Copy từng cell từ kaggle/kaggle_notebook.py vào notebook
4. Cell 2: Điền NGROK_TOKEN = "your_token"
5. Chạy Cell 1 → 8 theo thứ tự
6. Copy VLLM_URL + EMBED_URL từ Cell 4 + Cell 6
```

### Bước 2 — Cập nhật .env (2 phút)
```bash
# Mở file .env và cập nhật:
VLLM_NGROK_URL=https://xxxx.ngrok-free.app   # từ Kaggle Cell 4
EMBED_NGROK_URL=https://yyyy.ngrok-free.app  # từ Kaggle Cell 6
LANGCHAIN_API_KEY=your_actual_key            # từ smith.langchain.com

# Restart API Gateway:
docker compose up -d api-gateway
```

### Bước 3 — Test Integration 8 (2 phút)
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is platform engineering?", "embedding": [0.1, 0.2, 0.3]}'
# Kỳ vọng: JSON với "answer", "latency_ms", "model"
```

### Bước 4 — Chụp Screenshots (10 phút)
```
- http://localhost:4200        → screenshots/prefect_ui.png
- http://localhost:3000        → screenshots/grafana_dashboard.png
- curl /api/v1/chat output     → screenshots/api_gateway.png
- pytest smoke-tests/ -v       → screenshots/smoke_tests_results.png
- python production_readiness  → screenshots/production_readiness.png
```

### Bước 5 — Trả lời 5 câu hỏi SUBMISSION.md (15 phút)
```
Q1: Trade-offs kiến trúc → Hybrid (local cost vs GPU power), Kafka (reliability vs complexity)
Q2: Xử lý ngắt kết nối → Circuit breaker (3 fails → open), timeout 30s, fallback response
Q3: Event-driven Kafka → Decouple producer/consumer, replay, horizontal scaling
Q4: Observability → Logs (Docker/structured), Metrics (Prometheus→Grafana), Traces (LangSmith)
Q5: Service crash → Graceful degradation, Docker restart: unless-stopped, Prefect retry
```

---

## 📊 TỔNG KẾT ĐIỂM DỰ KIẾN

| Tiêu chí | Trọng số | Hiện tại | Sau khi xong Kaggle |
|---|---|---|---|
| Integration Completeness (10 pts) | 40% | ~7/10 (thiếu Int 2, 6+7, 8, 10) | 10/10 ✅ |
| Observability (Prometheus+Grafana+LangSmith) | 25% | ~80% (thiếu LangSmith) | 100% ✅ |
| Performance (load test, latency) | 20% | 70% (chưa có vLLM latency) | 90%+ ✅ |
| Architecture Quality (docs, clean code) | 15% | 90% (thiếu 5 câu hỏi) | 100% ✅ |
| **BONUS (circuit breaker, alerts, dashboard)** | +extra | ✅ Đã có | ✅ |
| **Tổng dự kiến** | | **~75%** | **~95-100%** |

---

## 🔧 BONUS ĐÃ HOÀN THÀNH

| Bonus | File | Trạng thái |
|---|---|---|
| ✅ Grafana Dashboard JSON (5 panels) | `monitoring/grafana-dashboards/lab28-dashboard.json` | Done |
| ✅ Prometheus Alert Rules (3 rules) | `monitoring/alert_rules.yml` | Done |
| ✅ Docker Healthchecks | `docker-compose.yml` | Done |
| ✅ Circuit Breaker Pattern | `api-gateway/main.py` | Done |
| ✅ Async Load Test (p50/p95/p99) | `scripts/load_test.py` | Done |

---

*Cập nhật file này sau mỗi bước hoàn thành.*
