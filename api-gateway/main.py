# api-gateway/main.py
from fastapi import FastAPI, Request, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time, logging, json
from datetime import datetime, timezone
from uuid import uuid4

try:
    from langsmith import Client as LangSmithClient
except Exception:  # pragma: no cover - tracing is optional at runtime
    LangSmithClient = None

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("api-gateway")

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ.get("VLLM_URL", "http://localhost:8001")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.environ.get("LANGCHAIN_PROJECT", "lab28-platform")
langsmith_client = (
    LangSmithClient(api_key=LANGCHAIN_API_KEY)
    if LangSmithClient and LANGCHAIN_API_KEY
    else None
)

# ── Circuit Breaker State ────────────────────────────────────
circuit_breaker = {
    "failures": 0,
    "threshold": 3,
    "reset_time": 60,
    "last_failure": 0,
    "state": "closed"  # closed = normal, open = blocking
}

def check_circuit():
    """Check if circuit breaker allows request"""
    cb = circuit_breaker
    if cb["state"] == "open":
        if time.time() - cb["last_failure"] > cb["reset_time"]:
            cb["state"] = "half-open"
            cb["failures"] = 0
            logger.info("Circuit breaker: half-open (attempting recovery)")
            return True
        return False
    return True

def record_failure():
    cb = circuit_breaker
    cb["failures"] += 1
    cb["last_failure"] = time.time()
    if cb["failures"] >= cb["threshold"]:
        cb["state"] = "open"
        logger.warning(f"Circuit breaker: OPEN after {cb['failures']} failures")

def record_success():
    cb = circuit_breaker
    cb["failures"] = 0
    cb["state"] = "closed"

def emit_langsmith_trace(query, answer, model, latency_ms, context_count, error=None):
    """Best-effort trace emission; observability must not break inference."""
    if not langsmith_client:
        return

    now = datetime.now(timezone.utc)
    try:
        langsmith_client.create_run(
            id=uuid4(),
            name="api-gateway-chat",
            run_type="chain",
            project_name=LANGCHAIN_PROJECT,
            inputs={"query": query, "context_count": context_count},
            outputs={"answer": answer, "model": model, "latency_ms": latency_ms},
            error=error,
            start_time=now,
            end_time=now,
            tags=["lab28", "api-gateway"],
        )
    except Exception as e:
        logger.warning(f"LangSmith trace emission failed: {e}")


@app.post("/api/v1/chat")
async def chat(request: Request):
    body = await request.json()

    # Validation
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=422, detail="Missing required field: 'query'")

    start = time.time()

    # Circuit breaker check
    if not check_circuit():
        logger.warning("Circuit breaker OPEN — returning fallback response")
        return {
            "answer": "Service temporarily unavailable. Please try again later.",
            "latency_ms": 0,
            "model": "fallback",
            "circuit_breaker": "open"
        }

    try:
        # 1. Vector search (with graceful degradation)
        context = []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                search_resp = await client.post(
                    f"{QDRANT_URL}/collections/documents/points/search",
                    json={
                        "vector": body.get("embedding", [0.0] * 384),
                        "limit": 3
                    }
                )
                context = search_resp.json().get("result", [])
                logger.info(f"Vector search returned {len(context)} results")
        except Exception as e:
            logger.warning(f"Qdrant search failed (graceful degradation): {e}")
            context = []

        # 2. LLM inference
        prompt = f"Context: {context}\n\nQuery: {query}"
        async with httpx.AsyncClient(timeout=30) as client:
            llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
                "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                "messages": [{"role": "user", "content": prompt}]
            })

        latency = (time.time() - start) * 1000
        result = llm_resp.json()
        record_success()

        logger.info(f"Chat completed in {latency:.2f}ms")

        answer = result["choices"][0]["message"]["content"]
        model = result["model"]
        emit_langsmith_trace(query, answer, model, round(latency, 2), len(context))

        return {
            "answer": answer,
            "latency_ms": round(latency, 2),
            "model": model
        }

    except httpx.TimeoutException:
        record_failure()
        logger.error("LLM inference timed out")
        emit_langsmith_trace(query, "", "error", 0, 0, error="LLM inference timed out")
        raise HTTPException(status_code=504, detail="LLM inference timed out")
    except Exception as e:
        record_failure()
        logger.error(f"Chat endpoint error: {e}")
        emit_langsmith_trace(query, "", "error", 0, 0, error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "circuit_breaker": circuit_breaker["state"],
        "timestamp": time.time()
    }
