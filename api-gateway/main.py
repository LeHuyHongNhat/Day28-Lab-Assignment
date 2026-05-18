# api-gateway/main.py
from fastapi import FastAPI, Request, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time, logging, json

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("api-gateway")

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ.get("VLLM_URL", "http://localhost:8001")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

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

        return {
            "answer": result["choices"][0]["message"]["content"],
            "latency_ms": round(latency, 2),
            "model": result["model"]
        }

    except httpx.TimeoutException:
        record_failure()
        logger.error("LLM inference timed out")
        raise HTTPException(status_code=504, detail="LLM inference timed out")
    except Exception as e:
        record_failure()
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "circuit_breaker": circuit_breaker["state"],
        "timestamp": time.time()
    }
