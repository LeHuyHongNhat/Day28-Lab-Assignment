# scripts/09_verify_observability.py
import os
from pathlib import Path
import requests

def load_dotenv():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

def check_prometheus():
    resp = requests.get("http://localhost:9090/api/v1/query",
                        params={"query": 'up{job="api-gateway"}'})
    resp.raise_for_status()
    data = resp.json()
    assert data["status"] == "success"
    result = data["data"]["result"]
    assert result and result[0]["value"][1] == "1"
    print("Integration 9 OK: Prometheus is scraping API Gateway")

def check_langsmith():
    from langsmith import Client

    api_key = os.environ.get("LANGCHAIN_API_KEY")
    project = os.environ.get("LANGCHAIN_PROJECT", "lab28-platform")
    assert api_key, "LANGCHAIN_API_KEY is required to verify LangSmith traces"

    client = Client(api_key=api_key)
    runs = list(client.list_runs(project_name=project, limit=10))
    assert runs, f"No LangSmith runs found in project {project}"
    print(f"Integration 10 OK: LangSmith traces visible in project {project}")

load_dotenv()
check_prometheus()
check_langsmith()
