import time
import math
import requests

BASE_URL = "https://cataas.com"
NB_REQUESTS = 10   # max 20 requêtes/run selon le sujet, on prend 10 pour rester raisonnable
TIMEOUT = 3


def run_qos() -> dict:
    """
    Effectue NB_REQUESTS appels sur GET /cat et calcule les métriques QoS.
    Retourne un dict avec : latency_ms_avg, latency_ms_p95, latency_ms_min,
    latency_ms_max, error_rate, availability, nb_requests.
    """
    latencies = []
    errors = 0

    for _ in range(NB_REQUESTS):
        try:
            start = time.perf_counter()
            response = requests.get(f"{BASE_URL}/cat", timeout=TIMEOUT)
            latency_ms = round((time.perf_counter() - start) * 1000)

            if response.status_code != 200:
                errors += 1
            elif not response.headers.get("Content-Type", "").startswith("image/"):
                errors += 1
            else:
                latencies.append(latency_ms)

        except requests.RequestException:
            errors += 1

    if latencies:
        latencies_sorted = sorted(latencies)
        avg = round(sum(latencies_sorted) / len(latencies_sorted), 1)
        min_lat = latencies_sorted[0]
        max_lat = latencies_sorted[-1]
        p95_index = max(0, math.ceil(0.95 * len(latencies_sorted)) - 1)
        p95 = latencies_sorted[p95_index]
    else:
        avg = min_lat = max_lat = p95 = None

    error_rate = round(errors / NB_REQUESTS, 3)
    availability = round((1 - error_rate) * 100, 1)

    return {
        "nb_requests": NB_REQUESTS,
        "latency_ms_avg": avg,
        "latency_ms_p95": p95,
        "latency_ms_min": min_lat,
        "latency_ms_max": max_lat,
        "error_rate": error_rate,
        "availability_pct": availability,
    }


if __name__ == "__main__":
    print("Mesure de la QoS en cours...\n")
    results = run_qos()
    print("===== Résultats QoS =====")
    print(f"Requêtes effectuées : {results['nb_requests']}")
    print(f"Latence moyenne     : {results['latency_ms_avg']} ms")
    print(f"Latence min         : {results['latency_ms_min']} ms")
    print(f"Latence max         : {results['latency_ms_max']} ms")
    print(f"P95                 : {results['latency_ms_p95']} ms")
    print(f"Taux d'erreur       : {round(results['error_rate'] * 100, 1)} %")
    print(f"Disponibilité       : {results['availability_pct']} %")
