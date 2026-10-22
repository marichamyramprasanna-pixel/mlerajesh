"""Quick test for the supplied Industrial IoT dataset integration."""
import requests

BASE = "http://127.0.0.1:8520"

print(requests.get(f"{BASE}/health", timeout=5).json())
print(requests.get(f"{BASE}/dataset/info", timeout=5).json())

start = requests.post(f"{BASE}/start/P-02", timeout=5).json()
print("START:", start)

reading = requests.post(f"{BASE}/read/P-02", timeout=5).json()
print("READ:", reading)

diagnosis = requests.post(
    f"{BASE}/diagnose",
    json={"machine": "P-02", "values": reading["values"]},
    timeout=5,
).json()
print("DIAGNOSIS:", diagnosis)
