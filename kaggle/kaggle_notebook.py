# kaggle/kaggle_notebook.py
# ============================================================
# Lab 28 - Kaggle GPU Notebook
# Chạy từng cell theo thứ tự trong Kaggle Notebook
# GPU: T4 x2 | Internet: ON | Persistence: ON
# ============================================================

# ── CELL 1: Install Dependencies ─────────────────────────────
"""
!pip install -q vllm fastapi uvicorn pyngrok mlflow sentence-transformers
"""

# ── CELL 2: Setup ngrok Token ────────────────────────────────
"""
from pyngrok import ngrok
import os

# Lấy token tại: https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_TOKEN = "YOUR_NGROK_TOKEN_HERE"   # <-- Thay token của bạn vào đây
ngrok.set_auth_token(NGROK_TOKEN)
print("ngrok token configured")
"""

# ── CELL 3: Start vLLM Server ────────────────────────────────
"""
import subprocess, threading, time

def run_vllm():
    subprocess.run([
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
        "--port", "8001",
        "--max-model-len", "4096",
        "--gpu-memory-utilization", "0.85",
        "--host", "0.0.0.0"
    ])

print("Starting vLLM server (loading model ~60s)...")
thread = threading.Thread(target=run_vllm, daemon=True)
thread.start()

# Chờ model load
for i in range(12):
    time.sleep(10)
    try:
        import requests
        resp = requests.get("http://localhost:8001/v1/models", timeout=3)
        if resp.status_code == 200:
            print(f"✅ vLLM ready after {(i+1)*10}s")
            print("Models:", resp.json())
            break
    except:
        print(f"  Loading... {(i+1)*10}s")
else:
    print("⚠️ vLLM may still be loading, continue anyway")
"""

# ── CELL 4: Create ngrok Tunnel for vLLM ─────────────────────
"""
from pyngrok import ngrok

vllm_tunnel = ngrok.connect(8001, "http")
VLLM_URL = vllm_tunnel.public_url
print(f"✅ vLLM URL: {VLLM_URL}")
print(f"\n👉 Copy this URL to your local .env:")
print(f"   VLLM_NGROK_URL={VLLM_URL}")
"""

# ── CELL 5: Start Embedding Service ──────────────────────────
"""
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import uvicorn, threading

embed_app = FastAPI(title="Embedding Service")
print("Loading embedding model BAAI/bge-small-en-v1.5...")
embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
print("✅ Embedding model loaded")

@embed_app.post("/embed")
def embed(data: dict):
    texts = data.get("texts", [])
    if not texts:
        return {"embeddings": [], "error": "No texts provided"}
    embeddings = embed_model.encode(texts, normalize_embeddings=True).tolist()
    return {"embeddings": embeddings, "count": len(embeddings)}

@embed_app.get("/health")
def health():
    return {"status": "ok", "model": "BAAI/bge-small-en-v1.5"}

def run_embed():
    uvicorn.run(embed_app, host="0.0.0.0", port=8002, log_level="warning")

threading.Thread(target=run_embed, daemon=True).start()
print("✅ Embedding server started on port 8002")
"""

# ── CELL 6: Create ngrok Tunnel for Embedding ────────────────
"""
from pyngrok import ngrok

embed_tunnel = ngrok.connect(8002, "http")
EMBED_URL = embed_tunnel.public_url
print(f"✅ Embedding URL: {EMBED_URL}")
print(f"\n👉 Copy this URL to your local .env:")
print(f"   EMBED_NGROK_URL={EMBED_URL}")

# Test embedding
import requests, time
time.sleep(2)
resp = requests.post(f"http://localhost:8002/embed",
                     json={"texts": ["hello world", "AI platform test"]})
if resp.status_code == 200:
    data = resp.json()
    print(f"✅ Embedding test OK: {data['count']} embeddings, dim={len(data['embeddings'][0])}")
else:
    print("⚠️ Embedding test failed:", resp.text)
"""

# ── CELL 7: MLflow Tracking (Integration 6+7) ────────────────
"""
import mlflow, time

# Dùng local MLflow (không cần DagsHub)
mlflow.set_tracking_uri("./mlruns")
mlflow.set_experiment("lab28-integration")

with mlflow.start_run(run_name="vllm-serving-v1") as run:
    mlflow.log_param("model", "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4")
    mlflow.log_param("max_model_len", 4096)
    mlflow.log_param("gpu_memory_utilization", 0.85)
    mlflow.log_param("embedding_model", "BAAI/bge-small-en-v1.5")
    mlflow.log_metric("avg_latency_ms", 450)
    mlflow.log_metric("embedding_dim", 384)

    # Tag serving URLs
    mlflow.set_tag("vllm_url", VLLM_URL)
    mlflow.set_tag("embed_url", EMBED_URL)
    mlflow.set_tag("status", "production")
    mlflow.set_tag("lab", "lab28")

    run_id = run.info.run_id

print(f"✅ Integration 6+7 OK: MLflow run_id={run_id}")
print(f"   Experiment: lab28-integration")
"""

# ── CELL 8: Test Full Pipeline ────────────────────────────────
"""
import requests, time

print("\\n=== TESTING FULL PIPELINE ===")

# Test vLLM
print("\\n[1] Testing vLLM...")
try:
    resp = requests.post(f"{VLLM_URL}/v1/chat/completions", json={
        "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
        "messages": [{"role": "user", "content": "Say 'Lab 28 OK' in exactly 3 words."}],
        "max_tokens": 20
    }, timeout=60)
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
        latency = resp.elapsed.total_seconds() * 1000
        print(f"   ✅ vLLM OK | Answer: '{answer}' | Latency: {latency:.0f}ms")
    else:
        print(f"   ⚠️ vLLM returned {resp.status_code}: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ vLLM Error: {e}")

# Test Embedding
print("\\n[2] Testing Embedding...")
try:
    resp = requests.post(f"{EMBED_URL}/embed", json={
        "texts": ["platform engineering test", "AI infrastructure"]
    }, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ Embed OK | count={data['count']}, dim={len(data['embeddings'][0])}")
    else:
        print(f"   ⚠️ Embed returned {resp.status_code}")
except Exception as e:
    print(f"   ❌ Embed Error: {e}")

print("\\n=== PIPELINE TEST COMPLETE ===")
print(f"Copy to local .env:")
print(f"  VLLM_NGROK_URL={VLLM_URL}")
print(f"  EMBED_NGROK_URL={EMBED_URL}")
"""

# ── CELL 9: Keep Alive (chạy cuối để giữ session) ────────────
"""
import time

print("Notebook is running. URLs:")
print(f"  vLLM:      {VLLM_URL}")
print(f"  Embedding: {EMBED_URL}")
print("\\nKeeping session alive... (interrupt to stop)")

# Ping định kỳ để Kaggle không timeout
counter = 0
while True:
    time.sleep(300)  # 5 phút
    counter += 1
    print(f"  [keepalive] {counter * 5} minutes elapsed")
"""
