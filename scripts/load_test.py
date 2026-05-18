# scripts/load_test.py
"""
Load test script for API Gateway
Sends concurrent requests and measures latency percentiles + throughput
"""
import asyncio
import httpx
import time
import statistics

BASE_URL = "http://localhost:8000"
TOTAL_REQUESTS = 50
CONCURRENT = 10

results = []
errors = 0


async def send_request(client: httpx.AsyncClient, i: int):
    global errors
    start = time.time()
    try:
        resp = await client.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "query": f"Load test request {i}",
                "embedding": [0.1] * 384
            },
            timeout=30
        )
        latency = (time.time() - start) * 1000
        if resp.status_code == 200:
            results.append(latency)
        else:
            errors += 1
            print(f"  Request {i}: HTTP {resp.status_code}")
    except Exception as e:
        errors += 1
        print(f"  Request {i}: Error - {e}")


async def run_load_test():
    global errors
    print(f"\n{'='*50}")
    print(f"  LOAD TEST — {TOTAL_REQUESTS} requests, {CONCURRENT} concurrent")
    print(f"{'='*50}\n")

    async with httpx.AsyncClient() as client:
        start_time = time.time()

        # Send requests in batches
        for batch_start in range(0, TOTAL_REQUESTS, CONCURRENT):
            batch_end = min(batch_start + CONCURRENT, TOTAL_REQUESTS)
            tasks = [
                send_request(client, i)
                for i in range(batch_start, batch_end)
            ]
            await asyncio.gather(*tasks)
            print(f"  Batch {batch_start}-{batch_end} completed")

        total_time = time.time() - start_time

    # Report
    print(f"\n{'='*50}")
    print(f"  RESULTS")
    print(f"{'='*50}")

    if results:
        results.sort()
        p50 = statistics.median(results)
        p95 = results[int(len(results) * 0.95)] if len(results) > 1 else results[0]
        p99 = results[int(len(results) * 0.99)] if len(results) > 1 else results[0]

        print(f"  Total Requests:  {TOTAL_REQUESTS}")
        print(f"  Successful:      {len(results)}")
        print(f"  Errors:          {errors}")
        print(f"  Total Time:      {total_time:.2f}s")
        print(f"  Throughput:      {len(results)/total_time:.2f} req/s")
        print(f"  Latency P50:     {p50:.2f}ms")
        print(f"  Latency P95:     {p95:.2f}ms")
        print(f"  Latency P99:     {p99:.2f}ms")
        print(f"  Latency Min:     {min(results):.2f}ms")
        print(f"  Latency Max:     {max(results):.2f}ms")
    else:
        print(f"  All {errors} requests failed!")

    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(run_load_test())
