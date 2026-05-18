# PLAN.md - Lab #28: Full Platform Integration Sprint

> Cap nhat lan cuoi: 2026-05-18 20:25 ICT
> Trang thai tong the: core lab da hoan thanh va da verify local. Con buoc ngoai repo: commit/push va nop link LMS neu can.

---

## 1. Yeu Cau Goc Can Dat

Nguon doi chieu:
- `README.md`: huong dan start platform, setup Kaggle, deploy Prefect, ingest, smoke tests, readiness.
- `SUBMISSION.md`: source code day du, integration scripts hoat dong, Prefect flow deploy/schedule, screenshots demo, smoke test, readiness score, documentation.
- `LAB28_GUIDE.md`: hybrid local + Kaggle, 10 integration points, 5 smoke tests, production readiness, demo evidence.

---

## 2. Trang Thai Sau Khi Sua

| Hang muc | Trang thai | Bang chung |
|---|---|---|
| Local Docker Compose stack | Done | `docker compose ps`: API Gateway, Qdrant, Redis healthy; Kafka/Prefect/Grafana/Prometheus Up |
| Kaggle vLLM + embedding tunnel | Done | Smoke test full inference pass qua API Gateway |
| Kafka ingest | Done | `scripts/01_ingest_to_kafka.py` sent `doc_001`, `doc_002` |
| Prefect deployment + schedule | Done | Deployment `Kafka to Delta Pipeline/kafka-to-delta`; run `antique-corgi` Completed |
| Delta Lake output | Done | `delta-lake/raw/batch_*.parquet` duoc tao tu Prefect |
| Feast/Redis feature store | Done | `scripts/03_delta_to_feast.py`: loaded 140 records, stored features |
| Qdrant vector store | Done | Collection `documents`, `points_count=5` |
| API Gateway | Done | `/health` returns `status=ok`, circuit breaker closed |
| Prometheus + Grafana | Done | Prometheus scrapes `api-gateway` va `qdrant`; dashboard shows both UP |
| LangSmith traces | Done | `scripts/09_verify_observability.py` pass project `lab28-platform` |
| Smoke tests | Done | `8 passed` |
| Production readiness | Done | `10/10 = 100%` |
| Submission answers | Done | `SUBMISSION_ANSWERS.md` |
| Screenshots | Done | `screenshots/` va root copies theo format nop bai |

---

## 3. Nhung Loi Da Sua So Voi PLAN Cu

| Van de cu | Cach sua |
|---|---|
| PLAN ghi screenshot con thieu, trong khi file da co nhung dat sai noi dung | Chup lai `screenshots/prefect_ui.png`, `screenshots/grafana_dashboard.png`, `screenshots/api_gateway.png` dung noi dung |
| API Gateway va Qdrant bi Docker `unhealthy` do healthcheck goi `curl` khong co trong image | Doi healthcheck API sang Python `urllib`; doi Qdrant sang TCP check bang `bash` |
| Prometheus scrape truc tiep Kafka/Prefect lam dashboard hien DOWN | Chi scrape target co metrics hop le: `api-gateway`, `qdrant` |
| Grafana dashboard bi nhieu target cu | Scope Services Status vao `up{job=~"api-gateway|qdrant"}` |
| Smoke test phu thuoc interpreter local co san package | Them root `requirements.txt`, README huong dan `pip install -r requirements.txt` |
| Prefect chua co deployment/schedule thuc te | Sua `prefect/flows/kafka_to_delta.py`, deploy deployment cron 5 phut, tao flow run completed |
| Prefect worker thieu dependency | Worker install `/opt/prefect/flows/requirements.txt` khi start |
| `pandas==2.1.0` keo `numpy 2.x` gay binary incompatibility voi `pyarrow==14.0.0` | Pin `numpy<2` |
| Kafka chi advertise `localhost:9092`, worker trong Docker khong consume duoc | Them dual listener: host `localhost:9092`, internal `kafka:29092` |
| LangSmith chi kiem tra project, chua co trace tu gateway | API Gateway emit LangSmith run best-effort cho moi `/api/v1/chat`; verify script tu doc `.env` |
| 5 cau hoi nop bai moi la goi y | Them `SUBMISSION_ANSWERS.md` va link tu `SUBMISSION.md` |

---

## 4. Integration Points

| # | Integration | Trang thai |
|---|---|---|
| 1 | Data Ingestion -> Kafka | Done |
| 2 | Kafka -> Prefect Pipeline | Done |
| 3 | Prefect -> Delta Lake | Done |
| 4 | Delta Lake -> Feast/Redis | Done |
| 5 | Data -> Embeddings -> Qdrant | Done |
| 6 | MLflow experiment tracking | Done |
| 7 | Model registry/tagging metadata | Done |
| 8 | vLLM -> API Gateway | Done |
| 9 | Prometheus/Grafana metrics | Done |
| 10 | LangSmith traces | Done |

---

## 5. Verification Commands

```bash
docker compose ps
/Users/lehuyhongnhat/miniconda3/bin/python -m pytest smoke-tests/ -q
/Users/lehuyhongnhat/miniconda3/bin/python scripts/production_readiness_check.py
/Users/lehuyhongnhat/miniconda3/bin/python scripts/09_verify_observability.py
```

Ket qua hien tai:
- Smoke tests: `8 passed in 19.07s`
- Production readiness: `10/10 = 100%`
- Observability verify: Prometheus OK, LangSmith OK
- Prefect run: `antique-corgi` Completed

---

## 6. Artifacts Nop Bai

```text
Day28-Lab-Assignment/
├── docker-compose.yml
├── README.md
├── SUBMISSION.md
├── SUBMISSION_ANSWERS.md
├── requirements.txt
├── prefect/flows/kafka_to_delta.py
├── scripts/
├── api-gateway/
├── monitoring/
├── screenshots/
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   ├── grafana_dashboard.png
│   ├── smoke_tests_results.png
│   └── production_readiness.png
├── smoke_tests_results.png
└── production_readiness.png
```

---

## 7. Viec Con Lai Neu Muon Nop Chinh Thuc

| Viec | Trang thai |
|---|---|
| Review `git diff --check` | Done |
| Commit cac sua doi moi | Chua lam |
| Push GitHub | Chua lam sau dot sua nay |
| Nop link repo qua LMS | Ngoai repo |
