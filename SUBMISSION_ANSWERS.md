# Câu Trả Lời Nộp Bài - Lab #28

## 1. Trade-offs trong thiết kế kiến trúc AI platform

Kiến trúc dùng mô hình hybrid: local Docker Compose chạy các service điều phối,
lưu trữ, API gateway và observability; Kaggle GPU chạy vLLM và embedding model.
Cách này cân bằng chi phí và hiệu năng: phần cần GPU được đưa lên Kaggle T4,
còn các thành phần cần kiểm soát cấu hình và demo nhanh vẫn chạy local.

Trade-off chính là độ tin cậy của đường mạng local -> Kaggle phụ thuộc tunnel
ngrok. Để giảm rủi ro, API Gateway đặt timeout, circuit breaker và fallback
response. Maintainability được giữ bằng cách tách từng service trong
`docker-compose.yml`, tách script theo integration point, và dùng Prometheus /
Grafana / LangSmith để quan sát lỗi thay vì debug thủ công.

## 2. Xử lý ngắt kết nối giữa local và Kaggle

API Gateway gọi vLLM qua URL tunnel và đặt timeout 30 giây cho request LLM.
Nếu Kaggle hoặc tunnel lỗi liên tiếp, circuit breaker trong `api-gateway/main.py`
đếm failure; sau 3 lỗi circuit chuyển sang `open` và trả fallback response thay
vì tiếp tục gọi service bên ngoài. Sau thời gian reset, circuit chuyển sang
`half-open` để thử phục hồi.

Qdrant search cũng được xử lý theo hướng graceful degradation: nếu vector store
lỗi, gateway vẫn gọi LLM với context rỗng thay vì làm hỏng toàn bộ request.
Như vậy happy path vẫn tận dụng đầy đủ RAG context, còn failure path vẫn có phản
hồi có kiểm soát.

## 3. Kafka giúp decouple các component như thế nào

Kafka đóng vai trò message bus giữa bước ingest và bước xử lý downstream. Producer
chỉ cần publish record vào topic `data.raw`, không cần biết Prefect flow hoặc
feature/vector store đang chạy lúc nào. Prefect consumer có thể đọc lại dữ liệu,
xử lý theo batch và ghi ra Delta Lake.

Mô hình event-driven này giúp giảm coupling trực tiếp giữa ingestion, pipeline,
feature store và vector store. Khi cần scale hoặc thay đổi consumer, producer
không phải thay đổi. Kafka cũng giúp demo replay/debug tốt hơn vì dữ liệu đã
được ghi vào topic trước khi các bước downstream chạy.

## 4. Observability được implement như thế nào

Logs được ghi từ Docker service logs và structured logging trong API Gateway.
Metrics được expose qua `/metrics` của API Gateway bằng
`prometheus-fastapi-instrumentator`; Prometheus scrape API Gateway và Qdrant, sau
đó Grafana dashboard hiển thị request rate, P95 latency, error rate, service
status và tổng số HTTP requests.

Tracing được gửi sang LangSmith theo project `lab28-platform`. API Gateway emit
trace dạng best-effort cho mỗi request `/api/v1/chat`; nếu LangSmith lỗi hoặc
thiếu key, inference không bị fail. Alert rules nằm trong
`monitoring/alert_rules.yml` để cảnh báo API Gateway down, latency cao và error
rate cao.

## 5. Khi Qdrant hoặc Kafka crash thì hệ thống xử lý thế nào

Docker Compose cấu hình `restart: unless-stopped` cho các service chính, nên
container có thể tự khởi động lại sau crash thông thường. Với Qdrant, API Gateway
có graceful degradation: nếu vector search lỗi, gateway log warning và tiếp tục
gọi LLM với context rỗng.

Với Kafka, producer/consumer sẽ fail nếu broker không sẵn sàng, nhưng dữ liệu đã
publish vào topic có thể được consumer đọc lại sau khi Kafka phục hồi. Trong bản
lab local một broker, chưa có high availability hoặc replication thực sự; chiến
lược hiện tại là restart policy, kiểm tra readiness, và replay lại script ingest
khi cần.
